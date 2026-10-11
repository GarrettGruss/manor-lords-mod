"""A small save descriptor for tests, in the layout of the real `_descr.sav` (spec 06, part D, fixture-load-bug.md)."""

import struct


def fstring(text: str) -> bytes:
    raw = text.encode("ascii") + b"\x00"
    return struct.pack("<i", len(raw)) + raw


def str_property(name: str, value: str) -> bytes:
    """FString name, FString "StrProperty", 4 zero bytes, int32 size, one byte, FString value."""
    payload = fstring(value)
    return fstring(name) + fstring("StrProperty") + b"\x00" * 4 + struct.pack("<i", len(payload)) + b"\x00" + payload


def descriptor(slot: str, name: str | None = None) -> bytes:
    return (b"GVAS-header" + str_property("LevelName", "Jagged_Cliffs") + str_property("saveName", name or slot)
            + str_property("saveSlot", slot) + fstring("None"))
