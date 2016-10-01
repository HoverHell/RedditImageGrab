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
    script_folder = path.dirname(path.realpath(__file__))
    with open(path.join(script_folder, 'files', 'deviantart.html')) as f:
        mock_html = f.read()
    with mock.patch('redditdownload.deviantart.urlopen') as mock_urlopen:
        mock_resp = mock.Mock()
        mock_resp.read.return_value = mock_html
        mock_urlopen.return_value = mock_resp

        res = process_deviant_url(page_url)

        assert res == [image_url]
