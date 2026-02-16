"""
Fix an existing patch with the proper tags.

Take an existing patch and add the appropriate tags, drawing from known
repositories to discover the origin. Also, renames the patch using the
subject found in the patch itself.
"""

__author__ = 'Jeff Mahoney'


import sys
from pathlib import Path

from patchtools.modified_argparse import ArgumentParsingError, ModifiedArgumentParser
from patchtools.patch import Patch
from patchtools.patcherror import PatchError
from patchtools.version import __version__


def fix_patchfile(pathname, options):
    """Fix one patchfile. Return 0 for success."""
    try:
        p = Patch(debug=options.debug)
        with Path(pathname).open('r', encoding='utf-8') as f:
            p.from_email(f.read())

        if options.name_only:
            suffix = '.patch' if options.suffix else ''
            fn = p.get_pathname()
            print(f'{fn}{suffix}')
            return 0

        if options.update_only:
            options.header_only = True
            options.no_rename = True

        if options.header_only:
            options.no_ack = True
            options.no_diffstat = True
            if options.reference:
                print('References will not be updated in header-only mode.',
                      file=sys.stderr)
                options.reference = None

        if not options.no_diffstat:
            p.add_diffstat()
        if not options.no_ack:
            p.add_signature(options.signed_off_by)

        if options.reference:
            p.add_references(options.reference)

        if options.mainline:
            p.add_mainline(options.mainline)

        if options.dry_run:
            print(p.message.as_string(unixfrom=False))
            return 0

        suffix = '.patch' if options.suffix else ''

        if options.no_rename:
            fn = pathname
        else:
            fn = f'{p.get_pathname()}{suffix}'
            dirname = Path(pathname).parent
            if dirname:
                fn = f'{dirname}/{fn}'
            if fn != pathname and Path(fn).exists() and not options.force:
                print(f'{fn} already exists.', file=sys.stderr)
                return 1

        print(fn)
        with Path(fn).open('w', encoding='utf-8') as f:
            print(p.message.as_string(unixfrom=False), file=f)
        if fn != pathname:
            Path(pathname).unlink()

    except (FileNotFoundError, PermissionError, PatchError) as e:
        print(e, file=sys.stderr)
        return 1

    return 0


def main():
    """The main entry point for this module. Return 0 for success."""
    parser = ModifiedArgumentParser(
                description='fix patch files with proper headers')
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('-n', '--dry-run', action='store_true', default=False,
                        help='Output results to stdout but do not commit change')
    parser.add_argument('-N', '--no-ack', action='store_true', default=False,
                        help='Do not add Acked-by tag (will add by default)')
    parser.add_argument('-D', '--no-diffstat', action='store_true', default=False,
                        help='Do not add the diffstat to the patch')
    parser.add_argument('-r', '--no-rename', action='store_true', default=False,
                        help='Do not rename the patch')
    parser.add_argument('-f', '--force', action='store_true', default=False,
                        help='Overwrite patch if it exists already')
    parser.add_argument('-H', '--header-only', action='store_true', default=False,
                        help='Only update patch headers, do not do Acked-by, diffstat, or add references')
    parser.add_argument('-U', '--update-only', action='store_true', default=False,
                        help='Update the patch headers but do not rename (-Hr)')
    parser.add_argument('-R', '--name-only', action='store_true', default=False,
                        help='Print the new filename for the patch but do not change anything')
    parser.add_argument('-F', '--reference', action='append', default=None,
                        help=(
                            'Add reference tag, if not in header-only mode. '
                            'Can be supplied multiple times.'
                            )
                        )
    parser.add_argument('-S', '--signed-off-by', action='store_true', default=False,
                        help='Use Signed-off-by instead of Acked-by')
    parser.add_argument('-M', '--mainline', action='append', default=None,
                        help=(
                            'Add Patch-mainline tag. Replaces existing tag if any. '
                            'Can be supplied multiple times.'
                            )
                        )
    parser.add_argument('-s', '--suffix', action='store_true',
                        help='When generating the patch name, append ".patch" suffix to filenames.',
                        default=False)
    parser.add_argument('-d', '--debug', action='store_true',
                        help='set debug mode', default=False)
    parser.add_argument('pathname', nargs='+', action='extend',
                        help='One or more patch to be fixed.')

    try:
        args = parser.parse_args()

    except ArgumentParsingError as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1

    for pathname in args.pathname:
        res = fix_patchfile(pathname, args)
        if res:
            return res

    return 0

# vim: sw=4 ts=4 et si:
