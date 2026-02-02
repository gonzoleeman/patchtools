import subprocess
import sys


def run_command(command, input=None, stdout=subprocess.PIPE):
    proc = subprocess.run(command, shell=True, encoding='utf-8',
                          input=input, stdout=stdout,
                          stderr=open("/dev/null", "w"))
    return proc.stdout

# vim: sw=4 ts=4 et si:
