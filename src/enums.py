from enum import Enum


class Strategy(str, Enum):
    FIXED = "fixed"
    DYNAMIC = "dynamic"
    PAUSE_AFTER_LOSS = "pause_after_loss"
    PERCENT = "percent"
    GUARDRAILS = "guardrails"
    VPW = "vpw"


class DataSource(str, Enum):
    SYNTHETIC = "synthetic"
    HISTORICAL = "historical"


class DistributionName(str, Enum):
    BOX_MULLER = "box_muller"
    STUDENT_T = "student_t"
