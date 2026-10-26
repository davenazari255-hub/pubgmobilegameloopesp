"""Console calibration harness.

Run this before building the overlay. It walks every chain in offsets.py and
prints what it finds, so a wrong offset shows up as a line of output instead
of as a blank overlay.
"""
from __future__ import annotations

import time

from src import offsets as O
from src import world as W
from src.memory import AttachError, GameMemory

INTERVAL = 0.5
MAX_ROWS = 6


def report(mem):
    world = W.u_world(mem)
    print(f"[uworld] 0x{world:X}")
    if not mem.valid(world):
        print("  -> UWORLD_CHAIN is wrong")
        return

    controller, pawn = W.local_player(mem, world)
    print(f"[local] controller=0x{controller:X} pawn=0x{pawn:X}")
    if not mem.valid(pawn):
        print("  -> local player chain is wrong")

    cam = W.camera(mem, controller)
    print(
        f"[camera] pos=({cam.position[0]:.1f}, {cam.position[1]:.1f}, "
        f"{cam.position[2]:.1f}) fov={cam.fov:.1f}"
    )

    found = W.actors(mem, world)
    print(f"[actors] {len(found)} in level")

    rows = 0
    for actor in found:
        player = W.read_player(mem, actor, cam.position)
        if player is None:
            continue
        print(
            f"  actor=0x{actor:X} name={player.name!r} hp={player.health:.0f} "
            f"team={player.team} dist={player.distance:.0f} pos={player.position}"
        )
        rows += 1
        if rows >= MAX_ROWS:
            break

    if rows == 0:
        print("  -> nothing matched: check ACTOR_TO_MESH and PAWN_TO_PLAYER_STATE")


def main():
    try:
        mem = GameMemory()
    except AttachError as exc:
        print("[mem]", exc)
        return

    base = mem.module_base(O.MODULE)
    print(f"[base] {O.MODULE} @ 0x{base:X}")

    try:
        while True:
            try:
                report(mem)
            except Exception as exc:
                print("[loop]", type(exc).__name__, exc)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("stopped")
    finally:
        mem.close()


if __name__ == "__main__":
    main()
