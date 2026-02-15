"""
Support package for doing SUSE Patch operations.
"""

import re

from patchtools.command import run_command
from patchtools.patcherror import PatchError


def key_version(tag):
    """Return the version nuber the the supplied tag."""
    m = re.match(r"v2\.(\d+)\.(\d+)(\.(\d+)|-rc(\d+)|)", tag)
    if m:
        major = 2
        minor = int(m.group(1))
        patch = int(m.group(2))
        if m.group(5):
            return (major, minor, patch, False, int(m.group(5)))
        else:
            mgroup4=int(m.group(4)) if m.group(4) else 0
            return (major, minor, patch, True, mgroup4)

    # We purposely ignore x.y.z tags since those are from -stable and
    # will never be used in a mainline tag.
    m = re.match(r"v(\d+)\.(\d+)(-rc(\d+)|)", tag)
    if m:
        major = int(m.group(1))
        minor = int(m.group(2))
        if m.group(4):
                return (major, minor, 0, False, int(m.group(4)))
        return (major, minor, 0, True, "")

    return ()


class LocalCommitError(PatchError):
    """Local commit Error."""


def get_tag(commit, repo):
    """Get the git tag for the specified commit."""
    # XXX will the refs/tags/v* wildcard work without using a shell?
    tag = run_command(f"git name-rev --refs=refs/tags/v* {commit}", cwd=repo)
    if not tag:
        return None

    m = re.search(r"tags/([a-zA-Z0-9\.-]+)\~?\S*$", tag)
    if m:
        return m.group(1)
    m = re.search(r"(undefined)", tag)
    if m:
        return m.group(1)
    return None

def get_next_tag(repo):
    """Get the next tag."""
    tag = run_command(f"git tag -l 'v[0-9]*'", cwd=repo)
    if not tag:
        return None

    lines = tag.split()
    lines.sort(key=key_version)
    lasttag = lines[len(lines) - 1]

    m = re.search(r"v([0-9]+)\.([0-9]+)(|-rc([0-9]+))$", lasttag)
    if m:
        # Post-release commit with no rc, it'll be rc1
        if not m.group(3):
            nexttag = "v%s.%d-rc1" % (m.group(1), int(m.group(2)) + 1)
        else:
            nexttag = "v%s.%d or v%s.%s-rc%d (next release)" % \
                      (m.group(1), int(m.group(2)), m.group(1),
                       m.group(2), int(m.group(4)) + 1)
        return nexttag

    return None

def get_diffstat(message):
    """Return output of the diffstat command for our message."""
    return run_command("diffstat -p1", our_input=message)

def get_git_repo_url(repo):
    """Return the remote git repo URL."""
    output = run_command(f"git remote show origin -n", cwd=repo)
    for line in output.split('\n'):
        m = re.search(r"URL:\s+(\S+)", line)
        if m:
            return m.group(1)
    return None

def confirm_commit(commit, repo):
    """Return whether or not the specified commit is in the specified repo."""
    head_name = run_command(f"git symbolic-ref --short HEAD", cwd=repo)
    remote_name = run_command(f"git config --get branch.{head_name}.remote",
                              cwd=repo)
    out = run_command(f"git rev-list HEAD --not --remotes {remote_name}",
                      cwd=repo)
    if not out:
        return True

    commits = out.split()
    if commit in commits:
        return False
    return True

def canonicalize_commit(commit, repo):
    """Return git's cannonicalization of the specified commit."""
    return run_command(f"git show -s {commit}^{{}} --pretty=%H", cwd=repo)

def get_commit(commit, repo, force=False):
    """Return git's idea of the specified commit."""
    data = run_command(f"git diff-tree --no-renames --pretty=email -r -p --cc --stat {commit}",
                       cwd=repo)
    if not data:
        return None

    if not force and not confirm_commit(commit, repo):
        raise LocalCommitError("Commit is not in the remote repository. Use -f to override.")

    return data

def safe_filename(name, keep_non_patch_brackets = True):
    """Return 'safe' version of the patch's filename."""
    if name is None:
        return name

    # These mimic the filters that git-am applies when it parses the email
    # to remove noise from the subject line.
    # keep_non_patch_brackets=True is the equivalent of git am -b
    if keep_non_patch_brackets:
        name = re.sub(r'(([Rr][Ee]:|\[PATCH[^]]*\])[ \t]*)*', '', name, count=1)
    else:
        name = re.sub(r'(([Rr][Ee]:|\[[^]]*\])[ \t]*)*', '', name, count=1)

    # This mimics the filters that git-format-patch applies prior to adding
    # prefixes or suffixes.
    name = re.sub(r'[^_A-Z0-9a-z\.]', '-', name)
    name = re.sub(r'-+', '-', name)
    name = re.sub(r'\.+', '.', name)
    return name.strip('-. ')

# vim: sw=4 ts=4 et si:
