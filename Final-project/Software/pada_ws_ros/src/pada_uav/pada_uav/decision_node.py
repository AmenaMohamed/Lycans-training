

import rclpy
from rclpy.node import Node

from pada_interfaces.msg import Detection

from .constants import (
    AVOID_LEFT,
    AVOID_RIGHT,
    DETECTION_TOPIC,
    EXECUTION_RETRY_PERIOD_SEC,
    MODE_AUTO,
    MODE_GUIDED,
    MODE_LAND,
    MODE_RTL,
)
from .control.decision_manager import Decision, DecisionManager, DetectionInput
from .control.mavros_interface import (
    SEND_ALREADY,
    SEND_DISPATCHED,
    SEND_NOT_READY,
    MavrosInterface,
)


class DecisionNode(Node):
    """Receives perception, decides, and commands MAVROS."""

    def __init__(self) -> None:
        super().__init__("decision_node")
        self._log = self.get_logger()

        self._manager = DecisionManager()

        # MavrosInterface reuses THIS node's ROS handle; confirmed modes are
        # pushed back into the manager through the callback.
        self._mavros = MavrosInterface(
            self, self._manager.update_confirmed_mode
        )

        # Pending (direction, offset) avoidance execution waiting for a
        # confirmed GUIDED mode and/or valid navigation data.
        self._pending_avoidance = None
        self._nav_warn_shown = False

        self.create_subscription(
            Detection, DETECTION_TOPIC, self._detection_cb, 10
        )

        # Execution-retry timer only. It retries an APPROVED action
        # (waiting for GUIDED confirmation / navigation data) and must
        # NEVER call DecisionManager.decide().
        self.create_timer(
            EXECUTION_RETRY_PERIOD_SEC, self._execution_retry_cb
        )

        self._log.info("Decision Node started.")

    # ------------------------------------------------------------------
    # Perception event (the only source of mission decisions)
    # ------------------------------------------------------------------
    def _detection_cb(self, msg: Detection) -> None:
        data = DetectionInput(
            command=int(msg.command),
            command_confidence=float(msg.command_confidence),
            obstacle_detected=bool(msg.obstacle_detected),
            obstacle_confidence=float(msg.obstacle_confidence),
            obstacle_direction=int(msg.obstacle_direction),
            obstacle_distance_level=int(msg.obstacle_distance_level),
        )
        decision = self._manager.decide(data)
        self._execute(decision)

    # ------------------------------------------------------------------
    # Decision execution
    # ------------------------------------------------------------------
    def _execute(self, decision: Decision) -> None:
        if decision.start_avoidance:
            direction = decision.avoidance_direction
            self._log.info(
                f"Avoidance selected: direction={self._direction_label(direction)}, "
                f"offset={decision.avoidance_offset:.1f} m"
            )
            self._pending_avoidance = (
                decision.avoidance_direction,
                decision.avoidance_offset,
            )
            self._mavros.reset_avoidance_execution()
            self._nav_warn_shown = False
        elif decision.obstacle_cleared:
            # Obstacle gone: no further avoidance execution is required, and
            # previously pending intent (LAND/RTL) or AUTO is requested below.
            self._pending_avoidance = None
            self._nav_warn_shown = False

        if decision.mode_requested is not None:
            if decision.obstacle_cleared:
                self._log.info("Obstacle cleared.")
                if decision.resumed_mode == MODE_AUTO:
                    self._log.info("Resuming AUTO.")
                elif decision.resumed_mode:
                    self._log.info(f"Resuming pending {decision.resumed_mode}.")
            self._mavros.request_mode(decision.mode_requested)

    # ------------------------------------------------------------------
    # Execution-retry timer (never a decision loop)
    # ------------------------------------------------------------------
    def _execution_retry_cb(self) -> None:
        if self._pending_avoidance is None:
            return

        direction, offset = self._pending_avoidance

        # Do NOT send DO_REPOSITION until GUIDED is CONFIRMED by /mavros/state.
        if not self._mavros.is_mode(MODE_GUIDED):
            return

        status = self._mavros.send_avoidance(direction, offset)
        if status == SEND_NOT_READY:
            # Retry later, but log only ONCE per unavailability period
            # so we never spam "Waiting for valid GPS..." at 10 Hz.
            if not self._nav_warn_shown:
                self._log.warn("Waiting for valid GPS, altitude and heading.")
                self._nav_warn_shown = True
            return

        self._nav_warn_shown = False

        if status == SEND_DISPATCHED:
            self._log.info("Navigation data ready.")
            self._log.info("Avoidance target sent.")
            self._pending_avoidance = None
        elif status == SEND_ALREADY:
            self._pending_avoidance = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _direction_label(direction: int) -> str:
        return "LEFT" if direction == AVOID_LEFT else "RIGHT"


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DecisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
