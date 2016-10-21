"""test for deviantart."""
from os import path
try:  # py3
    from unittest import mock
except ImportError:  # py2
    import mock

from redditdownload.deviantart import process_deviant_url


def test_direct_url():
    """test parser when url is direct url to image."""
    url = (
        'http://orig13.deviantart.net'
        '/0ce0/f/2016/243/8/b/mimikyusad_re_by_starsoulart-dafy5ft.jpg')
    res = process_deviant_url(url)
    assert res == [url]


def test_page_url():
    """test parser when url link to html page."""
    page_url = 'http://blizzomos.deviantart.com/art/Blizz-Scarlet-fate-635233437'
    image_url = (
        'http://pre05.deviantart.net'
        '/100e/th/pre/i/2016/262/d/3/_blizz__scarlet_fate_by_blizzomos-dai7999.png')
    mock_html = mock.Mock()
    raw_url = (
        'http://t12.deviantart.net/lGEeqCoH2VPjwUc0PptAVguf8cg=/fit-in/150x150/'
        'filters:no_upscale():origin()/pre05/100e/th/pre/i/2016/262/d/3/'
        '_blizz__scarlet_fate_by_blizzomos-dai7999.png'
    )
    mock_tag = mock.Mock()
    mock_tag.get.return_value = raw_url

    def mock_bs_side_effect_func(arg):
        """side effect for mocked BeautifulSoup obj."""
        if arg == 'img':
            return [mock_tag]
        return arg

    with mock.patch('redditdownload.deviantart.urlopen') as mock_urlopen, \
            mock.patch('redditdownload.deviantart.BeautifulSoup') as mock_bs:
        mock_resp = mock.Mock()
        mock_resp.read.return_value = mock_html
        mock_bs.return_value.select.side_effect = mock_bs_side_effect_func
        mock_urlopen.return_value = mock_resp

        res = process_deviant_url(page_url)

        assert res == [image_url]
        assert len(mock_bs.mock_calls) == 2
        mock_bs.return_value.select.assert_called_once_with('img')

        assert len(mock_urlopen.mock_calls) == 2
        assert mock.call(mock_urlopen.return_value.read.return_value, 'lxml') in mock_bs.mock_calls
        mock_urlopen.assert_called_once_with(page_url)
        mock_urlopen.return_value.read.assert_called_once_with()

