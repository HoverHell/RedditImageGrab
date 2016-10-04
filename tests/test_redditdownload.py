#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import (
    getcwd,
    path,
)
from urllib2 import HTTPError
from unittest import TestCase
import unittest
try:  # py3
    from unittest import mock
except ImportError:  # py2
    import mock

import pytest

from redditdownload import (
    download_from_url,
    FileExistsException,
    parse_args,
    process_deviant_url,
    process_imgur_url,
    WrongFileTypeException,
)


class TestParseArgs(TestCase):
    def test_simple_args(self):
        ARGS = parse_args(['funny'])
        self.assertEqual(ARGS.reddit, 'funny')
        self.assertEqual(ARGS.dir, getcwd())

    def test_multiple_reddit_plus(self):
        ARGS = parse_args(['funny+anime'])
        self.assertEqual(ARGS.reddit, 'funny+anime')

    def test_nsfw_sfw_arg(self):
        ARGS = parse_args(['--nsfw --sfw'])
        self.assertFalse(ARGS.nsfw)
        self.assertFalse(ARGS.sfw)


@pytest.mark.online
class TestProcessDeviantUrl(TestCase):
    def setUp(self):
        self.url = 'http://shortethan.deviantart.com/art/Bumbleby-Shirts-495533842'
        # actual link is :
        # http://www.deviantart.com/download/495533842/bumbleby_shirts_by_shortethan-d8710cy.png?token=a5c45dc54b928b8a9622203db5142f9b5e1c3e7f&ts=1440638185
        # token may change per request
        self.not_full_download_url = ('http://www.deviantart.com/download/'
                                      '495533842/bumbleby_shirts_by_shortethan-d8710cy.png')

    def test_link_with_download_button(self):
        result_url = process_deviant_url(self.url)
        # result_url is a list, contain one or more pic
        self.assertIsInstance(result_url, list)
        self.assertIn(self.not_full_download_url, result_url[0])
        self.assertGreaterEqual(len(result_url), 1)


@pytest.mark.online
class TestProcessImgurUrl(TestCase):
    def setUp(self):
        self.album_url = 'http://imgur.com/a/WobUS'
        self.album_url_member = 'http://i.imgur.com/qVOLIba.jpg'

        # single url with extension
        self.single_url = 'https://i.imgur.com/XdWGz14.jpg'

    def test_extract_album(self):
        result = process_imgur_url(self.album_url)
        self.assertIsInstance(result, list)
        self.assertIn(self.album_url_member, result)

    def test_extract_single(self):
        result = process_imgur_url(self.single_url)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn(self.single_url, result)

class TestDownloadFromUrl(TestCase):
    """test download_from_url func."""

    def test_empty_mock_input(self):
        """test with empty mock input."""
        with pytest.raises(TypeError):
            download_from_url(mock.Mock(), mock.Mock())

    @mock.patch('redditdownload.redditdownload.pathexists')
    def test_empty_mock_input_with_patched_pathexist(self, mock_pathexists):
        with pytest.raises(FileExistsException):
            download_from_url(mock.Mock(), mock.Mock())

        mock_pathexists.return_value = False

        with pytest.raises(TypeError):
            download_from_url(mock.Mock(), mock.Mock())

    @mock.patch('redditdownload.redditdownload.pathexists')
    def test_imgur_url_with_existing_alt_ext_file(self, mock_pathexists):
        """test imgur.com url when alternative ext file already exist in file."""
        imgur_url = 'https://i.imgur.com/3panxHg.jpg'
        dest_file = '3panxHg.jpg'
        for ext in ['.jpg', '.jpeg']:
            dest_file = path.splitext(path.basename(imgur_url))[0] + ext
            mock_pathexists.side_effect = lambda x: False if x == dest_file else True
            with pytest.raises(FileExistsException):
                download_from_url(imgur_url, dest_file)

    @mock.patch('redditdownload.redditdownload.pathexists')
    def test_unknown_filetype_url(self, mock_pathexists):
        """test url with unknown_filetype."""
        url = 'randomwebsite.com/random_path'
        dest_file = path.basename(url)
        mock_pathexists.return_value = False
        # ValueError raised because random url
        with pytest.raises(ValueError):
            download_from_url(url, dest_file)

        with mock.patch('redditdownload.redditdownload.request') as mock_request:
            with pytest.raises(WrongFileTypeException):
                download_from_url(url, dest_file)
            mock_request.assert_any_call(url)

            call_list = [
                mock.call().info(),
                mock.call().info().keys(),
                # NOTE:dunder not recognized by mock
                # mock.call().info().keys().__contains__('content-type'),
            ]
            for single_call in call_list:
                assert single_call in mock_request.mock_calls

    @mock.patch('redditdownload.redditdownload.request')
    @mock.patch('redditdownload.redditdownload.pathexists')
    def test_working_url(self, mock_pathexists, mock_request):
        """test working url."""
        valid_ext = '.jpg'
        url = 'randomwebsite.com/random_path' + valid_ext
        dest_file = path.basename(url)
        mock_pathexists.return_value = False

        mock_open_target = 'redditdownload.redditdownload.open'
        with mock.patch(mock_open_target, mock.mock_open(), create=True) as dfu_mock_open:
            download_from_url(url, dest_file)
            # test mock_request
            assert mock.call().read() in mock_request.mock_calls
            # test dfu_mock_open
            dfu_mock_open.assert_any_call(dest_file, 'wb')
            assert mock.call().write(mock_request(url).read()) in dfu_mock_open.mock_calls
            assert mock.call().close() in dfu_mock_open.mock_calls

    @mock.patch('redditdownload.redditdownload.request')
    @mock.patch('redditdownload.redditdownload.pathexists')
    def test_removed_imgur(self, mock_pathexists, mock_request):
        """test removed imgur."""
        url = 'http://i.imgur.com/2gUGa.jpg'
        remove_imgurl_url = 'http://i.imgur.com/removed.png'
        dest_file = path.basename(url)
        mock_pathexists.return_value = False
        mock_request.return_value.url = remove_imgurl_url

        with pytest.raises(HTTPError):
            download_from_url(url, dest_file)

if __name__ == '__main__':
    unittest.main()
