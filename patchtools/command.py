"""Handle running a command"""


import subprocess


def run_command(command, stdin=None, command_input=None, stdout=subprocess.PIPE):
    with open('/dev/null') as dn:
        proc = subprocess.run(command, encoding='utf-8', check=False, shell=True,
                              stdin=stdin, input=command_input, stdout=stdout,
                              stderr=dn)
    return proc.stdout
