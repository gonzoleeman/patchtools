"""
Represent Git Repos.
"""

import configparser
import os
import pwd
import site
from pathlib import Path

from patchtools.command import run_command
from patchtools.patchops import get_git_repo_url

MAINLINE_URLS = [ """git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux-2.6.git""",
                  """git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git""",
                  """https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git""",
                  """https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux.git"""
                ]


def get_git_config(gitdir, var):
    """Return a git configuration variable for the specified repo."""
    res = run_command(f'git config {var}', cwd=gitdir)
    return res.strip()


# We deliberately don't catch exceptions when the option is mandatory
class Config:
    """The Configuration class, built from config files."""
    def __init__(self):
        # Set some sane defaults
        self.repos = [Path.cwd()]
        self.mainline_repos = MAINLINE_URLS
        self.merge_mainline_repos()
        self.email = get_git_config(Path.cwd(), 'user.email')
        self.emails = [self.email]
        self.name = pwd.getpwuid(os.getuid()).pw_gecos.split(',')[0].strip()

        self.read_configs()
        self.merge_mainline_repos()

    def read_configs(self):
        """Return the configuraiton file(s)."""
        our_config = configparser.ConfigParser()
        our_config.read(['/etc/patch.cfg',
                         f'{site.USER_BASE}/etc/patch.cfg',
                         Path('~/.patch.cfg').expanduser(),
                         './patch.cfg'])
        try:
            self.repos = our_config.get('repositories', 'search').split()
            repos = our_config.get('repositories', 'mainline').split()
            self.mainline_repos += repos
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass

        try:
            self.name = our_config.get('contact', 'name')
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass

        try:
            self.emails = our_config.get('contact', 'email').split()
            self.email = self.emails[0]
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass

    def merge_mainline_repos(self):
        """Merge repos found in our list into the mainline list, if appropriate."""
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
        return [self._canonicalize(r) for r in self.repos]


    def get_mainline_repos(self):
        """Return a cannonicalized list of the mainline repos."""
        return [self._canonicalize(r) for r in self.mainline_repos]


# vim: sw=4 ts=4 et si:
