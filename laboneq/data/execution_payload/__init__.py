# Copyright 2020 Zurich Instruments AG
# SPDX-License-Identifier: Apache-2.0


# __init__.py of 'execution_payload' package - autogenerated, do not edit
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List

from numpy.typing import ArrayLike


#
# Enums
#
class ServerType(Enum):
    DATA_SERVER = auto()
    WEB_SERVER = auto()
    SCOPE_SERVER = auto()
    POWER_SWITCH_SERVER = auto()

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


class TargetDeviceType(Enum):
    UHFQA = auto()
    HDAWG = auto()
    SHFQA = auto()
    SHFSG = auto()
    SHFQC = auto()
    PQSC = auto()

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


class NearTimeOperationType(Enum):
    CALL = auto()
    ACQUIRE = auto()
    SET = auto()
    PLAY_PULSE = auto()
    DELAY = auto()
    RESERVE = auto()
    ACQUIRE_LOOP_RT = auto()
    ACQUIRE_LOOP_NT = auto()
    NO_OPERATION = auto()
    SET_SOFTWARE_PARM = auto()
    FOR_LOOP = auto()

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


class LoopType(Enum):
    SWEEP = auto()
    AVERAGE = auto()
    HARDWARE = auto()

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


#
# Data Classes
#


@dataclass
class TargetServer:
    uid: str = None
    address: str = None
    port: int = None
    server_type: ServerType = None
    api_level: int = None


@dataclass
class InitializationConfiguration:
    reference_clock_source: str = None
    reference_clock: float = None
    dio_mode: str = None


@dataclass
class JobParameter:
    uid: str = None
    values: List[Any] = field(default_factory=list)
    axis_name: str = None


@dataclass
class SourceCode:
    uid: str = None
    file_name: str = None
    source_text: str = None


@dataclass
class TargetDevice:
    uid: str = None
    server: TargetServer = None
    device_serial: str = None
    device_type: TargetDeviceType = None
    interface: str = None


@dataclass
class Initialization:
    uid: str = None
    device: TargetDevice = None
    source_code: SourceCode = None
    config: InitializationConfiguration = None


@dataclass
class NearTimeOperation:
    uid: str = None
    operation_type: NearTimeOperationType = None
    children: List[Any] = field(default_factory=list)
    args: Dict[str, Any] = field(default_factory=dict)
    parameters: List[JobParameter] = field(default_factory=list)


@dataclass
class WaveForm:
    uid: str = None
    sampling_rate: float = None
    length_samples: int = None
    samples: ArrayLike = None


@dataclass
class NearTimeProgram:
    uid: str = None
    children: List[NearTimeOperation] = field(default_factory=list)


@dataclass
class Recipe:
    uid: str = None
    initializations: List[Initialization] = field(default_factory=list)
    waveforms: List[WaveForm] = field(default_factory=list)
    measurement_map: Dict[str, str] = field(default_factory=dict)


@dataclass
class TargetSetup:
    uid: str = None
    setup_name: str = None
    servers: List[TargetServer] = field(default_factory=list)
    devices: List[TargetDevice] = field(default_factory=list)


@dataclass
class ExecutionPayload:
    uid: str = None
    target_setup: TargetSetup = None
    compiled_experiment_hash: str = None
    experiment_hash: str = None
    device_setup_hash: str = None
    src: List[SourceCode] = field(default_factory=list)
    recipe: Recipe = None
    near_time_program: NearTimeProgram = None