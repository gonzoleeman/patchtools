"""The test suite for the patchtools exportpatch command.

Test using the locally available 'exportpatch' command, and its
libraries. Assume the local config files are correct."""

import filecmp
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


def call_code_directly(arg_array):
    """Call the code directly, passing in the specified arguments."""
    save_argv = sys.argv
    sys.argv = [MUT, *arg_array]
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
        res = main_under_test()
    sys.argv = save_argv
    return (res, captured_stdout.getvalue(), captured_stderr.getvalue())


def get_patch_path_no_exist(fname, dirname=None, prefix='', suffix='', truncate=64):
    """Return a patch filename that isn't too long, and ensure it does not exist.

    This code is copied in part from patch.py, so we match."""
    truncate_chars = truncate - len(fname) - len(prefix + suffix)
    if truncate_chars < 0:
        fname = fname[0:truncate_chars]
    fpath = Path(prefix + fname + suffix)
    if dirname:
        fpath = Path(dirname) / fpath
    fpath.unlink(missing_ok=True)
    return fpath


def find_data_dir_path():
    """Find the 'data' directory path, if possible.

    This is the directory where known-good patch files
    are kept.

    Look first in the current directory. If not there,
    then look for a 'test' subdirectory, and look there."""
    for data_pathname in ['data', 'test2/data', '../data', '../test2/data']:
        data_path = Path(data_pathname)
        if data_path.is_dir():
            return data_path
    return None


def get_git_repo_dir():
    """Get a valid Linux git repo path.

    Return results as (success/failure, pathname/error_msg).

    For now, get repo path from environment variable LINUX_GIT."""
    linux_git_dir = os.getenv('LINUX_GIT')
    if not linux_git_dir:
        return (False, 'No LINUX_GIT environment variable found')
    if not Path(linux_git_dir).exists():
        return (False, f'LINUX_GIT directory not found: {linux_git_dir}')
    return (True, linux_git_dir)


# template for the patch.cfg file we create
PATCH_CFG_TEMPLATE = [
    '[repositories]',
    'search:',
    '  @PATHNAME@',
    '',
    '[contact]',
    'name: Barney Rubbel',
    'email: brubbel@suse.com',
    ]


def create_config_file():
    """Create a minimal config file, for testing.

    Return (success/failure, error_msg/filename)."""
    (ok, git_repo_reply) = get_git_repo_dir()
    if not ok:
        return None
    cfp = Path('patch.cfg')
    with cfp.open('w', encoding='utf-8') as configf:
        for aline in PATCH_CFG_TEMPLATE:
            if '@PATHNAME@' in aline:
                print(aline.replace('@PATHNAME@', git_repo_reply), file=configf)
            else:
                print(aline, file=configf)
    return cfp


# the module under test
MUT = 'exportpatch'

# commit for one file
COMMIT_1F = '8db816c6f176321e42254badd5c1a8df8bfcfdb4'

# commit for multiple files
COMMIT_MF = '362432e9b9aefb914ab7d9f86c9fc384a6620c41'

# patch name for known commit (no suffix, etc)
PATCH_1F = 'scsi-st-Tighten-the-page-format-heuristics-with-MODE-SELECT'

# patch name for known commit with multiple files
PATCH_MF = 'scsi-libsas-Add-rollback-handling-when-an-error-occurs'

# patchname for the one file in the simple commit
PATCH_FILE_1F = 'drivers/scsi/st.c'

# patch filename pattern for all files in multiple-file commit
PATCH_FILE_PAT_MF = 'drivers/scsi/libsas/'

# patch filenames for the patch with multiple commits
PATCH_FILES_MF = [
    'drivers/scsi/libsas/sas_init.c',
    'drivers/scsi/libsas/sas_internal.h',
    'drivers/scsi/libsas/sas_phy.c',
    ]

# patchname for one file in mulitple-file commit
PATCH_FILE_FIRST_MF = 'drivers/scsi/libsas/sas_internal.h'

# set the data directory
DATA_DIR = find_data_dir_path()

# import or module under test
# we must create a config file before we import patchtools
# or it won't find it. After import, we can delete it.
try:
    configp = create_config_file()
    from patchtools.exportpatch import main as main_under_test
    configp.unlink()
finally:
    pass


class TestExportpatchNormalFunctionality(unittest.TestCase):
    """Test normal functionality for 'exportpatch'."""

    def setUp(self):
        """Set up for the tests in this class."""
        self.assertTrue(DATA_DIR, 'cannot find "data" subdirectory')
        filecmp.clear_cache()

    def test_to_file_in_dir_defaults_1f(self):
        """Test exportpatch of one file to file/dir, using defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            (res, pname, err_out) = call_code_directly(['-w', '-d', tmpdir, COMMIT_1F])
            self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_in_dir_defaults_mf(self):
        """Test exportpatch of multiple files to file/dir, using defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            (res, pname, err_out) = call_code_directly(['-w', '-d', tmpdir, COMMIT_MF])
            self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_MF}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_in_dir_suffix(self):
        """Test exportpatch to file/dir, with a suffix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir, suffix='.patch')
            (res, pname, err_out) = call_code_directly(['-w', '-d', tmpdir, '-s', COMMIT_1F])
            self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_numeric_default(self):
        """Test exportpatch to file/dir, with numeric filename, using default start."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir, prefix='0001-')
            (res, pname, err_out) = call_code_directly(['-w', '-d', tmpdir, '-n', COMMIT_1F])
            self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_numeric_s2(self):
        """Test exportpatch to file/dir, with numeric filename, using start number 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir, prefix='0002-')
            (res, pname, err_out) = call_code_directly(['-w', '-d', tmpdir, '-n', '-N', '2', COMMIT_1F])
            self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_numeric_w3(self):
        """Test exportpatch to file/dir, with numeric filename, using width of 3."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir, prefix='001-')
            (res, pname, err_out) = \
                    call_code_directly(['-w', '-d', tmpdir, '-n', '--num-width', '3', COMMIT_1F])
            self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_overwrite_force(self):
        """Test exportpatch to file/dir, where patch already exists, using overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            patch_name_expected.touch()
            (res, pname, err_out) = call_code_directly(['-w', '-d', tmpdir, '-f', COMMIT_1F])
            self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_overwrite_no_force(self):
        """Test exportpatch to file/dir, where patch already exists, not using overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # create an empty 'patch' file, to creat a collision
            patch_name_orig = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            patch_name_orig.touch()
            # now set up for actual path for patch name expected
            patch_name_expected = patch_name_orig.with_name(f'{patch_name_orig.name}-{COMMIT_1F[0:8]}')
            (res, pname, err_out) = call_code_directly(['-w', '-d', tmpdir, COMMIT_1F])
            self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_stdout_defaults(self):
        """Test exportpatch to stdout, using default arguments."""
        (res, pbody, err_out) = call_code_directly([COMMIT_1F])
        self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
        # create a temp file
        tmpfd, tmpname = tempfile.mkstemp(text=True)
        # write out our patch to our temp file
        try:
            with os.fdopen(tmpfd, 'w', encoding='utf-8') as tmpf:
                tmpf.write(pbody)
            # compare the commit file with a known good one
            res = filecmp.cmp(tmpname, f'{DATA_DIR}/{PATCH_1F}.known_good')
        finally:
            os.remove(tmpname)
        self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_in_cwd_defaults(self):
        """Test exportpatch to file/dir, using default arguments."""
        patch_name_expected = get_patch_path_no_exist(PATCH_1F)
        (res, pname, err_out) = call_code_directly(['-w', COMMIT_1F])
        self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
        self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
        # compare the commit file with a known good one
        res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.known_good')
        self.assertEqual(res, True, 'patch file differs from known good')
        patch_name_expected.unlink()

    def test_to_file_using_reference(self):
        """Test exportpatch to file/dir, passing a a reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            (res, pname, err_out) = \
                    call_code_directly(['-w', '-d', tmpdir, '-F', 'some-reference', COMMIT_1F])
            self.assertEqual(res, 0, f'calling {MUT} returned faliure: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.some_reference')
            self.assertEqual(res, True, 'patch file differs from known good')


class TestExportpatchExtract(unittest.TestCase):
    """Test extract functionality for 'exportpatch'."""

    def setUp(self):
        """Set up for the tests in this class."""
        self.assertTrue(DATA_DIR, 'cannot find "data" subdirectory')
        filecmp.clear_cache()

    def test_extract_of_all_1f(self):
        """Test exportpatch that extracts the one file in a patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            (res, pname, err_out) = \
                    call_code_directly(['-w', '-d', tmpdir, '-x', PATCH_FILE_1F, COMMIT_1F])
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.extracted')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_extract_of_all_mf_pat(self):
        """Test exportpatch that extracts all files in a patch using a pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            (res, pname, err_out) = \
                    call_code_directly(['-w', '-d', tmpdir, '-x', PATCH_FILE_PAT_MF, COMMIT_MF])
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_MF}.2f_of_2')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_extract_of_all_mf_multiple_opts(self):
        """Test exportpatch that extracts all files in a patch using multiple options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            cmd_arr = ['-w', '-d', tmpdir]
            for a_file in PATCH_FILES_MF:
                cmd_arr += ['-x', a_file]
            cmd_arr.append(COMMIT_MF)
            (res, pname, err_out) = call_code_directly(cmd_arr)
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_MF}.2f_of_2')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_extract_of_none_1f(self):
        """Test exportpatch that extracts nothing from a patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (res, _, err_out) = call_code_directly(['-w', '-d', tmpdir, '-x', '/bogus/path', COMMIT_1F])
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_extract_of_none_mf(self):
        """Test exportpatch that extracts nothing from a patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (res, _, err_out) = call_code_directly(['-w', '-d', tmpdir, '-x', '/bogus/path', COMMIT_MF])
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_extract_of_one_mf(self):
        """Test exportpatch that extracts one file of two."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            (res, pname, err_out) = \
                    call_code_directly(['-w', '-d', tmpdir, '-x', PATCH_FILES_MF[1], COMMIT_MF])
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_MF}.extracted_file2_of_3')


class TestExportpatchExclude(unittest.TestCase):
    """Test exclude functionality for 'exportpatch'."""

    def setUp(self):
        """Set up for the tests in this class."""
        self.assertTrue(DATA_DIR, 'cannot find "data" subdirectory')
        filecmp.clear_cache()

    def test_exclude_of_all_1f(self):
        """Test exportpatch that excludes the only file in a single-file patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (res, _, err_out) = \
                    call_code_directly(['-w', '-d', tmpdir, '-X', PATCH_FILE_1F, COMMIT_1F])
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_exlude_of_all_mf_pat(self):
        """Test exportpatch that excludes all files in a patch using a pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (res, _, err_out) = \
                    call_code_directly(['-w', '-d', tmpdir, '-X', PATCH_FILE_PAT_MF, COMMIT_MF])
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_exlude_of_all_mf_multiple_opts(self):
        """Test exportpatch that excludes all files with multiple options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd_arr = ['-w', '-d', tmpdir]
            for a_file in PATCH_FILES_MF:
                cmd_arr += ['-X', a_file]
            cmd_arr.append(COMMIT_MF)
            (res, _, err_out) = call_code_directly(cmd_arr)
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_exclude_of_none_1f(self):
        """Test exportpatch exclude of nothing for 1 file patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            (res, pname, err_out) = \
                    call_code_directly(['-w', '-d', tmpdir, '-X', '/abc/def', COMMIT_1F])
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            # (extracted and excluded -> same file)
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_1F}.extracted')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_exclude_of_none_mf(self):
        """Test exportpatch exclude of nothing for mutliple file patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            (res, pname, err_out) = \
                    call_code_directly(['-w', '-d', tmpdir, '-X', '/abc/def', COMMIT_MF])
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            # (extracted and excluded -> same file)
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_MF}.extracted')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_exclude_2f_of_multiple(self):
        """Test exportpatch exclude 2 files of multiple files in a patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_name_expected = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            cmd_arr = ['-w', '-d', tmpdir]
            cmd_arr += ['-X', PATCH_FILES_MF[0]]
            cmd_arr += ['-X', PATCH_FILES_MF[-1]]
            cmd_arr.append(COMMIT_MF)
            (res, pname, err_out) = call_code_directly(cmd_arr)
            self.assertEqual(res, 0, f'running {MUT} failed: {err_out}')
            self.assertEqual(pname.strip(), patch_name_expected.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(patch_name_expected, f'{DATA_DIR}/{PATCH_MF}.excluded_first_and_last')
            self.assertEqual(res, True, 'patch file differs from known good')
            self.assertEqual(res, True, 'patch file differs from known good')
