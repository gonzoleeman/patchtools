"""The test suite for the patchtools config module.

Test the local patchtools package 'patch' module,
by calling the exportpatch or fixpatch as needed.
"""

import filecmp
import tempfile
import unittest
from contextlib import chdir     # requires python >= 3.11

from .util import DATA_PATH, call_mut, create_config_file, get_patch_path, import_mut

# the module under test
FIXPATCH = 'fixpatch'
EXPORTPATCH = 'exportpatch'

# commit for one file
COMMIT_1F = '8db816c6f176321e42254badd5c1a8df8bfcfdb4'

# patch name for known commit (no suffix, etc)
PATCH_1F = 'scsi-st-Tighten-the-page-format-heuristics-with-MODE-SELECT'

exportpatch = import_mut(EXPORTPATCH)

class TestConfigModuleFunctionality(unittest.TestCase):
    """Test functionality in the config module."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class for this class. Done once per class."""
        cls.assertTrue(DATA_PATH, 'cannot find "data" subdirectory')

    def test_with_empty_config_file(self):
        """Test using exportpatch with an empty config file."""
        with tempfile.TemporaryDirectory() as tmpdir, chdir(tmpdir):
            create_config_file(empty=True)
            patch_path_expected = get_patch_path(PATCH_1F, dirname=tmpdir)
            (res, pname, err_out) = call_mut(exportpatch, EXPORTPATCH,
                                             ['-w', '-d', tmpdir, COMMIT_1F])
            self.assertEqual(res, 0, f'calling {EXPORTPATCH} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_path_expected.name, 'patch name wrong')
            res = filecmp.cmp(patch_path_expected, f'{DATA_PATH}/{PATCH_1F}.known_good')
            self.assertEqual(res, False, 'patch file expected to be different but is not')
