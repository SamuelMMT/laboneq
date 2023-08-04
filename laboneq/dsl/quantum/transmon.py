# Copyright 2022 Zurich Instruments AG
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

from laboneq.dsl.calibration import Calibration, Oscillator, SignalCalibration
from laboneq.dsl.device import LogicalSignalGroup
from laboneq.dsl.device.io_units import LogicalSignal
from laboneq.dsl.dsl_dataclass_decorator import classformatter
from laboneq.dsl.enums import ModulationType
from laboneq.dsl.quantum.quantum_element import QuantumElement, SignalType


@classformatter
@dataclass
class TransmonParameters:
    #: Resonance frequency of the qubits g-e transition.
    resonance_frequency_ge: float
    #: Resonance frequency of the qubits e-f transition.
    resonance_frequency_ef: float
    #: Local oscillator frequency for the drive signals.
    drive_lo_frequency: float
    #: Readout resonantor frequency of the qubit.
    readout_resonator_frequency: float
    #: local oscillator frequency for the readout lines.
    readout_lo_frequency: float
    #: integration delay between readout pulse and data acquisition, defaults to 20 ns.
    readout_integration_delay: Optional[float] = 20e-9
    #: drive power setting, defaults to 10 dBm.
    drive_range: Optional[float] = 10
    #: readout output power setting, defaults to 5 dBm.
    readout_range_out: Optional[float] = 5
    #: readout input power setting, defaults to 10 dBm.
    readout_range_in: Optional[float] = 10
    #: offset voltage for flux control line - defaults to 0.
    flux_offset_voltage: Optional[float] = 0
    #: Free form dictionary of user defined parameters.
    user_defined: Optional[Dict] = field(default_factory=dict)

    @property
    def drive_frequency_ge(self) -> float:
        """Qubit drive frequency."""
        return self.resonance_frequency_ge - self.drive_lo_frequency

    @property
    def drive_frequency_ef(self) -> float:
        """Qubit drive frequency."""
        return self.resonance_frequency_ef - self.drive_lo_frequency

    @property
    def readout_frequency(self) -> float:
        """Readout baseband frequency."""
        return self.readout_resonator_frequency - self.readout_lo_frequency


@classformatter
@dataclass(init=False, repr=True, eq=False)
class Transmon(QuantumElement):
    """A class for a superconducting, flux-tuneable Transmon Qubit."""

    def __init__(
        self,
        uid: str = None,
        signals: Dict[str, LogicalSignal] = None,
        parameters: Optional[Union[TransmonParameters, Dict[str, Any]]] = None,
    ):
        """
        Initializes a new Transmon Qubit.

        Args:
            uid: A unique identifier for the Qubit.
            signals: A mapping of logical signals associated with the qubit.
                Qubit accepts the following keys in the mapping: 'drive', 'measure', 'acquire', 'flux'

                This is so that the Qubit parameters are assigned into the correct signal lines in
                calibration.
            parameters: Parameters associated with the qubit.
                Required for generating calibration and experiment signals via `calibration()` and `experiment_signals()`.
        """
        if isinstance(parameters, dict):
            parameters = TransmonParameters(**parameters)
        super().__init__(uid=uid, signals=signals, parameters=parameters)

    @classmethod
    def from_logical_signal_group(
        cls,
        uid: str,
        lsg: LogicalSignalGroup,
        parameters: Optional[Union[TransmonParameters, Dict[str, Any]]] = None,
    ) -> "Transmon":
        """Transmon Qubit from logical signal group.

        Args:
            uid: A unique identifier for the Qubit.
            lsg: Logical signal group.
                Transmon Qubit understands the following signal line names:

                    - drive: 'drive', 'drive_line'
                    - drive_ef: 'drive_ef', 'drive_line_ef'
                    - measure: 'measure', 'measure_line'
                    - acquire: 'acquire', 'acquire_line'
                    - flux: 'flux', 'flux_line'

                This is so that the Qubit parameters are assigned into the correct signal lines in
                calibration.
            parameters: Parameters associated with the qubit.
        """
        signal_type_map = {
            SignalType.DRIVE: ["drive", "drive_line"],
            SignalType.DRIVE_EF: ["drive_ef", "drive_line_ef"],
            SignalType.MEASURE: ["measure", "measure_line"],
            SignalType.ACQUIRE: ["acquire", "acquire_line"],
            SignalType.FLUX: ["flux", "flux_line"],
        }
        return cls._from_logical_signal_group(
            cls,
            uid=uid,
            lsg=lsg,
            parameters=parameters,
            signal_type_map=signal_type_map,
        )

    def calibration(self, set_local_oscillators=True) -> Calibration:
        """Generate calibration from the parameters and attached signal lines.

        `Qubit` requires `parameters` for it to be able to produce calibration objects.

        Args:
            set_local_oscillators (bool):
                If True, adds local oscillator settings to the calibration.

        Returns:
            calibration:
                Prefilled calibration object from Qubit parameters.
        """

        if set_local_oscillators:
            drive_lo = Oscillator(
                uid=f"{self.uid}_drive_local_osc",
                frequency=self.parameters.drive_lo_frequency,
            )
            readout_lo = Oscillator(
                uid=f"{self.uid}_readout_local_osc",
                frequency=self.parameters.readout_lo_frequency,
            )
        else:
            drive_lo = None
            readout_lo = None

        calib = {}
        if "drive" in self.signals:
            calib[self.signals["drive"]] = SignalCalibration(
                oscillator=Oscillator(
                    uid=f"{self.uid}_drive_ge_osc",
                    frequency=self.parameters.drive_frequency_ge,
                    modulation_type=ModulationType.HARDWARE,
                ),
                local_oscillator=drive_lo,
                range=self.parameters.drive_range,
            )
        if "drive_ef" in self.signals:
            calib[self.signals["drive_ef"]] = SignalCalibration(
                oscillator=Oscillator(
                    uid=f"{self.uid}_drive_ef_osc",
                    frequency=self.parameters.drive_frequency_ef,
                    modulation_type=ModulationType.HARDWARE,
                ),
                local_oscillator=drive_lo,
                range=self.parameters.drive_range,
            )
        if "measure" in self.signals:
            calib[self.signals["measure"]] = SignalCalibration(
                oscillator=Oscillator(
                    uid=f"{self.uid}_measure_osc",
                    frequency=self.parameters.readout_frequency,
                    modulation_type=ModulationType.SOFTWARE,
                ),
                local_oscillator=readout_lo,
                range=self.parameters.readout_range_out,
            )
        if "acquire" in self.signals:
            calib[self.signals["acquire"]] = SignalCalibration(
                oscillator=Oscillator(
                    uid=f"{self.uid}_acquire_osc",
                    frequency=self.parameters.readout_frequency,
                    modulation_type=ModulationType.SOFTWARE,
                ),
                local_oscillator=readout_lo,
                range=self.parameters.readout_range_in,
                port_delay=self.parameters.readout_integration_delay,
            )
        if "flux" in self.signals:
            calib[self.signals["flux"]] = SignalCalibration(
                voltage_offset=self.parameters.flux_offset_voltage,
            )
        return Calibration(calib)
