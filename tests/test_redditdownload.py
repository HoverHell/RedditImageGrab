#!/usr/bin/env python
"""test redditdownload module."""
import json
import os
import sys
import unittest


import pytest
try:  # py3
    from mock import patch, MagicMock
except ImportError:  # py2
    from unittest import mock

from redditdownload import redditdownload

FILE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files')


def get_mock_items():
    """get mock items."""
    items_json_path = os.path.join(FILE_FOLDER, 'items.json')
    with open(items_json_path) as ff:
        mock_items = json.load(ff)
    return mock_items


class TestMainMethod(unittest.TestCase):
    """test the main function of redditdownload module."""

    def test_no_input(self):
        """test no input when main func called.

        program will exit for this case.
        """
        with pytest.raises(SystemExit):
            redditdownload.main()

    @patch('redditdownload.redditdownload.download_from_url')
    @patch('redditdownload.redditdownload.getitems', side_effect=[get_mock_items(),{}])
    def test_update_flag(self, mock_get_items, mock_download_func):
        """test update flag."""
        mock_argv = patch.object(
            sys, 'argv', ['redditdl.py', 'cats', '--num', '2', '--update']
        )
        #start patch
        mock_argv.start()
        # run the main function.
        redditdownload.main()

        # assert the call count
        assert mock_get_items.call_count == 1
        assert mock_download_func.call_count == 2

        # change side effect to raise error
        err_txt = 'Expected Error on testing'
        mock_download_func.side_effect = redditdownload.FileExistsException(err_txt)
        # run the main func.
        redditdownload.main()

        # assert the call count
        assert mock_get_items.call_count == 2
        assert mock_download_func.call_count == 2
        # stop patch
        mock_argv.stop

