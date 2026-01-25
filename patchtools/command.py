"""
Run a command.
"""

from subprocess import PIPE, run


def run_command(command, our_input=None, stdout=PIPE):
    """Run a command, with optional input and output supplied."""
    proc = run(command, shell=True, encoding='utf-8',
               input=our_input, stdout=stdout)
    return proc.stdout
