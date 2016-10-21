import unittest
try:
    from unittest import mock
except ImportError:
    from mock import mock

from redditdownload.redditdownload import download_from_url

class TestDownloadFromURLMethods(unittest.TestCase):

    @mock.patch('redditdownload.redditupload.download')
    @mock.patch('redditdownload.redditdownload.pathexists')
    def test_download_from_url(self, mock_pathexist, mock_download_func):
        """test :func:`download_from_url`."""
        # set mock value
        mock_url = (
            'https://i.reddituploads.com/aaa5af49dea641718b1428d7b0c46bec'
            '?fit=max&h=1536&w=1536&s=6f08d532dc8e81ea8d4a85e6cac643b2')
        mock_dest_file  = mock.Mock()
        mock_pathexist.return_value = False

        download_from_url(mock_url, mock_dest_file)

        mock_pathexist.assert_called_once_with(mock_dest_file)
        mock_download_func.assert_called_once_with(mock_url, mock.ANY)
