"""The 'test' class for patchtools."""

from .test_config import TestConfigModuleFunctionality
from .test_exportpatch import TestExportpatchExclude, TestExportpatchExtract, TestExportpatchNormalFunctionality
from .test_fixpatch import TestFixpatchErrorCases, TestFixpatchNormalFunctionalityA, TestFixpatchNormalFunctionalityB

__all__ = [
    'TestConfigModuleFunctionality',
    'TestExportpatchExclude',
    'TestExportpatchExtract',
    'TestExportpatchNormalFunctionality',
    'TestFixpatchErrorCases',
    'TestFixpatchNormalFunctionalityA',
    'TestFixpatchNormalFunctionalityB',
    ]

# vim: sw=4 ts=4 et si:
