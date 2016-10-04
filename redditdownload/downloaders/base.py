# coding: utf8
"""
Base utils for per-site plugins.

Covers most common cases.

NOTE: for future use, it should be possible to wrap exec()-based
downloader commands into this.
"""
from __future__ import print_function

import urlparse
import contextlib


class DownloadError(Exception):
    """ Common point for all errors with downloading """

    def __init__(self, message, context=None):
        super(DownloadError, self).__init__(message)
        self.context = context

    def __repr__(self):
        return '<%s(%r, %r)>' % (
            self.__class__.__name__,
            self.message,
            self.context)


class RetriableEror(DownloadError):
    """ Raiseable error to denote something that might be retriable """


class UnknownError(DownloadError):
    """
    Raiseable error to denote that nothing could be downloaded for an
    unparsed reason.
    """


class DownloaderPlugin(object):

    domains = None

    def __init__(self, context=None):
        self.context = {} if context is None else context

    def match(self, url, **kwargs):
        if self.domains:
            # Common case: match by host.
            url_data = self._parse_url(url)
            return self.match_domains(url_data.hostname, self.domains, **kwargs)
        raise NotImplementedError

    def match_host(self, host, **kwargs):
        raise NotImplementedError

    def download_base(self, url, filename=None):
        raise NotImplementedError

    def download(self, url, filename=None, **kwargs):
        # Common case: wrap known exceptions.
        with self.default_wrap():
            return self.download_base(url, filename=filename, **kwargs)

    @staticmethod
    def match_domains(url_domain, known_domains, include_subdomains=True):
        for known_domain in known_domains:
            if url_domain == known_domain:
                return True
            elif include_subdomains and url_domain.endswith('.{}'.format(known_domain)):
                return True
        return False

    @staticmethod
    def _parse_url(url):
        return urlparse.urlparse(url)

    @staticmethod
    @contextlib.contextmanager
    def default_wrap():
        try:
            yield None
        except Exception as exc:
            print(repr(exc))
            raise
