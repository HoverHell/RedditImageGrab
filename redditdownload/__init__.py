from redditdownload import *


def running_python2():
    from platform import python_version_tuple
    return int(python_version_tuple()[0]) == 2
