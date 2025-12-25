"""The test suite for the patchtools exportpatch command.

Test using the locally available 'exportpatch' command, and its
libraries. Assume the local config files are correct."""

import filecmp
import os
import tempfile
import unittest
from pathlib import Path
from shutil import copy
from subprocess import run


def my_run_command(command, our_input=None, cwd=None):
    """Run the specified command."""
    proc = run(command.split(), encoding='utf-8', check=False, cwd=cwd,
               input=our_input, capture_output=True)
    return (proc.returncode, proc.stdout, proc.stderr)


def get_patch_path(fname, dirname=None, prefix='', suffix='', truncate=64):
    """Return a patch filename that isn't too long"""
    truncate_chars = truncate - len(fname) - len(prefix + suffix)
    if truncate_chars < 0:
        fname = fname[0:truncate_chars]
    fpath = Path(prefix + fname + suffix)
    if dirname:
        fpath = Path(dirname) / fpath
    return fpath


def find_data_dir_path():
    """Find the 'data' directory path, if possible.

    Look first in the current directory. If not there,
    then look for a 'test' subdirectory, and look there."""
    for data_pathname in ['data', 'test/data']:
        data_path = Path(data_pathname)
        if data_path.is_dir():
            return data_path
    return None


# the command under test
CUT = 'exportpatch'

# our testing config file
TEST_CONFIG_SRC = 'patch.cfg.for_testing'

# commit for one file
COMMIT_1F = '8db816c6f176321e42254badd5c1a8df8bfcfdb4'

# commit for two files
COMMIT_2F = '362432e9b9aefb914ab7d9f86c9fc384a6620c41'

# patch name for known commit (no suffix, etc)
PATCH_1F = 'scsi-st-Tighten-the-page-format-heuristics-with-MODE-SELECT'

# patch name for known commit with 2 files
PATCH_2F = 'scsi-libsas-Add-rollback-handling-when-an-error-occurs'

# patchname for the one file in the simple commit
PATCH_FILE_1F = 'drivers/scsi/st.c'

# patchname pattern for both files in 2-file commit
PATCH_FILE_PAT_2F = 'drivers/scsi/libsas/'

# patchname for one file in 2-file commit
PATCH_FILE_FIRST_2F = 'drivers/scsi/libsas/sas_internal.h'


class TestExportpatchNormalFunctionality(unittest.TestCase):
    """Test normal functionality for 'exportpatch'"""

    def setUp(self):
        """Set up for the tests in this class."""
        self.ddir = find_data_dir_path()
        self.assertTrue(self.ddir, 'cannot find "data" subdirectory')

    def copy_config_from_ddir(self, to_dir):
        """Copy our config file to our data directory."""
        src_path = self.ddir / TEST_CONFIG_SRC
        copy(src_path, Path(to_dir) / 'patch.cfg')

    def test_to_file_in_dir_defaults_1f(self):
        """Test exportpatch of one file to file/dir, using defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_in_dir_defaults_2f(self):
        """Test exportpatch of two files to file/dir, using defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_2F, dirname=tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} {COMMIT_2F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_2F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_suffix(self):
        """Test exportpatch to file/dir, with a suffix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir, suffix='.patch')
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -s -d {tmpdir} {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_numeric_default(self):
        """Test exportpatch to file/dir, with numeric filename, using default start"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir, prefix='0001-')
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} -n {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_numeric_s2(self):
        """Test exportpatch to file/dir, with numeric filename, using start number 2"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir, prefix='0002-')
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} -n -N 2 {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_numeric_w3(self):
        """Test exportpatch to file/dir, with numeric filename, using width of 3"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir, prefix='001-')
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} -n --num-width 3 {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_overwrite_force(self):
        """Test exportpatch to file/dir, where patch already exists, using overwrite"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir)
            # make sure our output file doesn't exist, then create empty one
            ofile_path.unlink(missing_ok=True)
            ofile_path.touch()
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} -f {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_overwrite_no_force(self):
        """Test exportpatch to file/dir, where patch already exists, not using overwrite"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir)
            # make sure our output file doesn't exist, then create empty one
            ofile_path.unlink(missing_ok=True)
            ofile_path.touch()
            # now set up path for patch name expected
            ofile_path = ofile_path.with_name(f'{ofile_path.name}-{COMMIT_1F[0:8]}')
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_stdout_defaults(self):
        """Test exportpatch to stdout, using default arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # run the command, saving output to a file in our tmpdir
            (res, pbody, _) = my_run_command(f'{CUT} {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # create a temp file
            tmpfd, tmpname = tempfile.mkstemp(text=True)
            # write out our patch to our temp file
            try:
                with os.fdopen(tmpfd, 'w', encoding='utf-8') as tmpf:
                    tmpf.write(pbody)
                # compare the commit file with a known good one
                res = filecmp.cmp(tmpname, f'{self.ddir}/{PATCH_1F}.known_good')
            finally:
                os.remove(tmpname)
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_in_cwd_defaults(self):
        """Test exportpatch to file/dir, using default arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_using_reference(self):
        """Test exportpatch to file/dir, passing a a reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} -F some-reference {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.some_reference')
            self.assertEqual(res, True, 'patch file differs from known good')


class TestExportpatchExtract(unittest.TestCase):
    """Test extract functionality for 'exportpatch'"""

    def setUp(self):
        """Set up for the tests in this class."""
        self.ddir = find_data_dir_path()
        self.assertTrue(self.ddir, 'cannot find "data" subdirectory')

    def copy_config_from_ddir(self, to_dir):
        """Copy our config file to our data directory."""
        src_path = self.ddir / TEST_CONFIG_SRC
        copy(src_path, Path(to_dir) / 'patch.cfg')

    def test_extract_of_all_1f(self):
        """Test exportpatch that extracts the one file in a patch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} -x {PATCH_FILE_1F} {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.extracted')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_extract_of_all_2f(self):
        """Test exportpatch that extracts the two files in a patch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_2F, dirname=tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} -x {PATCH_FILE_PAT_2F} {COMMIT_2F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_2F}.2f_of_2')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_extract_of_none_1f(self):
        """Test exportpatch that extracts nothing from a patch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_1F, dirname=tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, _, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} -x /bogus/path {COMMIT_1F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertTrue('Skipping' in err_out)
            # no patch file to compare

    def test_extract_of_none_2f(self):
        """Test exportpatch that extracts nothing from a patch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_2F, dirname=tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, _, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} -x /bogus/path {COMMIT_2F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertTrue('Skipping' in err_out)
            # no patch file to compare

    def test_extract_of_one_2f(self):
        """Test exportpatch that extracts one file of two"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            self.copy_config_from_ddir(tmpdir)
            # get name we expect for our patch
            ofile_path = get_patch_path(PATCH_2F, dirname=tmpdir)
            # make sure our output file doesn't exist (even though its a temp dir)
            ofile_path.unlink(missing_ok=True)
            # run the command, saving output to a file in our tmpdir
            (res, pname, _) = my_run_command(f'{CUT} -w -d {tmpdir} -x {PATCH_FILE_FIRST_2F} {COMMIT_2F}', cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_2F}.extracted_1f_of_2')
            self.assertEqual(res, True, 'patch file differs from known good')


class TestExportpatchExclude(unittest.TestCase):
    """Test exclude functionality for 'exportpatch'"""

    def setUp(self):
        """Set up for the tests in this class."""
        self.ddir = find_data_dir_path()
        self.assertTrue(self.ddir, 'cannot find "data" subdirectory')

    def copy_config_from_ddir(self, to_dir):
        """Copy our config file to our data directory."""
        src_path = self.ddir / TEST_CONFIG_SRC
        copy(src_path, Path(to_dir) / 'patch.cfg')
