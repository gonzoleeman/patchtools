"""
Export a patch from a repository with the SUSE set of patch headers.

From Jeff Mahoney, updated by Lee Duncan.
"""

__author__ = 'Jeff Mahoney'

import sys
from pathlib import Path

from patchtools.modified_argparse import ArgumentParsingError, ModifiedArgumentParser
from patchtools.patch import EmptyCommitError, Patch
from patchtools.patcherror import PatchError
from patchtools.version import __version__

# default: do not write out a patch file
WRITE=False

# default directory where patch gets written
DIR='.'


def export_patch(commit, options, prefix, suffix):
    """Export a single commit/patch. Return 0 for success, else 1."""
    try:
        p = Patch(commit, debug=options.debug, force=options.force)
    except PatchError as e:
        print(e, file=sys.stderr)
        return 1
    if p.find_commit():
        if options.reference:
            p.add_references(options.reference)
        if options.extract:
            try:
                p.filter(options.extract)
            except EmptyCommitError:
                print(f'Commit {commit} is now empty. Skipping.', file=sys.stderr)
                return 0
        if options.exclude:
            try:
                p.filter(options.exclude, True)
            except EmptyCommitError:
                print(f'Commit {commit} is now empty. Skipping.', file=sys.stderr)
                return 0
        p.add_signature(options.signed_off_by)
        if options.write:
            fn = p.get_pathname(options.dir, prefix, suffix)
            if Path(fn).exists() and not options.force:
                f = fn
                fn += f'-{commit[0:8]}'
                print(f'{f} already exists. Using {fn}', file=sys.stderr)
            print(Path(fn).name)
            try:
                with Path(fn).open('w', encoding='utf-8') as f:
                    print(p.message.as_string(False), file=f)
            except OSError as e:
                print(e, file=sys.stderr)
                return 1

        else:
            print(p.message.as_string(False))
        return 0

    print(f'Could not locate commit "{commit}"; Skipping.', file=sys.stderr)
    return 1


def main():
    """The main entry point for this module. Return 0 for success."""
    parser = ModifiedArgumentParser(
                description='Export upstream patch commits(s) with proper patch headers')
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('-w', '--write', action='store_true',
                        help='write patch file(s) instead of stdout [default is %(default)s]',
                        default=WRITE)
    parser.add_argument('-s', '--suffix', action='store_true',
                        help='when used with -w, append .patch suffix to filenames.',
                        default=False)
    parser.add_argument('-n', '--numeric', action='store_true',
                        help='when used with -w, prepend order numbers to filenames.',
                        default=False)
    parser.add_argument('--num-width', type=int, action='store',
                        help='when used with -n, set the width of the order numbers',
                        default=4)
    parser.add_argument('-N', '--first-number', type=int, action='store',
                        help='Start numbering the patches with number instead of 1',
                        default=1)
    parser.add_argument('-d', '--dir', action='store',
                        help='write patch to this directory (default ".")', default=DIR)
    parser.add_argument('-f', '--force', action='store_true',
                        help='write over existing patch or export commit that only exists in local repo',
                        default=False)
    parser.add_argument('-D', '--debug', action='store_true',
                        help='set debug mode', default=False)
    parser.add_argument('-F', '--reference', action='append',
                        help='add reference tag. This option can be specified multiple times.',
                        default=None)
    parser.add_argument('-x', '--extract', action='append',
                        help=(
                            'extract specific parts of the commit; using a path '
                            'that ends with / includes all files under that hierarchy. '
                            'This option can be specified multiple times.'
                            ),
                        default=None)
    parser.add_argument('-X', '--exclude', action='append',
                        help=(
                            'exclude specific parts of the commit; using a path '
                            'that ends with / excludes all files under that hierarchy. '
                            'This option can be specified multiple times.'
                            ),
                        default=None)
    parser.add_argument('-S', '--signed-off-by', action='store_true',
                        help='Use Signed-off-by instead of Acked-by',
                        default=False)
    parser.add_argument('commits', nargs='+', action='extend',
                        help='One or more commits to be exported.')

    try:
        args = parser.parse_args()

    except ArgumentParsingError as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1

    if args.first_number + len(args.commits) > 9999 or \
       args.first_number < 0:
        print('The starting number + commits needs to be in the range 0 - 9999',
              file=sys.stderr)
        return 1

    suffix = '.patch' if args.suffix else ''

    num_width = 4
    if args.num_width:
        n_ = int(args.num_width)
        if 0 < n_ < 5:
            num_width = n_

    n = args.first_number
    for commit in args.commits:
        prefix = f'{n:0{num_width}}-' if args.numeric else ''

        res = export_patch(commit, args, prefix, suffix)
        if res:
            return res

        n += 1

    return 0

# vim: sw=4 ts=4 et si:
