# Copyright 2023 Zurich Instruments AG
# SPDX-License-Identifier: Apache-2.0


# __init__.py of 'experiment_description' package - autogenerated, do not edit
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from numbers import Number
from typing import Any, Dict, List, Optional, Union

from numpy.typing import ArrayLike


#
# Enums
#
class AcquisitionType(Enum):
    DISCRIMINATION = auto()
    INTEGRATION = auto()
    RAW = auto()
    SPECTROSCOPY = auto()

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


class AveragingMode(Enum):
    CYCLIC = auto()
    SEQUENTIAL = auto()
    SINGLE_SHOT = auto()

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


class ExecutionType(Enum):
    NEAR_TIME = auto()
    REAL_TIME = auto()

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


class RepetitionMode(Enum):
    AUTO = auto()
    CONSTANT = auto()
    FASTEST = auto()

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


class SectionAlignment(Enum):
    LEFT = auto()
    RIGHT = auto()

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


#
# Data Classes
#


@dataclass
class SignalCalibration:
    uid: str = None
    oscillator: Optional[Any] = None
    local_oscillator: Optional[Any] = None
    mixer_calibration: Optional[Any] = None
    precompensation: Optional[Any] = None
    port_delay: Optional[Any] = None
    port_mode: Optional[Any] = None
    delay_signal: Optional[Any] = None
    voltage_offset: Optional[Any] = None
    range: Optional[Any] = None
    threshold: Optional[Any] = None
    amplitude: Optional[Any] = None


@dataclass
class Operation:
    uid: str = None


@dataclass
class ExperimentSignal:
    uid: str = None
    calibration: Optional[Any] = None


@dataclass
class Parameter:
    uid: str = None


@dataclass
class Pulse:
    uid: str = None


@dataclass
class Section:
    uid: str = None
    alignment: SectionAlignment = None
    execution_type: Optional[ExecutionType] = None
    length: Optional[float] = None
    play_after: List[str] = field(default_factory=list)
    children: List[Operation] = field(default_factory=list)
    trigger: Dict = field(default_factory=dict)
    on_system_grid: Optional[bool] = None


@dataclass
class Acquire(Operation):
    signal: str = None
    handle: str = None
    kernel: Pulse = None
    length: float = None
    pulse_parameters: Optional[Any] = None


@dataclass
class AcquireLoopNt(Section):
    uid: str = None
    averaging_mode: AveragingMode = None
    count: int = None
    execution_type: ExecutionType = None


@dataclass
class AcquireLoopRt(Section):
    uid: str = None
    acquisition_type: AcquisitionType = None
    averaging_mode: AveragingMode = None
    count: int = None
    execution_type: ExecutionType = None
    repetition_mode: RepetitionMode = None
    repetition_time: float = None
    reset_oscillator_phase: bool = None


@dataclass
class Call(Operation):
    func_name: Any = None
    args: Dict = field(default_factory=dict)


@dataclass
class Case(Section):
    uid: str = None
    state: int = None


@dataclass
class Delay(Operation):
    signal: str = None
    time: Parameter = None
    precompensation_clear: Optional[bool] = None


@dataclass
class Experiment:
    uid: str = None
    signals: Union[Dict[str, ExperimentSignal], List[ExperimentSignal]] = None
    epsilon: float = None
    sections: List[Section] = field(default_factory=list)
    pulses: List[Pulse] = field(default_factory=list)


@dataclass
class LinearSweepParameter(Parameter):
    uid: str = None
    start: Number = None
    stop: Number = None
    count: int = None
    axis_name: str = None


@dataclass
class Match(Section):
    uid: str = None
    handle: str = None
    local: bool = None


@dataclass
class PlayPulse(Operation):
    signal_uid: str = None
    pulse: Pulse = None
    amplitude: Union[float, complex, Parameter] = None
    increment_oscillator_phase: Parameter = None
    phase: float = None
    set_oscillator_phase: float = None
    length: Parameter = None
    pulse_parameters: Optional[Dict] = None
    precompensation_clear: Optional[bool] = None
    marker: Optional[Dict] = None


@dataclass
class PulseFunctional(Pulse):
    uid: str = None
    function: str = None
    amplitude: float = None
    length: float = None
    pulse_parameters: Optional[Dict] = None


@dataclass
class PulseSampledComplex(Pulse):
    uid: str = None
    samples: ArrayLike = None


@dataclass
class PulseSampledReal(Pulse):
    uid: str = None
    samples: ArrayLike = None


@dataclass
class Reserve(Operation):
    signal: str = None


@dataclass
class Set(Operation):
    uid: str = None
    path: str = None
    key: str = None
    value: Any = None


@dataclass
class Sweep(Section):
    uid: str = None
    parameters: List[Parameter] = field(default_factory=list)
    reset_oscillator_phase: bool = None
    execution_type: ExecutionType = None


@dataclass
class SweepParameter(Parameter):
    uid: str = None
    values: ArrayLike = None
    axis_name: str = None
