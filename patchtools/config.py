"""
Represent Git Repos
"""

import configparser
import os
import pwd
import re
import site
from pathlib import Path

from patchtools.command import run_command
from patchtools.patchops import NoRepositoryError, git_dir

MAINLINE_URLS = [
        """git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux-2.6.git""",
        """git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git""",
        """https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git""",
        """https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux.git""",
        ]


def get_git_repo_url(gitdir):
    """Return the git remote repo URL, if possible."""
    try:
        gdir = git_dir(gitdir)
    except NoRepositoryError:
        return None
    output = run_command(f'git --git-dir={gdir} remote show origin -n')
    for line in output.split('\n'):
        m = re.search(r'URL:\s+(\S+)', line)
        if m:
            return m.group(1)
    return None

def get_git_config(gitdir, var):
    """Return a configuraton variable for the specified repo."""
    try:
        gdir = git_dir(gitdir)
    except NoRepositoryError:
        return ''
    res = run_command(f'git --git-dir={gdir} config {var}')
    return res.strip()


# We deliberately don't catch exceptions when the option is mandatory
class Config:
    """Configuration class."""
    def __init__(self):
        """Initialize Config class with some defaults."""
        self.repos = [ Path.cwd() ]
        self.mainline_repos = MAINLINE_URLS
        self.merge_mainline_repos()
        self.email = get_git_config(Path.cwd(), 'user.email')
        self.emails = [self.email]
        self.name = pwd.getpwuid(os.getuid()).pw_gecos.split(',')[0].strip()

        self.read_configs()
        self.merge_mainline_repos()

    def read_configs(self):
        """Read the configuration files."""
        parser_config = configparser.ConfigParser()
        parser_config.read(['/etc/patch.cfg',
                            f'{site.USER_BASE}/etc/patch.cfg',
                            Path('~/.patch.cfg').expanduser(),
                            './patch.cfg'])
        try:
            self.repos = parser_config.get('repositories', 'search').split()
            repos = parser_config.get('repositories', 'mainline').split()
            self.mainline_repos += repos
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass

        try:
            self.name = parser_config.get('contact', 'name')
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass

        try:
            self.emails = parser_config.get('contact', 'email').split()
            self.email = self.emails[0]
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass

    def merge_mainline_repos(self):
        """Merge repos found in our repo list into the mainline list, if appropriate."""
        for repo in self.repos:
            url = get_git_repo_url(repo)
            if url in self.mainline_repos:
                self.mainline_repos.append(repo)

    def _canonicalize(self, path):
        """Return the canonicalized pathname."""
        if path[0] == '/':
            return str(Path(path).resolve())
        if path == '.':
            return str(Path.cwd())
        return path

    def get_repos(self):
        """Return a canonicalized list of our repos."""
        return list(self._canonicalize(r) for r in self.repos)

    def get_mainline_repos(self):
        """Return a canonicalized list of the mainline repos."""
        return list(self._canonicalize(r) for r in self.mainline_repos)

    def get_default_mainline_repo(self):
        """Return the first mainline repo."""
        return self._canonicalize(self.mainline_repos[0])


# set up a global config instance
#
# XXX this means the configuration is read when this file is imported,
# but we may wish to delay that, instead waiting until we actually need it?
#
config = Config()

# vim: sw=4 ts=4 et si:
