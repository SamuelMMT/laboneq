# Copyright 2020 Zurich Instruments AG
# SPDX-License-Identifier: Apache-2.0


# __init__.py of 'experiment_results' package - autogenerated, do not edit
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Union

from numpy.typing import ArrayLike

#
# Enums
#

#
# Data Classes
#


@dataclass
class AcquiredResult:
    data: ArrayLike = None
    axis_name: List = field(default_factory=list)
    axis: List[Union[ArrayLike, List[ArrayLike]]] = field(default_factory=list)
    last_nt_step: List[int] = field(default_factory=list)


@dataclass
class ExperimentResults:
    uid: str = None
    acquired_results: Dict[str, AcquiredResult] = field(default_factory=dict)
    user_func_results: Dict = field(default_factory=dict)
    execution_errors: List = field(default_factory=list)
    experiment_hash: str = None
    compiled_experiment_hash: str = None
    execution_payload_hash: str = None