from dataclasses import dataclass


@dataclass
class CharacterMotionLimits:
    max_speed_mps: float = 0.5
    max_yaw_rate: float = 0.5
    max_body_height_offset: float = 0.05


DEFAULT_CHARACTER_LIMITS = CharacterMotionLimits()
