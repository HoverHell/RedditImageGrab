#!/usr/bin/env python
"""module to test redditupload module."""
import os
import tempfile
import unittest

try:
    from unittest.mock import patch, Mock, PropertyMock, ANY as mock_ANY, mock_open
except ImportError:
    from mock import Mock, patch, PropertyMock, ANY as mock_ANY, mock_open

from redditdownload.redditupload import match, download, main


def test_match():
    """test if url match func work against input data."""
    urls = [
        ('https://i.reddituploads.com/9049436b10ee4f95985a9273c2e8dae5'
         '?fit=max&h=1536&w=1536&s=8ffb4f473ee556113844d6542aa5ad29'),
    ]
    invalid_urls = [
        'redditupload.com/23u40238409328402398402384203984032'
    ]

    for url in urls:
        assert match(url)
    for url in invalid_urls:
        assert not match(url)

@patch('redditdownload.redditupload.copyfileobj')
@patch('redditdownload.redditupload.requests.get')
class TestDownloadMethods(unittest.TestCase):
    def setUp(self):
        """set up func."""
        self.url = (
            'https://i.reddituploads.com/9049436b10ee4f95985a9273c2e8dae5'
            '?fit=max&h=1536&w=1536&s=8ffb4f473ee556113844d6542aa5ad29'
        )
        self.url_filename = '9049436b10ee4f95985a9273c2e8dae5.jpg'

    def test_404_response(self, mock_get, mock_copyfileobj):
        """test if download is not working and and 404 status code given."""
        type(mock_get.return_value.raw).decode_content = PropertyMock(return_value=False)
        type(mock_get.return_value).status_code = PropertyMock(return_value=404)

        m = mock_open()
        with patch('redditdownload.redditupload.open', m, create=True):
            download(self.url)

            # check mock open
            assert not m.called
            # check mock_get
            mock_get.assert_called_once_with(self.url, stream=True)
            assert not mock_get.return_value.raw.decode_content
            # check if copyfileobj is not called
            assert not mock_copyfileobj.called

    def test_working_url(self, mock_get, mock_copyfileobj):
        """test when it return 200 status code and file can be downloaded."""
        type(mock_get.return_value).status_code = PropertyMock(return_value=200)
        type(mock_get.return_value.raw).decode_content = False

        m = mock_open()
        with patch('redditdownload.redditupload.open', m, create=True):
            download(self.url)

            # check mock open
            m.assert_called_once_with(self.url_filename, 'wb')
            # check mock_get
            mock_get.assert_called_once_with(self.url, stream=True)
            assert mock_get.return_value.raw.decode_content
            # check if copyfileobj called
            assert mock_copyfileobj.called
            mock_copyfileobj.assert_called_once_with(
                mock_get.return_value.raw, mock_ANY)


@patch('redditdownload.redditupload.match')
@patch('redditdownload.redditupload.download')
def test_main(mock_download, mock_match):
    """test main func."""
    url = 'https://i.reddituploads.com/9049436b10ee4f95985a9273c2e8dae5'
    main('redditupload.py --download {}'.format(url).split(' '))
    mock_download.assert_called_once_with(url)
    assert not mock_match.called

    # reset both mock
    mock_match.reset_mock()
    mock_download.reset_mock()

    main('redditupload.py --match {}'.format(url).split(' '))
    mock_match.assert_called_once_with(url)
    assert not mock_download.called
