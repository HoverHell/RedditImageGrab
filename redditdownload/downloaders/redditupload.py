#!/usr/bin/env python
"""
Downloader for reddit-uploaded images.

"""
import os.path
import urlparse
from shutil import copyfileobj
import argparse
import sys
import requests
from redditupload.downloaders.base import DownloaderPlugin, UnknownError


DOMAINS = (
    'i.redditmedia.com',
    'i.reddituploads.com',
    'i.redd.it',
)


def download(url, filename=None, dl_dir=None, default_ext='.jpg'):
    """
    Download from reddit uploads.

    :param url: (str) url to be downloaded.
    :param filename: (str) target filename.
    :param dl_dir: (str) download folder to be used when filename is not given.
    :param default_ext: (str) default extension if no extension if given in url.
    """
    # assume filename is not given, filename is invalid or empty.
    default_user_agent = (
        'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Ubuntu Chromium/52.0.2743.116 Chrome/52.0.2743.116 Safari/537.36')
    cookies = {'User-Agent': default_user_agent}
    # generate filename if not specified.
    if not filename:
        url_parts = urlparse.urlparse(url)
        filename = url_parts.path.rsplit('/', 1)[-1]
        if '.' not in filename:
            filename = '{}{}'.format(filename, default_ext)
        if dl_dir:
            filename = os.path.joindl_dir, basename)
    # downlod the url.
    resp = requests.get(url, stream=True, cookies=cookies)
    if resp.status_code == 200:
        with open(filename, 'wb') as fobj:
            # XXXX: probably should not be needed:
            # `If True, attempts to decode specific content-encoding's based on headers
            #  (like 'gzip' and 'deflate') will be skipped and raw data will be used
            #  instead.`
            resp.raw.decode_content = True
            # ...
            copyfileobj(resp.raw, fobj)
        return
    else:
        raise UnknownError("Unexpected response status", dict(status=resp.status_code, resp=resp))


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
    parts = DOMAINS
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


class Plugin(DownloaderPlugin):

    domains = DOMAINS

    def download_base(self, url, filename=None):
        return download(url, filename=filename)


if __name__ == "__main__":
    main()  # pragma: no cover
