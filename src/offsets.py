"""Every offset lives here so a game patch only touches this one file.

CHAIN convention: the first entry is added to the module base, each following
entry is added after dereferencing the previous result, and the final address
is returned. Callers dereference the last hop themselves:

    value = mem.ptr(mem.chain(base, SOME_CHAIN))

So [0x1234] means base + 0x1234, and [0x1234, 0x8] means [base + 0x1234] + 0x8.
Replace every 0x0 with a real value.
"""

# Module the offsets are relative to. Confirm it in Task Manager -> Details.
MODULE = "aow_exe.exe"

# --- UWorld ---------------------------------------------------------------
UWORLD_CHAIN = [0x0]

# --- level and actors -----------------------------------------------------
UWORLD_TO_LEVEL = 0x0
LEVEL_TO_ACTORS = 0x0
LEVEL_TO_ACTOR_COUNT = 0x0

# --- local player ---------------------------------------------------------
UWORLD_TO_GAME_INSTANCE = 0x0
GAME_INSTANCE_TO_LOCAL_PLAYERS = 0x0
LOCAL_PLAYER_TO_CONTROLLER = 0x0
CONTROLLER_TO_PAWN = 0x0

# --- camera ---------------------------------------------------------------
CONTROLLER_TO_CAMERA_MANAGER = 0x0
CAMERA_TO_VIEW_INFO = 0x0
VIEW_INFO_TO_ROTATION = 0xC
VIEW_INFO_TO_FOV = 0x18

# --- actor layout ---------------------------------------------------------
ACTOR_TO_MESH = 0x0
MESH_TO_COMPONENT_TO_WORLD = 0x0
MESH_TO_BONE_ARRAY = 0x0
BONE_COUNT = 0
TRANSFORM_TO_TRANSLATION = 0x10
MATRIX_TO_TRANSLATION = 0x30

# --- player state ---------------------------------------------------------
PAWN_TO_PLAYER_STATE = 0x0
PLAYER_STATE_TO_NAME = 0x0
PAWN_TO_HEALTH = 0x0
PAWN_TO_TEAM = 0x0
PAWN_TO_IS_DEAD = 0x0

# --- calibration flags ----------------------------------------------------
# Flip these while calibrating instead of editing the readers.
COMPONENT_TO_WORLD_IS_TRANSFORM = True
NAME_IS_INLINE_FSTRING = False
BONES_ARE_TRANSFORMS = True
