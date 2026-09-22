
import math
from typing import Callable, Optional, Tuple

from rclpy.node import Node  # type-hint only; this class is NOT a Node

from mavros_msgs.msg import State
from mavros_msgs.srv import SetMode, CommandInt
from sensor_msgs.msg import NavSatFix
from sensor_msgs.msg import NavSatStatus
from std_msgs.msg import Float64

from .constants import (
    COMMAND_INT_SERVICE,
    GPS_METERS_PER_DEG_LAT,
    MAVROS_COMPASS_HDG_TOPIC,
    MAVROS_GLOBAL_TOPIC,
    MAVROS_REL_ALT_TOPIC,
    MAVROS_STATE_TOPIC,
    MAV_CMD_DO_REPOSITION,
    MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
    MODE_GUIDED,
    SET_MODE_SERVICE,
)

# send_avoidance() status values (plain strings, no extra classes).
SEND_NOT_GUIDED = "not_guided"        # /mavros/state does not report GUIDED
SEND_NOT_READY = "not_ready"          # navigation data or service not ready
SEND_DISPATCHED = "dispatched"        # reposition request sent (ack pending)
SEND_ALREADY = "already"              # already dispatched, not repeated


class MavrosInterface:
    """Asynchronous MAVROS communication + navigation data gateway."""

    def __init__(self, node: Node, mode_callback: Callable[[str], None]) -> None:
        # NOTE: dependency injection - we reuse DecisionNode's ROS handle.
        # We never call super().__init__() and never create another Node.
        self._node = node
        self._log = node.get_logger()

        # Confirmed mode (authoritative source: /mavros/state).
        self._mode_callback = mode_callback
        self._confirmed_mode: str = ""
        self._connected: bool = False
        self._state_received: bool = False
        self._disconnect_warned: bool = False

        # Requested-but-unconfirmed mode: used ONLY to prevent request spam.
        self._requested_mode: Optional[str] = None

        # Navigation data (each tracked explicitly - a live topic is not
        # sufficient proof that the data is usable).
        self._latitude: float = 0.0
        self._longitude: float = 0.0
        self._rel_alt: float = 0.0
        self._heading_deg: float = 0.0
        self._has_global: bool = False
        self._has_alt: bool = False
        self._has_heading: bool = False

        # Avoidance (DO_REPOSITION) anti-spam.
        self._reposition_dispatched: bool = False

        # --- Subscriptions (created through DecisionNode's node handle) ---
        node.create_subscription(
            State, MAVROS_STATE_TOPIC, self._state_cb, 10
        )
        node.create_subscription(
            NavSatFix, MAVROS_GLOBAL_TOPIC, self._global_cb, 10
        )
        node.create_subscription(
            Float64, MAVROS_REL_ALT_TOPIC, self._rel_alt_cb, 10
        )
        node.create_subscription(
            Float64, MAVROS_COMPASS_HDG_TOPIC, self._heading_cb, 10
        )

        # --- Service clients (async only) ---
        self._set_mode_client = node.create_client(SetMode, SET_MODE_SERVICE)
        self._command_int_client = node.create_client(
            CommandInt, COMMAND_INT_SERVICE
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def confirmed_mode(self) -> str:
        return self._confirmed_mode

    def is_connected(self) -> bool:
        return self._connected

    def is_mode(self, mode: str) -> bool:
        return (mode or "").upper() == self._confirmed_mode

    def is_navigation_ready(self) -> bool:
        return self._has_global and self._has_alt and self._has_heading

    def reset_avoidance_execution(self) -> None:
        """Reset the reposition guard for a NEW avoidance decision."""
        self._reposition_dispatched = False

    # ------------------------------------------------------------------
    # Mode requests
    # ------------------------------------------------------------------
    def request_mode(self, mode: str) -> bool:
        """Return True iff a new async set_mode request was actually sent.

        Anti-spam rules:
          * never request a mode that is already confirmed;
          * never repeat a request that is still pending confirmation.
        """
        mode = (mode or "").upper()

        if not self._connected:
            if not self._disconnect_warned:
                self._log.warn(
                    "MAVROS is disconnected: flight commands will not be sent."
                )
                self._disconnect_warned = True
            return False

        if self._confirmed_mode == mode:
            return False  # already confirmed - LAND->LAND, RTL->RTL, ...

        if self._requested_mode == mode:
            return False  # same request still pending - no spam

        if not self._set_mode_client.service_is_ready():
            self._log.warn(
                "SetMode service not ready; mode request deferred: "
                f"{self._confirmed_mode or 'UNKNOWN'} -> {mode}"
            )
            return False

        request = SetMode.Request()
        request.custom_mode = mode

        # Asynchronous call: the Future resolves with the service response.
        # response.mode_sent merely means the *request* was accepted by
        # MAVROS. Actual flight-mode confirmation can ONLY come from
        # /mavros/state.
        future = self._set_mode_client.call_async(request)
        self._requested_mode = mode
        self._log.info(f"Mode request: {self._confirmed_mode or 'UNKNOWN'} -> {mode}")
        future.add_done_callback(
            lambda fut, m=mode: self._on_set_mode_response(fut, m)
        )
        return True

    def _on_set_mode_response(self, future, mode: str) -> None:
        try:
            response = future.result()
        except Exception as exc:  # noqa: BLE001 - report any service failure
            self._log.warn(f"SetMode service call failed ({mode}): {exc}")
            if self._requested_mode == mode:
                self._requested_mode = None
            return

        if not response.mode_sent:
            # Rejected by MAVROS. Report it clearly; do NOT pretend success.
            self._log.warn(
                f"Mode request REJECTED by MAVROS ({mode}, mode_sent=False). "
                "Still waiting for the real mode from /mavros/state."
            )
            if self._requested_mode == mode:
                self._requested_mode = None

    # ------------------------------------------------------------------
    # Avoidance (DO_REPOSITION)
    # ------------------------------------------------------------------
    def send_avoidance(self, direction: int, offset: float) -> str:
        """Send ONE DO_REPOSITION guided target. See send status constants.

        Safety conditions before sending:
          * GUIDED must be CONFIRMED by /mavros/state (the caller gates this,
            we double-check anyway);
          * navigation data must be valid (lat, lon, rel_alt, heading);
          * the reposition must not already have been dispatched.
        """
        if not self.is_mode(MODE_GUIDED):
            return SEND_NOT_GUIDED

        if self._reposition_dispatched:
            return SEND_ALREADY

        if not self.is_navigation_ready():
            return SEND_NOT_READY

        if not self._command_int_client.service_is_ready():
            return SEND_NOT_READY

        target = self._compute_avoidance_target(direction, offset)
        if target is None:
            return SEND_NOT_READY

        request = self._build_reposition_request(target)

        future = self._command_int_client.call_async(request)
        self._reposition_dispatched = True
        future.add_done_callback(self._on_command_int_response)
        return SEND_DISPATCHED

    def _on_command_int_response(self, future) -> None:
        try:
            response = future.result()
        except Exception as exc:  # noqa: BLE001
            self._log.warn(f"Reposition service call failed: {exc}")
            return

        # CommandInt response has a `success` flag; there is NO `result`
        # field on this service in this setup - do not use response.result.
        if response.success:
            self._log.info("Avoidance command accepted.")
        else:
            self._log.warn(
                "Avoidance command REJECTED by MAVROS (success=False)."
            )

    # ------------------------------------------------------------------
    # Avoidance target geometry
    # ------------------------------------------------------------------
    def _compute_avoidance_target(
        self, direction: int, offset: float
    ) -> Optional[Tuple[float, float, float]]:
        """Return (target_lat, target_lon, target_rel_alt) or None.

        APPROVED GEOMETRY (no path/trajectory planner, ONE point):
            forward = offset
            lateral = offset for AVOID_RIGHT, -offset for AVOID_LEFT

            north = forward*cos(h) - lateral*sin(h)
            east  = forward*sin(h) + lateral*cos(h)

        Offsets are in meters; heading comes from compass_hdg (degrees) and
        is converted to radians here. Altitude is NOT changed: we reuse the
        current relative altitude.
        """
        if not self.is_navigation_ready():
            return None

        heading_rad = math.radians(self._heading_deg)
        lat_rad = math.radians(self._latitude)

        forward = float(offset)
        # Correction 4: `offset` is the *magnitude* for the forward and
        # lateral components. The resulting horizontal displacement to the
        # target is sqrt(forward^2 + lateral^2) = offset*sqrt(2), which is
        # LARGER than the offset value. The offset is the selected avoidance
        # offset magnitude, NOT the true distance to the target point.
        lateral = float(offset) if direction >= 0 else -float(offset)

        north = forward * math.cos(heading_rad) - lateral * math.sin(heading_rad)
        east = forward * math.sin(heading_rad) + lateral * math.cos(heading_rad)

        target_lat = self._latitude + north / GPS_METERS_PER_DEG_LAT
        target_lon = self._longitude + east / (
            GPS_METERS_PER_DEG_LAT * math.cos(lat_rad)
        )
        return target_lat, target_lon, self._rel_alt

    def _build_reposition_request(
        self, target: Tuple[float, float, float]
    ) -> CommandInt.Request:
        lat, lon, alt = target
        request = CommandInt.Request()
        request.command = MAV_CMD_DO_REPOSITION
        request.frame = MAV_FRAME_GLOBAL_RELATIVE_ALT_INT  # global + rel alt
        request.current = 0
        request.autocontinue = 0
        # param1: ground speed < 0 -> use the default speed.
        request.param1 = -1.0
        # param2: not used to change the mode (GUIDED must already be set).
        request.param2 = 0.0
        # param3: loiter radius / default.
        request.param3 = 0.0
        # param4: default yaw / loiter direction.
        request.param4 = 0.0
        request.param5 = 0.0
        request.param6 = 0.0
        request.param7 = 0.0
        # Integer-scaled latitude/longitude for COMMAND_INT.
        request.x = int(lat * 1e7)
        request.y = int(lon * 1e7)
        request.z = float(alt)
        return request

    # ------------------------------------------------------------------
    # Subscriptions (callbacks must not block)
    # ------------------------------------------------------------------
    def _state_cb(self, msg: State) -> None:
        self._connected = bool(msg.connected)
        self._state_received = True

        if self._connected and self._disconnect_warned:
            self._log.info("MAVROS connection established.")
            self._disconnect_warned = False

        mode = (msg.mode or "").upper()
        if mode != self._confirmed_mode:
            old = self._confirmed_mode or "UNKNOWN"
            self._confirmed_mode = mode
            if self._requested_mode == mode:
                # The pending request has now been confirmed: clear it.
                self._requested_mode = None
            # Confirmation ONLY comes from /mavros/state.
            self._log.info(f"Mode changed: {old} -> {mode}")
            self._mode_callback(mode)

    def _global_cb(self, msg: NavSatFix) -> None:
        if msg.status.status >= NavSatStatus.STATUS_FIX:
            self._latitude = msg.latitude
            self._longitude = msg.longitude
            self._has_global = True

    def _rel_alt_cb(self, msg: Float64) -> None:
        self._rel_alt = float(msg.data)
        self._has_alt = True

    def _heading_cb(self, msg: Float64) -> None:
        # compass_hdg provides heading directly in DEGREES. Stored as degrees,
        # converted to radians only inside the GPS target math above.
        self._heading_deg = float(msg.data)
        self._has_heading = True
