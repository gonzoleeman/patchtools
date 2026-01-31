"""
Support package for doing SUSE Patch operations
"""

import email.parser
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from patchtools import patchops
from patchtools.config import config
from patchtools.patcherror import PatchError

_PATCH_START_RE = re.compile(r'^(---|\*\*\*|Index:)[ \t][^ \t]|^diff -|^index [0-9a-f]{7}')


class InvalidCommitIDError(PatchError):
    """An invalid Commit ID Error."""


class InvalidPatchError(PatchError):
    """An invalid Patch Error."""


class InvalidURLError(PatchError):
    """An invalid URL Error."""


class EmptyCommitError(PatchError):
    """An empty commit Error."""


class Patch:
    """The 'Patch' class, representing one patch."""
    def __init__(self, commit=None, debug=False, force=False):
        """Initialize the Patch class, setting defaults."""
        self.commit = commit
        self.debug = debug
        self.force = force
        self.repo = None
        self.repourl = None
        self.message = None
        self.repo_list = config.get_repos()
        self.mainline_repo_list = config.get_mainline_repos()
        self.in_mainline = False
        if self.debug:
            print('DEBUG: repo_list:', self.repo_list)

        if commit and (re.search(r'\^', commit) or r'HEAD' in commit):
            raise InvalidCommitIDError('Commit IDs must be hashes, not relative references. '
                                       'HEAD and ^ are not allowed.')

    def add_diffstat(self):
        """Add a diffstat to the Patch."""
        for line in self.message.get_payload().splitlines():
            if re.search(r'[0-9]+ files? changed, [0-9]+ insertion', line):
                return

        diffstat = patchops.get_diffstat(self.body())
        switched = False
        need_sep = True

        for line in self.header().splitlines():
            if re.match(r'^---$', line) and not switched:
                need_sep = False

        diffstat = '---\n' + diffstat if need_sep else '\n' + diffstat
        diffstat += '\n'

        header = self.header().rstrip() + '\n'
        self.message.set_payload(header + diffstat + self.body())

    def update_diffstat(self):
        """Remove and replace the diffstat in a Patch."""
        text = ''
        eat = ''
        for line in self.header().splitlines():
            if re.search(r'#? .* \| ', line):
                eat = eat + line + '\n'
                continue
            if re.match(r'#? .* files? changed(, .* insertions?\(\+\))?(, .* deletions?\(-\))?', line):
                eat = ''
                continue
            text += eat + line + '\n'
            eat = ''

        self.message.set_payload(text + '\n' + self.body())
        self.add_diffstat()

    def add_references(self, newrefs):
        """Add a References tag to the Patch."""
        if 'References' in self.message:
            refs = self.message['References'].split()
            for ref in refs:
                if ref in newrefs:
                    newrefs.remove(ref)

            refs += newrefs
            refs.sort()
            self.message.replace_header('References', ' '.join(refs))
        else:
            newrefs.sort()
            self.message.add_header('References', ' '.join(newrefs))

    def add_signature(self, sob=False):
        """Add a signature tag to the Patch."""
        for line in self.message.get_payload().splitlines():
            for an_email in config.emails:
                if re.search(rf'Acked-by.*{an_email}', line) or \
                   re.search(rf'Signed-off-by.*{an_email}', line):
                    return

        text = ''
        last = ''
        for line in self.message.get_payload().splitlines():
            if re.match(r'^---$', line):
                text = text.rstrip() + '\n'

                # If this is the first *-by tag, separate it
                if r'-by: ' not in last:
                    text += '\n'
                tag = 'Signed-off-by' if sob else 'Acked-by'
                text += f'{tag}: {config.name} <{config.email}>\n'
            text += line + '\n'
            last = line

        self.message.set_payload(text)

    def add_mainline(self, tag):
        """Add or create a 'Patch-mainline' header, with 'tag'."""
        if 'Patch-mainline' in self.message:
            self.message.replace_header('Patch-mainline', ' '.join(tag))
        else:
            self.message.add_header('Patch-mainline', ' '.join(tag))

    def from_email(self, msg):
        """Set up our Patch state from an email file."""
        p = email.parser.Parser()
        self.message = p.parsestr(msg)

        if 'Git-commit' in self.message:
            self.commit = self.message['Git-commit']

        msg_from = self.message.get_unixfrom()
        if msg_from is not None:
            m = re.match(r'From (\S{40})', msg_from)
            if m:
                msg_commit = m.group(1)
                if not self.commit or \
                   re.match(rf'^{self.commit}.*', msg_commit) is not None:
                    self.commit = msg_commit
                self.find_repo()

        if not self.repo:
            self.find_repo()

        if self.repo in self.mainline_repo_list:
            self.in_mainline = True
        elif self.repo and not self.message['Git-repo']:
            r = self.repourl
            if not r:
                r = patchops.get_git_repo_url(self.repo)
            if r and r not in self.mainline_repo_list:
                self.message.add_header('Git-repo', r)
                self.repourl = r

        if self.commit and not self.message['Git-commit']:
            self.message.add_header('Git-commit', self.commit)

        if self.in_mainline:
            tag = patchops.get_tag(self.commit, self.repo)
            if tag and tag == 'undefined':
                tag = patchops.get_next_tag(self.repo)
            if tag:
                if 'Patch-mainline' in self.message:
                    self.message.replace_header('Patch-mainline', tag)
                else:
                    self.message.add_header('Patch-mainline', tag)
        elif self.message['Git-commit'] and self.repourl and \
              re.search(r'git.kernel.org', self.repourl):
            if 'Patch-mainline' in self.message:
                self.message.replace_header('Patch-mainline',
                                            'Queued in subsystem maintainer repo')
            else:
                self.message.add_header('Patch-mainline',
                                        'Queued in subsystem maintainer repo')
        self.handle_merge()

    def from_file(self, pathname):
        """Set up our Patch instance from an email file."""
        with Path(pathname).open('r', encoding='utf-8') as f:
            self.from_email(f.read())

    def files(self):
        """
        Return a list of files from the diffstat.

        XXX: seems to always return a list of one file
        """
        diffstat = patchops.get_diffstat(self.body())
        f = []
        for line in diffstat.splitlines():
            m = re.search(r'#? (\S+) \| ', line)
            if m:
                f.append(m.group(1))
            if not f:
                return None
            return f
        return None

    def find_commit(self):
        """
        Find current commit and repo, and setup our instance from that,
        return True on success.
        """
        for repo in self.repo_list:
            commit = patchops.get_commit(self.commit, repo, self.force)
            if commit is not None:
                self.commit = patchops.canonicalize_commit(self.commit, repo)
                self.repo = repo
                self.from_email(commit)
                return True
        return False

    def parse_commitdiff_header(self):
        """Parse our commit's diff header, and fill in state from that."""
        url = self.message['X-Git-Url']
        url = unquote(url)

        uc = urlparse(url)
        if not uc.scheme:
            raise InvalidURLError(f'X-Git-Url provided but is not a URL ({url})')

        args = dict([x.split('=', 1) for x in uc.query.split(';')])
        if 'p' in args:
            args['p'] = unquote(args['p'])

        if uc.netloc == 'git.kernel.org':
            self.repo = None
            self.repourl = f'git://{uc.netloc}/pub/scm/{args["p"]}'
        # Add more special cases here
        else:
            self.repo = None
            self.repourl = f'{uc.scheme}//{uc.netloc}{uc.path + args["p"]}'
        if args['h'] and not self.commit:
            self.commit = args['h']
        del self.message['X-Git-Url']

    def get_pathname(self, dirname=None, prefix='', suffix='', truncate=64):
        """Get the pathname for Patch."""
        if self.message and self.message['Subject']:
            filename = patchops.safe_filename(self.message['Subject'])
            truncate_chars = truncate - len(filename) - len(prefix + suffix)
            if truncate_chars < 0:
                filename = filename[0:truncate_chars]
            filename = prefix + filename + suffix
            if dirname:
                filename = str(Path(dirname) / filename)
            return filename
        raise InvalidPatchError('Patch contains no Subject line')

    def find_repo(self):
        """
        Find the repo for our Patch, returning True on success.

        XXX: return value ignored.
        """
        if self.message['Git-repo'] or self.in_mainline:
            return True

        if self.message['X-Git-Url']:
            self.parse_commitdiff_header()
            return True

        if self.commit:
            commit = None
            for repo in self.repo_list:
                commit = patchops.get_commit(self.commit, repo, self.force)
                if commit:
                    r = self.repourl
                    if not r:
                        r = patchops.get_git_repo_url(self.repo)
                    if r and r in self.mainline_repo_list:
                        self.in_mainline = True
                    else:
                        self.repo = repo
                    return True

        return False

    def header(self):
        """Return our header as a string (newlines embedded)."""
        in_body = False
        ret = ''
        for line in self.message.get_payload().splitlines():
            if not in_body:
                if _PATCH_START_RE.match(line):
                    in_body = True
                    continue
                ret += line + '\n'
            else:
                break
        return ret

    def body(self):
        """Return the body of Patch as a string (newlines embedded)."""
        in_body = False
        ret = ''
        for line in self.message.get_payload().splitlines():
            if not in_body:
                if _PATCH_START_RE.match(line):
                    in_body = True
                    ret += line + '\n'
            else:
                ret += line + '\n'
        return ret

    @staticmethod
    def file_in_path(filename, paths):
        """Class static function to check for filename in path."""
        if filename in paths:
            return True
        return any(f[-1:] == '/' and f in filename for f in paths)

    @staticmethod
    def shrink_chunk(chunk):
        """Class static function to shrink our patch body."""
        text = ''
        start = -1
        end = -1
        lines = []
        added = 0
        removed = 0
        count = 0
        lines = chunk.splitlines()
        debug = False
        for n, line in enumerate(lines):
            if re.match(r'^-', line):
                if start < 0:
                    start = n - 3  # count this line
                    if start < 0:
                        if debug:
                            print(f'resetting start(1) ({start}, {n})')
                            print('----')
                            print(chunk)
                            print('----')
                        start = 0

                removed += 1
                count = 0
            elif re.match(r'^\+', line):
                if start < 0:
                    start = n - 3  # count this line
                    if start < 0:
                        if debug:
                            print(f'resetting start(2) ({start}, {n})')
                            print('----')
                            print(chunk)
                            print('----')
                        start = 0

                added += 1
                count = 0
            else:
                count += 1
                if start >= 0 > end and (count > 3 or n + 1 == len(lines)):
                    end = n  # count this line
                    if end >= len(lines):
                        if debug:
                            print('Truncating end')
                            print('----')
                            print(chunk)
                            print('----')
                        end = len(lines) - 1

            if start >= 0 and end >= 0:
                diff = end - start
                text += f'@@ -{start+1},{diff-added} +{start+1},{diff-removed} @@\n'
                text += '\n'.join(lines[start:end])
                text += '\n'
                end = -1
                start = -1
                added = 0
                removed = 0

        return text

    def handle_merge(self):
        """Handle a marge of of chunks."""
        chunk = ''
        text = ''

        in_chunk = False
        lines = self.body().splitlines()
        for line in lines:
            if _PATCH_START_RE.match(line):
                if in_chunk:
                    text += Patch.shrink_chunk(chunk)
                    chunk = ''
                else:
                    chunk += line + '\n'
                in_chunk = False
            elif re.match(r'^@@@', line):
                if in_chunk:
                    text += Patch.shrink_chunk(chunk)
                else:
                    text += chunk
                chunk = ''
                in_chunk = True
            elif in_chunk:
                if line[1] == ' ' or line[1] == '+':
                    chunk += line[0:1] + line[2:] + '\n'
            else:
                chunk += line + '\n'

        if in_chunk:
            text += Patch.shrink_chunk(chunk)
        else:
            text += chunk

        self.message.set_payload(self.header() + text)

    def filter(self, files, exclude=False):
        """Filter our Patch files that are excluded."""
        is_empty = False
        body = ''
        chunk = ''
        filename = None
        partial = False

        for line in self.body().splitlines():
            if _PATCH_START_RE.match(line):
                if filename:
                    if exclude ^ Patch.file_in_path(filename, files):
                        body += chunk + '\n'
                    else:
                        partial = True
                    filename = None
                chunk = ''
            chunk += line + '\n'

            m = re.match(r'^\+\+\+ [^/]+/(\S+)', line)
            if m:
                filename = m.group(1)

        if filename and exclude ^ Patch.file_in_path(filename, files):
            body += chunk + '\n'

        self.message.set_payload(self.header() + body)

        if not body:
            is_empty = True

        if partial:
            commit = self.message['Git-commit']
            if '(partial)' not in commit:
                self.message.replace_header('Git-commit',
                                            f'{commit} (partial)')
            filtered_header = ' !'.join(['', *files])[1:] if exclude else ' '.join(files)

            if 'Patch-filtered' in self.message:
                h = self.message['Patch-filtered']
                self.message.replace_header('Patch-filtered',
                                            f'{h} {filtered_header}')
            else:
                self.message['Patch-filtered'] = filtered_header
        self.update_diffstat()

        if is_empty:
            raise EmptyCommitError('commit is empty')

    def update_refs(self, refs):
        """Update the References tag in our message."""
        if 'References' not in self.message:
            self.message.add_header('References', refs)
        else:
            self.message['References'] = refs

# vim: sw=4 ts=4 et si:
