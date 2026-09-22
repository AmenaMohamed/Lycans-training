
# ---------------------------------------------------------------------------
# Detection command values (pada_interfaces/msg/Detection -> command)
# ---------------------------------------------------------------------------
COMMAND_NONE = 0
COMMAND_RTL = 1
COMMAND_LAND = 2

# ---------------------------------------------------------------------------
# Obstacle direction (camera/body frame, reported by perception)
# ---------------------------------------------------------------------------
OBSTACLE_LEFT = -1
OBSTACLE_CENTER = 0
OBSTACLE_RIGHT = 1

# ---------------------------------------------------------------------------
# Avoidance direction (execution frame, opposite to the obstacle direction)
# ---------------------------------------------------------------------------
AVOID_LEFT = -1
AVOID_RIGHT = 1

# ---------------------------------------------------------------------------
# Obstacle distance level
# ---------------------------------------------------------------------------
DISTANCE_FAR = -1
DISTANCE_MEDIUM = 0
DISTANCE_NEAR = 1
# Unknown / unexpected distance levels fall back to the most cautious offset.

# ---------------------------------------------------------------------------
# Confidence thresholds
# ---------------------------------------------------------------------------
LAND_CONFIDENCE_THRESHOLD = 0.85
RTL_CONFIDENCE_THRESHOLD = 0.85
OBSTACLE_CONFIDENCE_THRESHOLD = 0.75

# ---------------------------------------------------------------------------
# Internal states of DecisionManager
# These mirror the CONFIRMED MAVROS flight mode (from /mavros/state) only.
# ---------------------------------------------------------------------------
STATE_AUTO = 0
STATE_AVOIDING = 1
STATE_LANDING = 2
STATE_RTL = 3

# ---------------------------------------------------------------------------
# Mission intents (LAND / RTL suppressed by an obstacle interruption)
# ---------------------------------------------------------------------------
INTENT_NONE = 0
INTENT_LAND = 1
INTENT_RTL = 2

# ---------------------------------------------------------------------------
# MAVROS flight mode names (custom_mode strings)
# ---------------------------------------------------------------------------
MODE_AUTO = "AUTO"
MODE_GUIDED = "GUIDED"
MODE_LAND = "LAND"
MODE_RTL = "RTL"

# ---------------------------------------------------------------------------
# Avoidance offsets (meters)
#
# IMPORTANT (Correction 4): these values are the *offset magnitude* used to
# generate the forward and lateral components of the temporary avoidance
# target with the approved geometry  forward = offset, lateral = offset.
#
# The resulting horizontal displacement from the current position to the
# temporary target is therefore:
#
#     displacement = sqrt(forward^2 + lateral^2) = offset * sqrt(2)
#
# i.e. larger than the offset value itself. The offset is the selected
# avoidance-offset magnitude, NOT the true Euclidean distance to the target.
# None of these values guarantees obstacle clearance.
#
# FAR_OFFSET = 43 m is a theoretical turn-radius baseline derived from the
# supplied aircraft constraint analysis:
#
#     R = V^2 / (g * tan(bank))
#
# with approximately V = 27 m/s and bank = 60 deg:
#
#     R ~= 42.9 m  -> 43 m
#
# MEDIUM_OFFSET = 60 m and NEAR_OFFSET = 85 m are ENGINEERING DESIGN VALUES
# selected for the simulation. They were NOT mathematically derived from the
# constraint analysis and MUST be validated experimentally in SITL.
# ---------------------------------------------------------------------------
FAR_OFFSET = 43.0
MEDIUM_OFFSET = 60.0
NEAR_OFFSET = 85.0
MAX_AVOIDANCE_OFFSET = 100.0

# ---------------------------------------------------------------------------
# MAVLink / MAVROS command constants
# ---------------------------------------------------------------------------
MAV_CMD_DO_REPOSITION = 192
MAV_FRAME_GLOBAL_RELATIVE_ALT_INT = 6  # global lat/lon + alt relative to home
GPS_METERS_PER_DEG_LAT = 111320.0

# ---------------------------------------------------------------------------
# ROS topics and services
# ---------------------------------------------------------------------------
DETECTION_TOPIC = "/vision/detection_cmd"
MAVROS_STATE_TOPIC = "/mavros/state"
MAVROS_GLOBAL_TOPIC = "/mavros/global_position/global"
MAVROS_REL_ALT_TOPIC = "/mavros/global_position/rel_alt"
MAVROS_COMPASS_HDG_TOPIC = "/mavros/global_position/compass_hdg"

SET_MODE_SERVICE = "/mavros/set_mode"
COMMAND_INT_SERVICE = "/mavros/cmd/command_int"

# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------
# Execution-retry timer: RETRIES execution of an already-decided action only.
# It NEVER makes new decisions and NEVER calls DecisionManager.decide().
EXECUTION_RETRY_PERIOD_SEC = 0.1
