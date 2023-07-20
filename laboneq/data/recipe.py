# Copyright 2019 Zurich Instruments AG
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SignalType(Enum):
    IQ = "iq"
    SINGLE = "single"
    INTEGRATION = "integration"
    MARKER = "marker"


class RefClkType(Enum):
    _10MHZ = 10
    _100MHZ = 100


class TriggeringMode(Enum):
    ZSYNC_FOLLOWER = 1
    DIO_FOLLOWER = 2
    DESKTOP_LEADER = 3
    DESKTOP_DIO_FOLLOWER = 4
    INTERNAL_FOLLOWER = 5


@dataclass(frozen=True)
class NtStepKey:
    indices: tuple[int]


@dataclass
class Gains:
    diagonal: float
    off_diagonal: float


@dataclass
class IO:
    channel: int
    enable: bool | None = None
    modulation: bool | None = None
    oscillator: int | None = None
    oscillator_frequency: int | None = None
    offset: float | None = None
    gains: Gains | None = None
    range: float | None = None
    range_unit: str | None = None
    precompensation: dict[str, dict] | None = None
    lo_frequency: Any | None = None
    port_mode: str | None = None
    port_delay: Any | None = None
    scheduler_port_delay: float = 0.0
    delay_signal: float | None = None
    marker_mode: str | None = None
    amplitude: Any | None = None


@dataclass
class AWG:
    awg: int
    signal_type: SignalType = SignalType.SINGLE
    qa_signal_id: str | None = None
    command_table_match_offset: int | None = None
    feedback_register: int | None = None


@dataclass
class Measurement:
    length: int
    channel: int = 0


@dataclass
class Config:
    repetitions: int = 1
    reference_clock: RefClkType = None
    holdoff: float = 0
    triggering_mode: TriggeringMode = TriggeringMode.DIO_FOLLOWER
    sampling_rate: float | None = None


@dataclass
class Initialization:
    device_uid: str
    config: Config = field(default_factory=Config)
    awgs: list[AWG] = None
    outputs: list[IO] = None
    inputs: list[IO] = None
    measurements: list[Measurement] = field(default_factory=list)
    ppchannels: list[dict[str, Any]] | None = None


@dataclass
class OscillatorParam:
    id: str
    device_id: str
    channel: int
    frequency: float = None
    param: str = None


@dataclass
class IntegratorAllocation:
    signal_id: str
    device_id: str
    awg: int
    channels: list[int]
    weights: str = None
    threshold: float = 0.0


@dataclass
class AcquireLength:
    section_id: str
    signal_id: str
    acquire_length: int


@dataclass
class RealtimeExecutionInit:
    device_id: str
    awg_id: int
    seqc_ref: str
    wave_indices_ref: str
    nt_step: NtStepKey


@dataclass
class Recipe:
    initializations: list[Initialization] = field(default_factory=list)
    realtime_execution_init: list[RealtimeExecutionInit] = field(default_factory=list)
    oscillator_params: list[OscillatorParam] = field(default_factory=list)
    integrator_allocations: list[IntegratorAllocation] = field(default_factory=list)
    acquire_lengths: list[AcquireLength] = field(default_factory=list)
    simultaneous_acquires: list[dict[str, str]] = field(default_factory=list)
    total_execution_time: float = None
    max_step_execution_time: float = None