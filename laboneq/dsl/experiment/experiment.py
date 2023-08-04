# Copyright 2022 Zurich Instruments AG
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Deque, Dict, List, Optional, Union

from laboneq.core.exceptions import LabOneQException
from laboneq.core.types.enums import DSLVersion
from laboneq.dsl.calibration.calibration import Calibration
from laboneq.dsl.device.io_units.logical_signal import LogicalSignalRef
from laboneq.dsl.enums import (
    AcquisitionType,
    AveragingMode,
    ExecutionType,
    RepetitionMode,
)
from laboneq.dsl.experiment.pulse import Pulse

from ..dsl_dataclass_decorator import classformatter
from .experiment_signal import ExperimentSignal
from .section import AcquireLoopNt, AcquireLoopRt, Case, Match, Section, Sweep

if TYPE_CHECKING:
    from .. import Parameter

experiment_id = 0


def experiment_id_generator():
    global experiment_id
    retval = f"exp_{experiment_id}"
    experiment_id += 1
    return retval


@classformatter
@dataclass(init=True, repr=True, order=True)
class Experiment:
    """LabOne Q Experiment.

    Args:
        uid: UID of the experiment.
        signals: Experiment signals.
        version: Used DSL version.
        epsilon: Epsilon. Not used.
        sections: Sections in the experiment.
    """

    uid: str = field(default_factory=experiment_id_generator)
    signals: Union[Dict[str, ExperimentSignal], List[ExperimentSignal]] = field(
        default_factory=dict
    )
    version: DSLVersion = field(default=DSLVersion.V3_0_0)
    epsilon: float = field(default=0.0)
    sections: List[Section] = field(default_factory=list)
    _section_stack: Deque[Section] = field(
        default_factory=deque, repr=False, compare=False, init=False
    )

    def __post_init__(self):
        if self.signals is not None and isinstance(self.signals, List):
            signals_dict = {}
            for s in self.signals:
                if isinstance(s, str):
                    signals_dict[s] = ExperimentSignal(uid=s)
                else:
                    signals_dict[s.uid] = s
            self.signals = signals_dict

    def add_signal(
        self, uid: str = None, connect_to: LogicalSignalRef = None
    ) -> ExperimentSignal:
        """Add an experiment signal to the experiment.

        Args:
            uid:
                The unique id of the new experiment signal (optional).
            connect_to:
                The `LogicalSignal` this experiment signal shall be connected to.
                Defaults to None, meaning that there is no connection defined yet.

        Returns:
            signal:
                The created and added signal.

        See also [map_signal][laboneq.dsl.experiment.experiment.Experiment.map_signal].
        """
        if uid is not None and uid in self.signals.keys():
            raise LabOneQException(f"Signal with id {uid} already exists.")
        signal = ExperimentSignal(uid=uid, map_to=connect_to)
        self.signals[uid] = signal
        return signal

    def add(self, section: Section):
        """Add a sweep, a section or an acquire loop to the experiment.

        Args:
            section: The object to add.
        """
        self._add_section_to_current_section(section)

    @property
    def experiment_signals_uids(self):
        """A list of experiment signal uids defined in this experiment."""
        return self.signals.keys

    def list_experiment_signals(self) -> List[ExperimentSignal]:
        """A list of experiment signals defined in this experiment.

        Returns:
            signals: List of defined experiment signals.
        """
        return list(self.signals.values())

    def is_experiment_signal(self, uid: str) -> bool:
        """Check if an experiment signal is defined for this experiment.

        Args:
            uid:
                The unique id of the experiment signal to check for.

        Returns:
            is_experiment_signal:
                `True` if the experiment signal is defined in this
                experiment, `False` otherwise.
        """
        return uid in self.signals.keys()

    def map_signal(self, experiment_signal_uid: str, logical_signal: LogicalSignalRef):
        """Connect an experiment signal to a logical signal.

        In order to relate an experiment signal to a logical signal defined in a
        device setup ([DeviceSetup][laboneq.dsl.device.device_setup.DeviceSetup]),
        you need to make a connection between these two types of signals.

        Args:
            experiment_signal_uid:
                The unique id of the experiment signal to be connected.
            logical_signal:
                The logical signal to connect to.

        See also [add_signal][laboneq.dsl.experiment.experiment.Experiment.add_signal].
        """
        if not self.is_experiment_signal(experiment_signal_uid):
            raise LabOneQException(
                f"Unknown experiment signal: {experiment_signal_uid}. Call experiment.experiment_signals to get a "
                f"list of experiment signals defined in this experiment. Call experiment.add_signal() to add a signal "
                f"prior to connect id to a LogicalSignal. "
            )

        self.signals[experiment_signal_uid].map(logical_signal)

    def reset_signal_map(self, signal_map: Dict[str, LogicalSignalRef] = None):
        """Reset, i.e. disconnect, all defined signal connections and
        apply a new signal map if provided.

        Args:
            signal_map: The new signal map to apply.
        """

        for signal in self.signals.values():
            signal.disconnect()
        if signal_map:
            self.set_signal_map(signal_map)

    @property
    def signal_mapping_status(self) -> Dict[str, Any]:
        """Get an overview of the signal mapping.

        Returns:
            signal_mapping:
                A dictionary with entries for:

                - `is_all_mapped`:
                    `True` if all experiment signals are mapped to a logical
                    signal, `False` otherwise.
                - `mapped_signals`:
                    A list of experiment signal uids that have a mapping to a
                    logical signal.
                - `not_mapped_signals`:
                    A list of experiment signal uids that have no mapping to a
                    logical signal.
        """
        is_all_mapped = True
        mapped_signals = list()
        not_mapped_signals = list()

        for signal in self.signals.values():
            if signal.is_mapped():
                mapped_signals.append(signal.uid)
            else:
                is_all_mapped = False
                not_mapped_signals.append(signal.uid)
        return {
            "is_all_mapped": is_all_mapped,
            "mapped_signals": mapped_signals,
            "not_mapped_signals": not_mapped_signals,
        }

    def get_signal_map(self) -> Dict[str, str]:
        return {
            signal.uid: signal.mapped_logical_signal_path
            for signal in self.signals.values()
            if signal.is_mapped()
        }

    def set_signal_map(self, signal_map: Dict[str, LogicalSignalRef]):
        for signal_uid, logical_signal_ref in signal_map.items():
            if signal_uid not in self.signals.keys():
                self._signal_not_found_error(signal_uid, "Cannot apply signal map.")

            self.signals[signal_uid].map(to=logical_signal_ref)

    # Calibration ....................................

    def _signal_not_found_error(self, signal_uid: str, msg: str = None):
        if msg is None:
            msg = ""
        raise LabOneQException(
            f"Signal with id '{signal_uid}' not found in experiment{': ' if msg else '.'}{msg}"
        )

    def set_calibration(self, calibration: Calibration):
        for signal_uid, calib_item in calibration.calibration_items.items():
            if calib_item is not None:
                if signal_uid not in self.signals.keys():
                    self._signal_not_found_error(
                        signal_uid, "Cannot apply experiment signal calibration."
                    )
                self.signals[signal_uid].calibration = calib_item

    def get_calibration(self):
        from ..calibration import Calibration

        experiment_signals_calibration = dict()
        for sig in self.signals.values():
            experiment_signals_calibration[sig.uid] = (
                sig.calibration if sig.is_calibrated() else None
            )

        calibration = Calibration(calibration_items=experiment_signals_calibration)
        return calibration

    def reset_calibration(self, calibration=None):
        try:
            signals = self.signals.values()
        except AttributeError:
            signals = self.signals
        for sig in signals:
            sig.reset_calibration()
        if calibration:
            self.set_calibration(calibration)

    def list_calibratables(self):
        from ..calibration import Calibratable

        calibratables = dict()
        for signal in self.signals.values():
            if isinstance(signal, Calibratable):
                calibratables[signal.uid] = signal.create_info()
        return calibratables

    # Operations .....................................

    def set_node(self, path: str, value: Any):
        """Set the value of an instrument node.

        Args:
            path: Path to the node whose value should be set.
            value: Value that should be set.

        !!! version-changed "Changed in version 2.0"
            Method name renamed from `set` to `set_node`.
            Removed `key` argument.
        """
        current_section = self._peek_section()
        current_section.set_node(path=path, value=value)

    def play(
        self,
        signal,
        pulse,
        amplitude=None,
        phase=None,
        increment_oscillator_phase=None,
        set_oscillator_phase=None,
        length=None,
        pulse_parameters: Optional[Dict[str, Any]] = None,
        precompensation_clear: Optional[bool] = None,
        marker=None,
    ):
        """Play a pulse on a signal line.

        Args:
            signal (str):
                The unique id of the signal to play the pulse on.
            pulse (Pulse):
                The pulse description of the pulse to be played.
            amplitude (float | Parameter):
                Amplitude the pulse shall be played with. Defaults to
                `None`, meaning that the pulse is played as is.
            length (float | Parameter):
                Length for which the pulse shall be played. Defaults to
                `None`, meaning that the pulse is played for its whole length.
            phase (float):
                The desired baseband phase (baseband rotation) with which the
                pulse shall be played. Given in radians, defaults to `None`,
                meaning that the pulse is played with its phase as defined.
            set_oscillator_phase (float):
                The desired oscillator phase at the start of the played pulse, in radians.
                The phase setting affects the pulse played in this command, and all following pulses.
                Defaults to `None`, meaning no change is made and the phase remains continuous.
            increment_oscillator_phase (float):
                The desired phase increment of the oscillator phase
                at the start of the played pulse, in radians.
                The new, incremented phase affects the pulse played in this command, and all following pulses.
                Defaults to `None`, meaning no change is made and the phase remains continuous.
            pulse_parameters (dict):
                Dictionary with user pulse function parameters (re)binding.
            marker (dict):
                Dictionary with markers to play. Example: `marker={"marker1": {"enable": True}}`

        !!! note
            If markers are specified but `pulse=None`, a zero amplitude pulse as long as the end of the longest
            marker will be automatically generated.
        """
        current_section = self._peek_section()
        current_section.play(
            signal=signal,
            pulse=pulse,
            amplitude=amplitude,
            phase=phase,
            increment_oscillator_phase=increment_oscillator_phase,
            set_oscillator_phase=set_oscillator_phase,
            length=length,
            pulse_parameters=pulse_parameters,
            precompensation_clear=precompensation_clear,
            marker=marker,
        )

    def delay(
        self,
        signal: str,
        time: Union[float, Parameter],
        precompensation_clear: Optional[bool] = None,
    ):
        """Delay execution of next operation on the given experiment signal.

        Args:
            signal:
                The unique id of the signal to delay execution of next operation.
            time:
                The delay time in seconds. The parameter can either be
                given as a float or as a sweep parameter.
            precompensation_clear:
                Clear the precompensation filter during this delay.
        """
        current_section = self._peek_section()
        current_section.delay(
            signal=signal, time=time, precompensation_clear=precompensation_clear
        )

    def reserve(self, signal):
        """Reserves an experiment signal for the duration of the active section.

        Reserving an experiment signal in a section means that if there is no
        operation defined on that signal, it is not available for other sections
        as long as the active section is scoped.

        Args:
            signal:
                The unique id of the signal to be reserved in the active
                section.
        """
        current_section = self._peek_section()
        current_section.reserve(signal=signal)

    def acquire(
        self,
        signal: str | list[str],
        handle: str,
        kernel: Pulse | list[Pulse] | None = None,
        length: float | None = None,
        pulse_parameters: dict[str, Any] | list[dict[str, Any] | None] | None = None,
    ):
        """Acquire a signal and make it available in [Result][laboneq.dsl.result.results.Results].

        Args:
            signal: The input signal(s) to acquire data on.
            handle:
                A unique identifier string that allows to retrieve the
                acquired data in the [Result][laboneq.dsl.result.results.Results]
                object.
            kernel: Pulse(s) for filtering the acquired signal.
            length: Integration length for spectroscopy mode.
            pulse_parameters: Dictionary with user pulse function parameters (re)binding.
        """
        current_section = self._peek_rt_section()
        current_section.acquire(
            signal=signal,
            handle=handle,
            kernel=kernel,
            length=length,
            pulse_parameters=pulse_parameters,
        )

    def measure(
        self,
        acquire_signal: str | list[str],
        handle: str,
        integration_kernel: Optional[Pulse | list[Pulse]] = None,
        integration_kernel_parameters: Optional[
            dict[str, Any] | list[dict[str, Any] | None]
        ] = None,
        integration_length: Optional[float] = None,
        measure_signal: Optional[str] = None,
        measure_pulse: Optional[Pulse] = None,
        measure_pulse_length: Optional[float] = None,
        measure_pulse_parameters: Optional[Dict[str, Any]] = None,
        measure_pulse_amplitude: Optional[float] = None,
        acquire_delay: Optional[float] = None,
        reset_delay: Optional[float] = None,
    ):
        """
        Execute a measurement.

        Unifies the optional playback of a measurement pulse, the acquisition of the return signal and an optional delay after the signal acquisition.

        For pulsed spectroscopy, set `integration_length` and either `measure_pulse` or `measure_pulse_length`.
        For CW spectroscopy, set only `integration_length` and do not specify the measure signal.
        For multistate discrimination, use lists of equal length for acquire_signal, integration_kernel and integration_kernel_parameters.
        For all other measurements, set either length or pulse for both the measure pulse and integration kernel.

        Args:

            acquire_signal: A string or list of strings that specifies the signal(s) for the data acquisition.
            handle: A string that specifies the handle of the acquired results.
            integration_kernel: An optional Pulse object or list of Pulse objects that specifies the kernel(s) for integration.
            integration_kernel_parameters: An optional dictionary (or list thereof) that contains pulse parameters for the integration kernel.
            integration_length: An optional float that specifies the integration length.
            measure_signal: An optional string that specifies the signal to measure.
            measure_pulse: An optional Pulse object that specifies the readout pulse for measurement.

                If this parameter is not supplied, no pulse will be played back for the measurement,
                which enables CW spectroscopy on SHFQA instruments.

            measure_pulse_length: An optional float that specifies the length of the measurement pulse.
            measure_pulse_parameters: An optional dictionary that contains parameters for the measurement pulse.
            measure_pulse_amplitude: An optional float that specifies the amplitude of the measurement pulse.
            acquire_delay: An optional float that specifies the delay between the acquisition and the measurement.
            reset_delay: An optional float that specifies the delay after the acquisition to allow for state relaxation or signal processing.
        """
        current_section = self._peek_section()
        current_section.measure(
            acquire_signal=acquire_signal,
            handle=handle,
            integration_kernel=integration_kernel,
            integration_kernel_parameters=integration_kernel_parameters,
            integration_length=integration_length,
            measure_signal=measure_signal,
            measure_pulse=measure_pulse,
            measure_pulse_length=measure_pulse_length,
            measure_pulse_parameters=measure_pulse_parameters,
            measure_pulse_amplitude=measure_pulse_amplitude,
            acquire_delay=acquire_delay,
            reset_delay=reset_delay,
        )

    def call(self, func_name, **kwargs):
        """Add a callback function in the execution of the experiment.

        The callback is called by the LabOne Q software as part of executing the
        experiment and in sequence with the other experiment operations.

        Args:
            func_name: The callback function.
            kwargs: These arguments are passed to the callback function as is.
        """
        current_section = self._peek_section()
        current_section.call(func_name=func_name, **kwargs)

    # Sections .......................................

    def sweep(
        self,
        parameter,
        execution_type=None,
        uid=None,
        alignment=None,
        reset_oscillator_phase=False,
        chunk_count=1,
    ):
        """Define a sweep section.

        Sections need to open a scope in the following way:

        ``` py
            with exp.sweep(...):
                # here come the operations that shall be executed in the sweep section
        ```

        !!! note
            A near time section cannot be defined in the scope of a real
            time section.

        Args:
            uid: The unique ID for this section.
            parameter: The sweep parameter(s) that is used in this section.
                The argument can be given as a single sweep parameter or a list
                of sweep parameters of equal length. If multiple sweep parameters are given, the
                parameters are executed in parallel in this sweep loop.
            execution_type: Defines if the sweep is executed in near time or
                real time. Defaults to
                [ExecutionType.NEAR_TIME][laboneq.core.types.enums.execution_type.ExecutionType.NEAR_TIME].
            alignment: Alignment of the operations in the section. Defaults to
                [SectionAlignment.LEFT][laboneq.core.types.enums.section_alignment.SectionAlignment.LEFT].
            reset_oscillator_phase: When True, reset all oscillators at the start of
                each step.
            chunk_count: The number of chunks to split the sweep into. Defaults to 1.

        """
        parameters = parameter if isinstance(parameter, list) else [parameter]
        return Experiment._SweepSectionContext(
            self,
            uid=uid,
            parameters=parameters,
            execution_type=execution_type,
            alignment=alignment,
            reset_oscillator_phase=reset_oscillator_phase,
            chunk_count=chunk_count,
        )

    class _SweepSectionContext:
        def __init__(
            self,
            experiment,
            uid,
            parameters,
            execution_type,
            alignment,
            reset_oscillator_phase,
            chunk_count,
        ):
            self.exp = experiment
            args = {"parameters": parameters}
            if uid is not None:
                args["uid"] = uid
            if execution_type is not None:
                args["execution_type"] = execution_type
                if execution_type is ExecutionType.NEAR_TIME:
                    try:
                        parent_section = experiment._peek_rt_section()
                    except LabOneQException:
                        pass
                    else:
                        if parent_section is not None:
                            raise LabOneQException(
                                "Near-time sweep not allowed within real-time context"
                            )

            if alignment is not None:
                args["alignment"] = alignment

            if reset_oscillator_phase is not None:
                args["reset_oscillator_phase"] = reset_oscillator_phase

            args["chunk_count"] = chunk_count

            self.sweep = Sweep(**args)

        def __enter__(self):
            self.exp._push_section(self.sweep)
            if len(self.sweep.parameters) == 1:
                return self.sweep.parameters[0]
            return tuple(self.sweep.parameters)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.exp._pop_and_add_section()

    def acquire_loop_nt(self, count, averaging_mode=AveragingMode.CYCLIC, uid=None):
        """Define an acquire section with averaging in near time.

        Sections need to open a scope in the following way:

        ``` py
            with exp.acquire_loop_nt(...):
                # here come the operations that shall be executed in the acquire_loop_nt section
        ```

        !!! note
            A near time section cannot be defined in the scope of a real
            time section.

        Args:
            uid: The unique ID for this section.
            count: The number of acquire iterations.
            averaging_mode: The mode of how to average the acquired data.
                Defaults to [AveragingMode.CYCLIC][laboneq.core.types.enums.averaging_mode.AveragingMode.CYCLIC].
        """
        return Experiment._AcquireLoopNtSectionContext(
            self, uid=uid, count=count, averaging_mode=averaging_mode
        )

    class _AcquireLoopNtSectionContext:
        def __init__(self, experiment, count, averaging_mode, uid=None):
            self.exp = experiment
            self.acquire_loop = AcquireLoopNt(
                uid=uid, count=count, averaging_mode=averaging_mode
            )

        def __enter__(self):
            self.exp._push_section(self.acquire_loop)
            return self.acquire_loop

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.exp._pop_and_add_section()

    def acquire_loop_rt(
        self,
        count,
        averaging_mode=AveragingMode.CYCLIC,
        repetition_mode=RepetitionMode.FASTEST,
        repetition_time=None,
        acquisition_type=AcquisitionType.INTEGRATION,
        uid=None,
        reset_oscillator_phase=False,
    ):
        """Define an acquire section with averaging in real time.

        Sections need to open a scope in the following way:

        ``` py
            with exp.acquire_loop_rt(...):
                # here come the operations that shall be executed in the acquire_loop_rt section
        ```

        !!! note
            A near time section cannot be defined in the scope of a real
            time section.

        Args:
            uid: The unique ID for this section.
            count: The number of acquire iterations.
            averaging_mode: The mode of how to average the acquired data.
                Defaults to [AveragingMode.CYCLIC][laboneq.core.types.enums.averaging_mode.AveragingMode.CYCLIC].
                Further options: [AveragingMode.SEQUENTIAL][laboneq.core.types.enums.averaging_mode.AveragingMode.SEQUENTIAL]
                and [AveragingMode.SINGLE_SHOT][laboneq.core.types.enums.averaging_mode.AveragingMode.SINGLE_SHOT].
                Single shot measurements are always averaged in cyclic mode.
            repetition_mode: Defines the shot repetition mode. Defaults to
                [RepetitionMode.FASTEST][laboneq.core.types.enums.repetition_mode.RepetitionMode.FASTEST].
                Further options are
                [RepetitionMode.CONSTANT][laboneq.core.types.enums.repetition_mode.RepetitionMode.CONSTANT]
                and [RepetitionMode.AUTO][laboneq.core.types.enums.repetition_mode.RepetitionMode.AUTO].
            repetition_time: This is the shot repetition time in sec. This
                argument is only required and valid if `repetition_mode` is
                [RepetitionMode.CONSTANT][laboneq.core.types.enums.repetition_mode.RepetitionMode.CONSTANT].
                The parameter can either be given as a float or as a sweep parameter
                ([Parameter][laboneq.dsl.parameter.Parameter]).
            acquisition_type: This is the acquisition type.
                Defaults to [AcquisitionType.INTEGRATION][laboneq.core.types.enums.acquisition_type.AcquisitionType.INTEGRATION].
                Further options are
                [AcquisitionType.SPECTROSCOPY][laboneq.core.types.enums.acquisition_type.AcquisitionType.SPECTROSCOPY],
                [AcquisitionType.DISCRIMINATION][laboneq.core.types.enums.acquisition_type.AcquisitionType.DISCRIMINATION]
                and [AcquisitionType.RAW][laboneq.core.types.enums.acquisition_type.AcquisitionType.RAW].
            reset_oscillator_phase: When True, the phase of every oscillator is reset at
                the start of the each step of the acquire loop.
        """
        return Experiment._AcquireLoopRtSectionContext(
            self,
            uid=uid,
            count=count,
            averaging_mode=averaging_mode,
            repetition_mode=repetition_mode,
            repetition_time=repetition_time,
            acquisition_type=acquisition_type,
            reset_oscillator_phase=reset_oscillator_phase,
        )

    class _AcquireLoopRtSectionContext:
        def __init__(
            self,
            experiment,
            count,
            averaging_mode,
            repetition_mode,
            repetition_time,
            acquisition_type,
            reset_oscillator_phase,
            uid=None,
        ):
            self.exp = experiment
            kwargs = dict(
                count=count,
                averaging_mode=averaging_mode,
                repetition_mode=repetition_mode,
                repetition_time=repetition_time,
                acquisition_type=acquisition_type,
                reset_oscillator_phase=reset_oscillator_phase,
            )
            if uid is not None:
                kwargs["uid"] = uid
            self.acquire_shots = AcquireLoopRt(**kwargs)

        def __enter__(self):
            self.exp._push_section(self.acquire_shots)
            return self.acquire_shots

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.exp._pop_and_add_section()

    def section(
        self,
        length=None,
        alignment=None,
        uid=None,
        on_system_grid=None,
        play_after: Optional[Union[str, Section, List[Union[str, Section]]]] = None,
        trigger: Optional[Dict[str, Dict[str, int]]] = None,
    ):
        """Define an section for scoping operations.

        Sections need to open a scope in the following way:

        ``` py
            with exp.section(...):
                # here come the operations that shall be executed in the section
        ```

        !!! note
            A near time section cannot be defined in the scope of a real
            time section.

        Args:
            uid: The unique ID for this section.
            length: The minimal duration of the section in seconds. The
                scheduled section might be slightly longer, as its length is
                rounded to the next multiple of the section timing grid.
                Defaults to `None` which means that the section length is
                derived automatically from the contained operations.
                The parameter can either be given as a float or as a sweep
                parameter ([Parameter][laboneq.dsl.parameter.Parameter]).
            alignment: Alignment of the operations in the section. Defaults to
                [SectionAlignment.LEFT][laboneq.core.types.enums.section_alignment.SectionAlignment.LEFT].
            play_after: Play this section after the end of the section(s) with the
                given ID(s). Defaults to None.
            trigger: Play a pulse a trigger pulse for the duration of this section.
                See below for details.
            on_system_grid: If True, the section boundaries are always rounded to the
                system grid, even if the signals would allow for tighter alignment.

        The individual trigger (a.k.a marker) ports on the device are addressed via the
        experiment signal that is mapped to the corresponding analog port.
        For playing trigger pulses, pass a dictionary via the `trigger` argument. The
        keys of the dictionary must be an ID of an
        [ExperimentSignal][laboneq.dsl.experiment.experiment_signal.ExperimentSignal].
        Each value is another `dict` of the form:

        ``` py
            {"state": value}
        ```

        `value` is a bit field that enables the individual trigger signals (on the
        devices that feature more than a single one).

        ``` py
            {"state": 1}  # raise trigger signal 1
            {"state": 0b10}  # raise trigger signal 2 (on supported devices)
            {"state": 0b11}  # raise both trigger signals
        ```

        As a more complete example, to fire a trigger pulse on the first port associated
        with signal `"drive_line"`, call:

        ``` py
            with exp.section(..., trigger={"drive_line": {"state": 0b01}}):
                ...
        ```

        When trigger signals on the same signal are issued in nested sections, the values
        are ORed.

        !!! version-changed "Changed in version 2.0.0"
            Removed deprecated `offset` argument.
        """
        return Experiment._SectionSectionContext(
            self,
            uid=uid,
            length=length,
            alignment=alignment,
            play_after=play_after,
            trigger=trigger,
            on_system_grid=on_system_grid,
        )

    class _SectionSectionContext:
        def __init__(
            self,
            experiment,
            uid,
            length=None,
            alignment=None,
            play_after=None,
            trigger=None,
            on_system_grid=None,
        ):
            self.exp = experiment
            args = {}
            if uid is not None:
                args["uid"] = uid
            if length is not None:
                args["length"] = length
            if alignment is not None:
                args["alignment"] = alignment
            if play_after is not None:
                args["play_after"] = play_after
            if trigger is not None:
                args["trigger"] = trigger
            if on_system_grid is not None:
                args["on_system_grid"] = on_system_grid

            self.section = Section(**args)

        def __enter__(self):
            self.exp._push_section(self.section)
            return self.section

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.exp._pop_and_add_section()

    def _push_section(self, section):
        if section.execution_type is None:
            if self._section_stack:
                parent_section = self._peek_section()
                execution_type = parent_section.execution_type
            else:
                execution_type = ExecutionType.NEAR_TIME
            section.execution_type = execution_type
        self._section_stack.append(section)

    def _pop_and_add_section(self):
        if not self._section_stack:
            raise LabOneQException(
                "Internal error: Section stack should not be empty. Unbalanced push/pop."
            )
        section = self._section_stack.pop()
        self._add_section_to_current_section(section)

    def _add_section_to_current_section(self, section):
        if not self._section_stack:
            self.sections.append(section)
        else:
            current_section = self._section_stack[-1]
            current_section.add(section)

    def _peek_section(self):
        if not self._section_stack:
            raise LabOneQException(
                "No section in experiment. Use 'with your_exp.section(...):' to create a section scope first."
            )
        return self._section_stack[-1]

    def _peek_rt_section(self):
        if not self._section_stack:
            raise LabOneQException(
                "No section in experiment. Use 'with your_exp.section(...):' to create a section scope first."
            )
        for s in reversed(self._section_stack):
            if s.execution_type == ExecutionType.REAL_TIME:
                return s
        raise LabOneQException(
            "No surrounding realtime section in experiment. Use 'with your_exp.acquire_loop_rt(...):' to create a section scope first."
        )

    def accept_section_visitor(self, visitor, sections=None):
        if sections is None:
            sections = self.sections
        for section in sections:
            visitor(section)
            self.accept_section_visitor(visitor, section.sections)

    def match_local(
        self,
        handle: str,
        uid: str = None,
        play_after: Optional[Union[str, Section, List[Union[str, Section]]]] = None,
    ):
        """Define a section which switches between different child sections based
        on a QA measurement on an SHFQC.

        Match needs to open a scope in the following way:

        ``` py
            with exp.match_local(...):
                # here come the different branches to be selected
        ```

        !!! note
            Only subsections of type `Case` are allowed.

        Args:
            uid: The unique ID for this section.
            handle: A unique identifier string that allows to retrieve the
                acquired data.
            play_after: Play this section after the end of the section(s) with the
                given ID(s). Defaults to None.

        """
        return Experiment._MatchSectionContext(
            self,
            uid=uid,
            handle=handle,
            user_register=None,
            play_after=play_after,
            local=True,
        )

    def match_global(
        self,
        handle: str,
        uid: str = None,
        play_after: Optional[Union[str, Section, List[Union[str, Section]]]] = None,
    ):
        """Define a section which switches between different child sections based
        on a QA measurement via the PQSC.

        Match needs to open a scope in the following way:

        ``` py
            with exp.match_global(...):
                # here come the different branches to be selected
        ```

        !!! note
            Only subsections of type `Case` are allowed.

        Args:
            uid: The unique ID for this section.
            handle: A unique identifier string that allows to retrieve the
                acquired data.
            play_after: Play this section after the end of the section(s) with the
                given ID(s). Defaults to None.

        """
        return Experiment._MatchSectionContext(
            self,
            uid=uid,
            handle=handle,
            user_register=None,
            play_after=play_after,
            local=False,
        )

    class _MatchSectionContext:
        def __init__(
            self,
            experiment,
            uid,
            handle,
            user_register,
            local,
            play_after=None,
        ):
            self.exp = experiment
            args = {"handle": handle}
            if uid is not None:
                args["uid"] = uid
            if play_after is not None:
                args["play_after"] = play_after
            args["local"] = local
            args["user_register"] = user_register

            self.section = Match(**args)

        def __enter__(self):
            self.exp._push_section(self.section)
            return self.section

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.exp._pop_and_add_section()

    def match(
        self,
        handle: Optional[str] = None,
        user_register: Optional[int] = None,
        uid: str = None,
        play_after: Optional[Union[str, Section, List[Union[str, Section]]]] = None,
    ):
        """Define a section which switches between different child sections based
        on a QA measurement (using `handle`) or a user register (using `user_register`).

        In case of the QA measurement option, the feedback path (local, or global,
        via PQSC) is chosen automatically.

        Match needs to open a scope in the following way:

        ``` py
            with exp.match(...):
                # here come the different branches to be selected
        ```

        !!! note
            Only subsections of type `Case` are allowed. Exactly one of `handle` or
            `user_register` must be specified, the other one must be None. The user register
            is evaluated only at the beginning of the experiment, not during the experiment,
            and only a few user registers per AWG can be used due to the limited number of
            processor registers.

        Args:
            uid: The unique ID for this section.
            handle: A unique identifier string that allows to retrieve the
                acquired data.
            user_register: The user register to use for the match.
            play_after: Play this section after the end of the section(s) with the
                given ID(s). Defaults to None.

        """
        return Experiment._MatchSectionContext(
            self,
            uid=uid,
            handle=handle,
            user_register=user_register,
            play_after=play_after,
            local=None,
        )

    def case(self, state: int, uid: str = None):
        """Define a section which plays after matching with the given value to the
        result of a QA measurement.

        Case needs to open a scope in the following way:

        ``` py
            with exp.case(...):
                # here come the operations that shall be executed in the section
        ```

        !!! note
            No subsections are allowed, only [play][laboneq.dsl.experiment.experiment.Experiment.play]
            and [delay][laboneq.dsl.experiment.experiment.Experiment.delay].

        Args:
            uid: The unique ID for this section.
            state: The state that this section is executed for.
        """
        if not isinstance(self._peek_section(), Match):
            raise LabOneQException("Case section must be inside a Match section")
        return Experiment._CaseSectionContext(
            self,
            uid=uid,
            state=state,
        )

    class _CaseSectionContext:
        def __init__(
            self,
            experiment,
            uid,
            state,
        ):
            self.exp = experiment
            args = {"state": state}
            if uid is not None:
                args["uid"] = uid

            self.section = Case(**args)

        def __enter__(self):
            self.exp._push_section(self.section)
            return self.section

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.exp._pop_and_add_section()

    @staticmethod
    def load(filename):
        from ..serialization import Serializer

        # TODO ErC: Error handling
        return Serializer.from_json_file(filename, Experiment)

    def save(self, filename):
        from ..serialization import Serializer

        # TODO ErC: Error handling
        Serializer.to_json_file(self, filename)

    def load_signal_map(self, filename):
        from ..serialization import Serializer

        # TODO ErC: Error handling
        signal_map = Serializer.from_json_file(filename, dict)
        self.set_signal_map(signal_map)

    def save_signal_map(self, filename):
        from ..serialization import Serializer

        # TODO ErC: Error handling
        Serializer.to_json_file(self.get_signal_map(), filename)

    @staticmethod
    def _all_subsections(section):
        retval = [section]
        for s in section.sections:
            retval.extend(Experiment._all_subsections(s))

        return retval

    def all_sections(self):
        retval = []
        for s in self.sections:
            retval.extend(Experiment._all_subsections(s))
        return retval


_store = threading.local()
_store.active_contexts = []


class ExperimentContext:
    def __init__(self, experiment: Experiment):
        self.experiment = experiment
        self.calibration = None

    def __enter__(self):
        _store.active_contexts.append(self)
        return self.experiment

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.calibration is not None:
            self.experiment.set_calibration(self.calibration)
        _store.active_contexts.pop()


def current_context() -> ExperimentContext:
    try:
        return _store.active_contexts[-1]
    except IndexError as e:
        raise LabOneQException(
            "Not in an experiment context. Use '@experiment' to create an experiment scope first."
        ) from e
