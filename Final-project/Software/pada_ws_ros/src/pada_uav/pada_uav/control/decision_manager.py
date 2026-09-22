
from dataclasses import dataclass, field
from typing import Optional, Tuple

from .constants import (
    AVOID_LEFT,
    AVOID_RIGHT,
    COMMAND_LAND,
    COMMAND_NONE,
    COMMAND_RTL,
    DISTANCE_FAR,
    DISTANCE_MEDIUM,
    DISTANCE_NEAR,
    FAR_OFFSET,
    INTENT_LAND,
    INTENT_NONE,
    INTENT_RTL,
    LAND_CONFIDENCE_THRESHOLD,
    MEDIUM_OFFSET,
    MODE_AUTO,
    MODE_GUIDED,
    MODE_LAND,
    MODE_RTL,
    NEAR_OFFSET,
    OBSTACLE_CENTER,
    OBSTACLE_CONFIDENCE_THRESHOLD,
    OBSTACLE_LEFT,
    OBSTACLE_RIGHT,
    RTL_CONFIDENCE_THRESHOLD,
    STATE_AUTO,
    STATE_AVOIDING,
    STATE_LANDING,
    STATE_RTL,
)


@dataclass
class DetectionInput:
    """Already-interpreted perception output (no pixel/image logic)."""

    command: int = COMMAND_NONE
    command_confidence: float = 0.0
    obstacle_detected: bool = False
    obstacle_confidence: float = 0.0
    obstacle_direction: int = OBSTACLE_CENTER
    obstacle_distance_level: int = DISTANCE_NEAR


@dataclass
class Decision:
    """Instruction produced by DecisionManager and executed by DecisionNode.

    ``mode_requested`` is only ever a *request*; the resulting state is
    confirmed later by /mavros/state.
    """

    mode_requested: Optional[str] = None
    start_avoidance: bool = False
    avoidance_direction: int = AVOID_RIGHT
    avoidance_offset: float = NEAR_OFFSET
    obstacle_cleared: bool = False
    resumed_mode: Optional[str] = None


class DecisionManager:
    """Pure state machine. Confirmed-state authority + mission priority."""

    def __init__(self) -> None:
        self._state: int = STATE_AUTO
        self._pending_intent: int = INTENT_NONE
        # True while an avoidance interruption has been *requested* (GUIDED)
        # but not yet confirmed by /mavros/state. Prevents re-request spam and
        # allows the interruption to be cleanly abandoned if the obstacle
        # clears before GUIDED is confirmed.
        self._interrupt_pending: bool = False

    # ------------------------------------------------------------------
    # State (CONFIRMED only)
    # ------------------------------------------------------------------
    @property
    def state(self) -> int:
        return self._state

    @property
    def pending_intent(self) -> int:
        return self._pending_intent

    def update_confirmed_mode(self, mode: str) -> None:
        """Call ONLY with a mode echoed by /mavros/state (authoritative)."""
        new_state = self._mode_to_state(mode)
        if new_state == STATE_AVOIDING:
            # GUIDED has been confirmed: the requested interruption became
            # reality, so it is no longer "pending".
            self._interrupt_pending = False
        self._state = new_state

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------
    def decide(self, data: DetectionInput) -> Decision:
        """Evaluate one detection event. Never called from any timer loop."""
        if self._obstacle_active(data):
            return self._on_obstacle(data)
        if self._state == STATE_AVOIDING or self._interrupt_pending:
            return self._resume(data)
        return self._mission_command(data)

    # ------------------------------------------------------------------
    # Obstacle interruption
    # ------------------------------------------------------------------
    def _on_obstacle(self, data: DetectionInput) -> Decision:
        """Safety interruption. LAND > RTL intent priority is applied here."""
        new_intent = self._detected_intent(data)
        if new_intent == INTENT_LAND:
            # LAND always overrides RTL (Scenarios 10/12/13).
            self._pending_intent = INTENT_LAND
        elif new_intent == INTENT_RTL and self._pending_intent != INTENT_LAND:
            # RTL is stored only if LAND is not already pending.
            self._pending_intent = INTENT_RTL

        if self._state == STATE_AVOIDING or self._interrupt_pending:
            # Already avoiding or already waiting for GUIDED confirmation:
            # do NOT restart avoidance, do NOT re-request GUIDED (Sc. 10-14).
            return Decision()

        # New interruption starting from a non-avoiding confirmed state.
        self._interrupt_pending = True
        direction, offset = self._select_avoidance(data)
        return Decision(
            mode_requested=MODE_GUIDED,
            start_avoidance=True,
            avoidance_direction=direction,
            avoidance_offset=offset,
        )

    # ------------------------------------------------------------------
    # Obstacle clear / resume
    # ------------------------------------------------------------------
    def _resume(self, data: DetectionInput) -> Decision:
        """Obstacle cleared while avoiding. Resume intent, or auto-mode.

        The mission remains owned by ArduPilot. No waypoint restoration or
        mission continuation logic is invented here: we only request AUTO and
        let /mavros/state + ArduPilot resume the mission.
        """
        self._interrupt_pending = False
        resumed = self._pop_pending_intent_mode()
        if resumed is not None:
            return Decision(
                mode_requested=resumed,
                obstacle_cleared=True,
                resumed_mode=resumed,
            )
        return Decision(
            mode_requested=MODE_AUTO,
            obstacle_cleared=True,
            resumed_mode=MODE_AUTO,
        )

    # ------------------------------------------------------------------
    # Normal operation (no obstacle)
    # ------------------------------------------------------------------
    def _mission_command(self, data: DetectionInput) -> Decision:
        # LAND is checked before RTL so LAND wins on a combined message.
        # This is valid from ANY confirmed state (e.g. RTL + LAND -> request
        # LAND directly). Duplicate-request protection happens in
        # MavrosInterface, not here.
        if self._command_is(data, COMMAND_LAND, LAND_CONFIDENCE_THRESHOLD):
            return Decision(mode_requested=MODE_LAND)
        if self._command_is(data, COMMAND_RTL, RTL_CONFIDENCE_THRESHOLD):
            return Decision(mode_requested=MODE_RTL)
        return Decision()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _pop_pending_intent_mode(self) -> Optional[str]:
        if self._pending_intent == INTENT_LAND:
            self._pending_intent = INTENT_NONE
            return MODE_LAND
        if self._pending_intent == INTENT_RTL:
            self._pending_intent = INTENT_NONE
            return MODE_RTL
        return None

    def _detected_intent(self, data: DetectionInput) -> Optional[int]:
        if self._command_is(data, COMMAND_LAND, LAND_CONFIDENCE_THRESHOLD):
            return INTENT_LAND
        if self._command_is(data, COMMAND_RTL, RTL_CONFIDENCE_THRESHOLD):
            return INTENT_RTL
        return None

    @staticmethod
    def _command_is(data: DetectionInput, command: int, threshold: float) -> bool:
        return data.command == command and data.command_confidence >= threshold

    @staticmethod
    def _obstacle_active(data: DetectionInput) -> bool:
        # Obstacle active = detected flag AND confidence gate. The perception
        # node owns hysteresis; we mirror its "obstacle_detected" verdict.
        return (
            data.obstacle_detected
            and data.obstacle_confidence >= OBSTACLE_CONFIDENCE_THRESHOLD
        )

    @staticmethod
    def _select_avoidance(data: DetectionInput) -> Tuple[int, float]:
        # Avoid in the OPPOSITE direction of the perceived obstacle.
        direction = {
            OBSTACLE_LEFT: AVOID_RIGHT,   # obstacle LEFT  -> avoid RIGHT
            OBSTACLE_RIGHT: AVOID_LEFT,   # obstacle RIGHT -> avoid LEFT
            OBSTACLE_CENTER: AVOID_RIGHT, # obstacle CENTER -> avoid RIGHT
        }.get(data.obstacle_direction, AVOID_RIGHT)

        offset = {
            DISTANCE_FAR: FAR_OFFSET,
            DISTANCE_MEDIUM: MEDIUM_OFFSET,
            DISTANCE_NEAR: NEAR_OFFSET,
        }.get(data.obstacle_distance_level, NEAR_OFFSET)  # cautious default
        return direction, offset

    def _mode_to_state(self, mode: str) -> int:
        # GUIDED is only ever entered for avoidance in this system.
        mapping = {
            MODE_AUTO: STATE_AUTO,
            MODE_GUIDED: STATE_AVOIDING,
            MODE_LAND: STATE_LANDING,
            MODE_RTL: STATE_RTL,
        }
        key = (mode or "").upper()
        # Unknown/empty modes (e.g. INITIALISING, MANUAL, LOITER) keep the
        # current state: we never claim a state we do not model.
        return mapping.get(key, self._state)
