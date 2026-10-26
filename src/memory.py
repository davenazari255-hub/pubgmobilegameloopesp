"""Read-only memory layer for the GameLoop ESP.

External access only: the game process is never injected or written to.
Every read goes through here so a bad offset stays contained.
"""
from __future__ import annotations

import struct

import pymem
import pymem.process

PROCESS_CANDIDATES = (
    "aow_exe.exe",
    "aow_exe64.exe",
    "AppPlayer.exe",
    "AndroidEmulator.exe",
    "AndroidEmulatorEn.exe",
    "AndroidEmulatorEx.exe",
)


class AttachError(RuntimeError):
    pass


class GameMemory:
    """Fault tolerant wrapper around pymem."""

    def __init__(self, candidates=PROCESS_CANDIDATES, verbose=True):
        self.pm = None
        self.name = None
        for name in candidates:
            try:
                pm = pymem.Pymem(name)
            except Exception:
                continue
            if getattr(pm, "process_id", 0):
                self.pm, self.name = pm, name
                break
        if self.pm is None:
            raise AttachError("GameLoop is not running. Tried: " + ", ".join(candidates))

        self.pid = self.pm.process_id
        if verbose:
            print(f"[mem] attached to {self.name} (pid {self.pid})")

    def module(self, module_name):
        mod = pymem.process.module_from_name(self.pm.process_handle, module_name)
        if mod is None:
            raise AttachError(f"module {module_name!r} is not loaded")
        return mod

    def module_base(self, module_name):
        return self.module(module_name).lpBaseOfDll

    def raw(self, address, size):
        try:
            return self.pm.read_bytes(address, size)
        except Exception:
            return bytes(size)

    def u8(self, address):
        return self.raw(address, 1)[0]

    def u16(self, address):
        return struct.unpack("<H", self.raw(address, 2))[0]

    def u32(self, address):
        return struct.unpack("<I", self.raw(address, 4))[0]

    def i32(self, address):
        return struct.unpack("<i", self.raw(address, 4))[0]

    def u64(self, address):
        return struct.unpack("<Q", self.raw(address, 8))[0]

    def f32(self, address):
        return struct.unpack("<f", self.raw(address, 4))[0]

    def vec3(self, address):
        return struct.unpack("<fff", self.raw(address, 12))

    def ptr(self, address):
        return self.u64(address)

    def chain(self, base, offsets):
        """Resolve [[base + o0] + o1] + ... and return the final address.

        Wrap with mem.ptr(...) when you need the pointer value.
        """
        address = base
        for index, offset in enumerate(offsets):
            address += offset
            if index != len(offsets) - 1:
                address = self.ptr(address)
        return address

    def block(self, address, count):
        """Read count consecutive 8 byte pointers in a single syscall."""
        raw = self.raw(address, count * 8)
        return struct.unpack("<" + str(count) + "Q", raw)

    def ue4_string(self, address, limit=32):
        """Read a UE4 FString (TArray<wchar_t>). Empty string when invalid."""
        buffer = self.ptr(address)
        length = self.i32(address + 8)
        if not buffer or length <= 0 or length > 512:
            return ""
        raw = self.raw(buffer, min(length, limit) * 2)
        text = raw.decode("utf-16-le", errors="ignore")
        return text.split(chr(0), 1)[0]

    @staticmethod
    def valid(address, low=0x10000, high=0x7FFFFFFFFFFF):
        return low <= address <= high

    def close(self):
        try:
            self.pm.close_process()
        except Exception:
            pass
