# Copyright 2023 Zurich Instruments AG
# SPDX-License-Identifier: Apache-2.0


from laboneq.data.experiment_results import AcquiredResult as AcquiredResultDATA
from laboneq.dsl.result.acquired_result import AcquiredResult as AcquiredResultDSL
from laboneq.implementation.legacy_adapters.dynamic_converter import convert_dynamic

# converter functions for data type package 'experiment_results'
#  AUTOGENERATED, DO NOT EDIT
from .post_process_experiment_results import post_process


def get_converter_function_experiment_results(orig):
    converter_function_directory = {
        AcquiredResultDSL: convert_AcquiredResult,
    }
    return converter_function_directory.get(orig)


def convert_AcquiredResult(orig: AcquiredResultDSL):
    if orig is None:
        return None
    retval = AcquiredResultDATA()
    retval.axis = convert_dynamic(
        orig.axis,
        source_type_string="List[Union[ArrayLike, List[ArrayLike]]]",
        target_type_string="Any",
        orig_is_collection=True,
        conversion_function_lookup=get_converter_function_experiment_results,
    )
    retval.axis_name = convert_dynamic(
        orig.axis_name,
        source_type_string="List[Union[str, List[str]]]",
        target_type_string="List",
        orig_is_collection=True,
        conversion_function_lookup=get_converter_function_experiment_results,
    )
    retval.data = convert_dynamic(
        orig.data,
        source_type_string="ArrayLike",
        target_type_string="ArrayLike",
        orig_is_collection=True,
        conversion_function_lookup=get_converter_function_experiment_results,
    )
    retval.last_nt_step = convert_dynamic(
        orig.last_nt_step,
        source_type_string="List[int]",
        target_type_string="List[int]",
        orig_is_collection=True,
        conversion_function_lookup=get_converter_function_experiment_results,
    )
    return post_process(
        orig,
        retval,
        conversion_function_lookup=get_converter_function_experiment_results,
    )