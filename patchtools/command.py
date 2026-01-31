"""
Run a command.
"""

from pathlib import Path
from subprocess import PIPE, run


def run_command(command, our_input=None, stdout=PIPE, cwd=None):
    """Run a command, with optional input and output supplied."""
    with Path('/dev/null').open('wb') as dn:
        proc = run(command.split(), encoding='utf-8', input=our_input,
                   stdout=stdout, stderr=dn, check=False, cwd=cwd)
    return proc.stdout
