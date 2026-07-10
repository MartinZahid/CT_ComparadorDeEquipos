"""Standalone constants used across modules (no package imports to avoid cycles)."""

MIN_RAM_GB: int = 1
MAX_RAM_GB: int = 128
MIN_STORAGE_GB: int = 40

PREFERRED_RAM_VALUES: tuple[int, ...] = (16, 32, 8, 64, 24, 12, 48)
