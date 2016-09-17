#!/usr/bin/env python
"""download reddit uploaded image."""
from os import path
from shutil import copyfileobj
import argparse
import sys

import requests


def download(url, filename=None, dl_dir=None, default_ext='.jpg'):
    """download from reddit uploads.

    see :func:`match` which reddit upload format is supported.
    Args:
        url (str): url to be downloaded.
        filename (str): target filename.
        dl_dir (str): download folder to be used when filename is not given.
        default_ext (str): default extension if no extension if given in url.
    """
    # assume filename is not given, filename is invalid or empty.
    default_user_agent = (
        'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Ubuntu Chromium/52.0.2743.116 Chrome/52.0.2743.116 Safari/537.36')
    cookies = {'User-Agent': default_user_agent}
    if not filename:
        filename = None
    # process filename if not given.
    if filename is None:
        basename = path.basename(url).split('?')[0]
        file_ext = default_ext if not path.splitext(basename)[1] else path.splitext(basename)[1]
        basename = path.splitext(basename)[0] + file_ext
        filename = path.join(dl_dir, basename) if dl_dir is not None else basename
    # downlod the url.
    r = requests.get(url, stream=True, cookies=cookies)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            r.raw.decode_content = True
            copyfileobj(r.raw, f)


def match(url):
    """return true or false if url match this module uploader.

    it support following domain:

        - i.redditmedia.com
        - i.reddituploads.com
        - i.redd.it

    Args:
        url (str): url to be matched.
    Returns:
        bool: return True if url match this downloader.
    """
    parts = [
        'i.redditmedia.com',
        'i.reddituploads.com',
        'i.redd.it',
    ]
    for part in parts:
        if part in url:
            return True
    return False


def main(argv=None):
    """
    main func.

    Args:
        argv (list): user input or system input.
    """
    argv = sys.argv if argv is None else argv
    parser = argparse.ArgumentParser(description='Download from reddit upload.')
    parser.add_argument(
        '--match', action='store_true', default=False,
        help='Print True if it match the reddit uploader or False if otherwise.')
    parser.add_argument(
        '--download', action='store_true', default=False,
        help='Download the file.')
    parser.add_argument(
        'url',
        help='Url to be processed.')
    args = parser.parse_args(argv[1:])

    if args.match:
        print(match(args.url))
    elif args.download:
        download(args.url)

if __name__ == "__main__":
    main()  # pragma: no cover
