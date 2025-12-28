"""The test suite for the patchtools exportpatch command.

Test using the locally available 'exportpatch' command, and its
libraries. Assume the local config files are correct."""

import filecmp
import os
import tempfile
import unittest
from pathlib import Path
from subprocess import run


def my_run_command(command, our_input=None, cwd=None):
    """Run the specified command."""
    proc = run(command.split(), encoding='utf-8', check=False, cwd=cwd,
               input=our_input, capture_output=True, shell=False)
    return (proc.returncode, proc.stdout, proc.stderr)


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
    for data_pathname in ['data', 'test/data', '../data', '../test/data']:
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


def create_config_file(dest_dir):
    """Create a minimal config file, for testing.

    Return (success/failure, error_msg/filename)."""
    (ok, git_repo_reply) = get_git_repo_dir()
    if not ok:
        return (False, git_repo_reply)
    configp = Path(dest_dir) / 'patch.cfg'
    with configp.open('w', encoding='utf-8') as configf:
        for aline in PATCH_CFG_TEMPLATE:
            if '@PATHNAME@' in aline:
                print(aline.replace('@PATHNAME@', git_repo_reply), file=configf)
            else:
                print(aline, file=configf)
    return (True, configp)


# the command under test
CUT = 'exportpatch'

# our testing config file
TEST_CONFIG_SRC = 'patch.cfg.for_testing'

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


class TestExportpatchNormalFunctionality(unittest.TestCase):
    """Test normal functionality for 'exportpatch'."""

    def setUp(self):
        """Set up for the tests in this class."""
        self.ddir = find_data_dir_path()
        self.assertTrue(self.ddir, 'cannot find "data" subdirectory')
        filecmp.clear_cache()

    def test_to_file_in_dir_defaults_1f(self):
        """Test exportpatch of one file to file/dir, using defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} {COMMIT_1F}',
                                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_in_dir_defaults_mf(self):
        """Test exportpatch of multiple files to file/dir, using defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} {COMMIT_MF}',
                                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_MF}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_suffix(self):
        """Test exportpatch to file/dir, with a suffix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir, suffix='.patch')
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = my_run_command(f'{CUT} -w -s -d {tmpdir} {COMMIT_1F}',
                                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_numeric_default(self):
        """Test exportpatch to file/dir, with numeric filename, using default start."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir, prefix='0001-')
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} -n {COMMIT_1F}',
                                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_numeric_s2(self):
        """Test exportpatch to file/dir, with numeric filename, using start number 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir, prefix='0002-')
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} -n -N 2 {COMMIT_1F}',
                                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_numeric_w3(self):
        """Test exportpatch to file/dir, with numeric filename, using width of 3."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir, prefix='001-')
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = \
                    my_run_command(f'{CUT} -w -d {tmpdir} -n --num-width 3 {COMMIT_1F}',
                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_overwrite_force(self):
        """Test exportpatch to file/dir, where patch already exists, using overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch, and ensure we have a a file there
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            ofile_path.touch()
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} -f {COMMIT_1F}',
                                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_overwrite_no_force(self):
        """Test exportpatch to file/dir, where patch already exists, not using overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch, and ensure we have a a file there
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            ofile_path.touch()
            # now set up path for patch name expected
            ofile_path = ofile_path.with_name(f'{ofile_path.name}-{COMMIT_1F[0:8]}')
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} {COMMIT_1F}',
                                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_stdout_defaults(self):
        """Test exportpatch to stdout, using default arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # run the command from tmpdir, saving stdout from the command
            (res, pbody, err_out) = my_run_command(f'{CUT} {COMMIT_1F}',
                                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
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
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = my_run_command(f'{CUT} -w {COMMIT_1F}',
                                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.known_good')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_to_file_using_reference(self):
        """Test exportpatch to file/dir, passing a a reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = \
                    my_run_command(f'{CUT} -w -d {tmpdir} -F some-reference {COMMIT_1F}',
                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.some_reference')
            self.assertEqual(res, True, 'patch file differs from known good')


class TestExportpatchExtract(unittest.TestCase):
    """Test extract functionality for 'exportpatch'."""

    def setUp(self):
        """Set up for the tests in this class."""
        self.ddir = find_data_dir_path()
        self.assertTrue(self.ddir, 'cannot find "data" subdirectory')
        filecmp.clear_cache()

    def test_extract_of_all_1f(self):
        """Test exportpatch that extracts the one file in a patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = \
                    my_run_command(f'{CUT} -w -d {tmpdir} -x {PATCH_FILE_1F} {COMMIT_1F}',
                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.extracted')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_extract_of_all_mf_pat(self):
        """Test exportpatch that extracts all files in a patch using a pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = \
                    my_run_command(f'{CUT} -w -d {tmpdir} -x {PATCH_FILE_PAT_MF} {COMMIT_MF}',
                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_MF}.2f_of_2')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_extract_of_all_mf_multiple_opts(self):
        """Test exportpatch that extracts all files in a patch using multiple options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            # run the command from tmpdir, saving output to a file there
            cmd_str = f'{CUT} -w -d {tmpdir}'
            for a_file in PATCH_FILES_MF:
                cmd_str += f' -x {a_file}'
            cmd_str += f' {COMMIT_MF}'
            (res, pname, err_out) = my_run_command(cmd_str, cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_MF}.2f_of_2')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_extract_of_none_1f(self):
        """Test exportpatch that extracts nothing from a patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # run the command from tmpdir, saving output to a file there
            (res, _, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} -x /bogus/path {COMMIT_1F}',
                                               cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_extract_of_none_mf(self):
        """Test exportpatch that extracts nothing from a patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # run the command from tmpdir
            (res, _, err_out) = my_run_command(f'{CUT} -w -d {tmpdir} -x /bogus/path {COMMIT_MF}',
                                               cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_extract_of_one_mf(self):
        """Test exportpatch that extracts one file of two."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            # run the command from tmpdir, saving output to a file there
            (res, pname, err_out) = \
                    my_run_command(f'{CUT} -w -d {tmpdir} -x {PATCH_FILES_MF[1]} {COMMIT_MF}',
                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_MF}.extracted_file2_of_3')
            self.assertEqual(res, True, 'patch file differs from known good')


class TestExportpatchExclude(unittest.TestCase):
    """Test exclude functionality for 'exportpatch'."""

    def setUp(self):
        """Set up for the tests in this class."""
        self.ddir = find_data_dir_path()
        self.assertTrue(self.ddir, 'cannot find "data" subdirectory')
        filecmp.clear_cache()

    def test_exclude_of_all_1f(self):
        """Test exportpatch that excludes the only file in a single-file patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # run the command from tmpdir
            (res, _, err_out) = \
                    my_run_command(f'{CUT} -w -d {tmpdir} -X {PATCH_FILE_1F} {COMMIT_1F}',
                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_exlude_of_all_mf_pat(self):
        """Test exportpatch that excludes all files in a patch using a pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # run the command from tmpdir
            (res, _, err_out) = \
                    my_run_command(f'{CUT} -w -d {tmpdir} -X {PATCH_FILE_PAT_MF} {COMMIT_MF}',
                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_exlude_of_all_mf_multiple_opts(self):
        """Test exportpatch that excludes all files with multiple options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # run the command from tmpdir, saving output to a file there
            cmd_str = f'{CUT} -w -d {tmpdir}'
            for a_file in PATCH_FILES_MF:
                cmd_str += f' -X {a_file}'
            cmd_str += f' {COMMIT_MF}'
            (res, _, err_out) = my_run_command(cmd_str, cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure we got an error message saying the patch was skipped
            self.assertTrue('Skipping' in err_out)

    def test_exclude_of_none_1f(self):
        """Test exportpatch exclude of nothing for 1 file patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_1F, dirname=tmpdir)
            # run the command from tmpdir
            (res, pname, err_out) = \
                    my_run_command(f'{CUT} -w -d {tmpdir} -X /abc/def {COMMIT_1F}',
                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            # (extracted and excluded -> same file)
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_1F}.extracted')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_exclude_of_none_mf(self):
        """Test exportpatch exclude of nothing for mutliple file patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            # run the command from tmpdir
            (res, pname, err_out) = \
                    my_run_command(f'{CUT} -w -d {tmpdir} -X /abc/def {COMMIT_MF}',
                                   cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            # (extracted and excluded -> same file)
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_MF}.extracted')
            self.assertEqual(res, True, 'patch file differs from known good')

    def test_exclude_2f_of_multiple(self):
        """Test exportpatch exclude 2 files of multiple files in a patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # set up our config file
            (ok, config_create_reply) = create_config_file(tmpdir)
            self.assertTrue(ok, config_create_reply)
            # get name we expect for our patch
            ofile_path = get_patch_path_no_exist(PATCH_MF, dirname=tmpdir)
            # run the command from tmpdir
            cmd_str = f'{CUT} -w -d {tmpdir}'
            cmd_str += f' -X {PATCH_FILES_MF[0]}'
            cmd_str += f' -X {PATCH_FILES_MF[-1]}'
            cmd_str += f' {COMMIT_MF}'
            (res, pname, err_out) = my_run_command(cmd_str, cwd=tmpdir)
            # ensure command succeeded
            self.assertEqual(res, 0, f'running {CUT} failed: {err_out}')
            # ensure name returned is the same
            self.assertEqual(pname.strip(), ofile_path.name, 'patch name wrong')
            # compare the commit file with a known good one
            res = filecmp.cmp(ofile_path, f'{self.ddir}/{PATCH_MF}.excluded_first_and_last')
            self.assertEqual(res, True, 'patch file differs from known good')
