"""The 'test' class for patchtools."""

from .test_exportpatch import TestExportpatchExclude, TestExportpatchExtract, TestExportpatchNormalFunctionality
from .test_fixpatch import TestFixpatchErrorCases, TestFixpatchNormalFunctionality
from .test_config import TestConfigModuleFunctionality

__all__ = [
    'TestConfigModuleFunctionality',
    'TestExportpatchExclude',
    'TestExportpatchExtract',
    'TestExportpatchNormalFunctionality',
    'TestFixpatchErrorCases',
    'TestFixpatchNormalFunctionality',
    ]

# vim: sw=4 ts=4 et si:
