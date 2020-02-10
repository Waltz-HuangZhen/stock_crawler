from dataclasses import dataclass


@dataclass
class LogType:
    INFO: int=1
    WARNING: int=2
    ERROR: int=3
