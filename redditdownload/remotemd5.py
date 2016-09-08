"""Python MD5 of remote file (URL)."""
import hashlib
import optparse
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen


def get_remote_md5_sum(url, max_file_size=100*1024*1024):
    """get remote md5 sum.

    Args:
        url (str): remote url.
        max_file_size(int): the limit for filesize. default to 100mb.

    Returns:
        str: md5 of the remote url.
    """
    remote = urlopen(url)
    hash = hashlib.md5()

    total_read = 0
    while True:
        data = remote.read(4096)
        total_read += 4096

        if not data or total_read > max_file_size:
            break

        hash.update(data)

    return hash.hexdigest()

if __name__ == '__main__':
    opt = optparse.OptionParser()
    opt.add_option('--url', '-u', default='http://www.google.com')

    options, args = opt.parse_args()
    print(get_remote_md5_sum(options.url))
