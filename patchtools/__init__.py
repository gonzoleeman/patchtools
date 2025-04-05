# vim: sw=4 ts=4 et si:
#
"""patch class"""

from . import config

__version__ = '1.2'

class PatchException(Exception):            # noqa: N818
    """Handle exception for the patchtools package"""

config = config.Config()
