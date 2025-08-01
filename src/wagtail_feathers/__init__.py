from .version import get_version


# release must be one of alpha, beta, rc, or final
VERSION = (1, 0, 0, "beta", 5)

__version__ = get_version(VERSION)