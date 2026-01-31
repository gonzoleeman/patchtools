"""The 'test' class for patchtools."""

from .test_exportpatch import TestExportpatchExclude, TestExportpatchExtract, TestExportpatchNormalFunctionality
from .test_fixpatch import TestFixpatchErrorCases, TestFixpatchNormalFunctionality

__all__ = [
    'TestExportpatchExclude',
    'TestExportpatchExtract',
    'TestExportpatchNormalFunctionality',
    'TestFixpatchErrorCases',
    'TestFixpatchNormalFunctionality',
    ]

# vim: sw=4 ts=4 et si:
