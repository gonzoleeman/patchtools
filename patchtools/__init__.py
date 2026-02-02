"""patchtools module initialization."""

import os
from . import config


class PatchException(Exception):
    pass


config = config.Config()

# vim: sw=4 ts=4 et si:
