#!/usr/bin/env python
"""test remotemd5 module."""
# import mock library
# try:  # py3
#     from unittest.mock import patch, Mock
# except ImportError:  # py2
#     from mock import patch, Mock

import pytest
from mock import patch, MagicMock

from redditdownload.remotemd5 import get_remote_md5_sum


@patch('redditdownload.remotemd5.urlopen')
def test_get_remote_md5_sum(mock_urlopen):
    """test get remote md5sum."""
    url1 = 'http://i.imgur.com/removed.png'
    # remote.read didn't return string or byte
    with pytest.raises(TypeError):
        get_remote_md5_sum(url1)

    # remote read return string or byte
    test_data = (
        ('random_string', '8ebbf52d27de03ddc54209a79ee80d4b'),
        ('1', '531acd16ec138e070b95ca843698b45c')
    )
    for read_return_value, read_md5 in test_data:
        # create MagicMock as return value of mock_urlopen
        mock_response = MagicMock()
        mock_response.read.return_value = read_return_value
        mock_urlopen.return_value = mock_response
        # check if result equal to expected md5
        res = get_remote_md5_sum(url1)
        assert res == read_md5
        assert isinstance(res, str)
        assert mock_urlopen.called
        assert mock_response.read.called
        mock_urlopen.assert_called_with(url1)
        mock_response.read.assert_called_with(4096)
