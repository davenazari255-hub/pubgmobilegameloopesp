"""Raw memory to players, and world coordinates to screen pixels."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import offsets as O


@dataclass
class Player:
    address: int = 0
    position: tuple = (0.0, 0.0, 0.0)
    name: str = ""
    health: float = 0.0
    team: int = 0
    dead: bool = False
    distance: float = 0.0
    screen: tuple = None
    head: tuple = None
    bones: dict = field(default_factory=dict)


@dataclass
class Camera:
    position: tuple = (0.0, 0.0, 0.0)
    rotation: tuple = (0.0, 0.0, 0.0)
    fov: float = 80.0


def u_world(mem):
    base = mem.module_base(O.MODULE)
    return mem.ptr(mem.chain(base, O.UWORLD_CHAIN))


def local_player(mem, world):
    """Return (player_controller, pawn) for the local player."""
    game_instance = mem.ptr(world + O.UWORLD_TO_GAME_INSTANCE)
    if not mem.valid(game_instance):
        return 0, 0
    local_players = mem.ptr(game_instance + O.GAME_INSTANCE_TO_LOCAL_PLAYERS)
    if not mem.valid(local_players):
        return 0, 0
    entry = mem.ptr(local_players)
    if not mem.valid(entry):
        return 0, 0
    controller = mem.ptr(entry + O.LOCAL_PLAYER_TO_CONTROLLER)
    if not mem.valid(controller):
        return 0, 0
    return controller, mem.ptr(controller + O.CONTROLLER_TO_PAWN)


def camera(mem, controller):
    cam = Camera()
    manager = mem.ptr(controller + O.CONTROLLER_TO_CAMERA_MANAGER)
    if not mem.valid(manager):
        return cam
    view = manager + O.CAMERA_TO_VIEW_INFO
    cam.position = mem.vec3(view)
    cam.rotation = mem.vec3(view + O.VIEW_INFO_TO_ROTATION)
    cam.fov = mem.f32(view + O.VIEW_INFO_TO_FOV)
    return cam


def actors(mem, world):
    level = mem.ptr(world + O.UWORLD_TO_LEVEL)
    if not mem.valid(level):
        return []
    array = mem.ptr(level + O.LEVEL_TO_ACTORS)
    count = mem.i32(level + O.LEVEL_TO_ACTOR_COUNT)
    if not mem.valid(array) or count <= 0 or count > 20000:
        return []
    return [p for p in mem.block(array, count) if mem.valid(p)]


def read_player(mem, actor, camera_position):
    """Build a Player from an actor. None when the actor is not a player."""
    mesh = mem.ptr(actor + O.ACTOR_TO_MESH)
    if not mem.valid(mesh):
        return None
    state = mem.ptr(actor + O.PAWN_TO_PLAYER_STATE)
    if not mem.valid(state):
        return None

    name = mem.ue4_string(state + O.PLAYER_STATE_TO_NAME)
    if not name or len(name) < 2:
        return None

    player = Player(address=actor, name=name)

    transform = mesh + O.MESH_TO_COMPONENT_TO_WORLD
    if O.COMPONENT_TO_WORLD_IS_TRANSFORM:
        player.position = mem.vec3(transform + O.TRANSFORM_TO_TRANSLATION)
    else:
        player.position = mem.vec3(transform + O.MATRIX_TO_TRANSLATION)

    player.health = mem.f32(actor + O.PAWN_TO_HEALTH)
    player.team = mem.i32(actor + O.PAWN_TO_TEAM)
    player.dead = mem.u8(actor + O.PAWN_TO_IS_DEAD) != 0

    dx = player.position[0] - camera_position[0]
    dy = player.position[1] - camera_position[1]
    dz = player.position[2] - camera_position[2]
    player.distance = math.sqrt(dx * dx + dy * dy + dz * dz) / 100.0
    return player


def rotation_matrix(pitch, yaw, roll):
    """UE4 FRotator in degrees to a 3x3 matrix. Flip signs here if mirrored."""
    p = math.radians(pitch)
    y = math.radians(yaw)
    r = math.radians(roll)
    sp, cp = math.sin(p), math.cos(p)
    sy, cy = math.sin(y), math.cos(y)
    sr, cr = math.sin(r), math.cos(r)
    return (
        (cp * cy, cp * sy, sp),
        (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp),
        (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp),
    )


def world_to_screen(point, cam, width, height):
    """Project a world point to pixels. None when it is behind the camera."""
    if not point:
        return None
    dx = point[0] - cam.position[0]
    dy = point[1] - cam.position[1]
    dz = point[2] - cam.position[2]

    m = rotation_matrix(cam.rotation[0], cam.rotation[1], cam.rotation[2])
    forward = m[0][0] * dx + m[0][1] * dy + m[0][2] * dz
    right = m[1][0] * dx + m[1][1] * dy + m[1][2] * dz
    up = m[2][0] * dx + m[2][1] * dy + m[2][2] * dz

    if forward < 1.0:
        return None

    scale = 1.0 / math.tan(math.radians(cam.fov) * 0.5)
    half_w = width * 0.5
    half_h = height * 0.5
    return (
        half_w + (right / forward) * scale * half_w,
        half_h - (up / forward) * scale * half_h,
    )
