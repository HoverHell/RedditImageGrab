import json
try:  # py3
    from unittest import mock
except ImportError:  # py2
    import mock
    from urllib2 import HTTPError

import pytest

from redditdownload.reddit import getitems


def test_empty_string():
    """test with empty string input."""
    res = getitems('')
    assert isinstance(res, list)
    assert len(res) > 0

@mock.patch('redditdownload.reddit.urlopen')
@mock.patch('redditdownload.reddit.Request')
def test_empty_string_mock(mock_requests, mock_urlopen):
    """test empty string but with mocking external dependencies.

    it will result the following url which 
    https://www.reddit.com/r/.json 
    which will redirect to json version of this url
    https://www.reddit.com/subreddits
    """
    expected_url = 'http://www.reddit.com/r/.json'
    mock_resp = mock.Mock()
    mock_items = range(5)
    mock_data = [{'data' :x} for x in mock_items]
    mock_resp.read.return_value = json.dumps({'data':{'children':mock_data}})
    mock_urlopen.return_value = mock_resp

    res = getitems("")

    assert res == mock_items
    mock_requests.assert_called_once_with(expected_url, headers=mock.ANY)


@mock.patch('redditdownload.reddit.urlopen')
@mock.patch('redditdownload.reddit.Request')
def test_sort_type(mock_requests, mock_urlopen):
    """test sort_type."""
    mock_resp = mock.Mock()
    mock_items = range(5)
    mock_data = [{'data' :x} for x in mock_items]
    mock_resp.read.return_value = json.dumps({'data':{'children':mock_data}})
    mock_urlopen.return_value = mock_resp

    # sort_type none, input is multireddit
    sort_type = None
    reddit_input = 'some_user/m/some_multireddit'
    expected_url = 'http://www.reddit.com/user/some_user/m/some_multireddit.json'
    res = getitems(reddit_input, reddit_sort=sort_type, multireddit=True)
    # test
    mock_requests.assert_called_once_with(expected_url, headers=mock.ANY)

    # starting with none sort_type
    mock_requests.reset_mock()
    sort_type = None
    expected_url = 'http://www.reddit.com/r/cats.json'
    res = getitems('cats', reddit_sort=sort_type)
    # test
    mock_requests.assert_called_once_with(expected_url, headers=mock.ANY)

    # test with sort type
    for sort_type in ['hot', 'new', 'rising', 'controversial', 'top', 'gilded']:
        mock_requests.reset_mock()
        res = getitems('cats', reddit_sort=sort_type)
        expected_url = 'http://www.reddit.com/r/cats/{}.json'.format(sort_type)
        mock_requests.assert_called_once_with(expected_url, headers=mock.ANY)

    # test with advanced_sort
    for sort_type in ['controversial', 'top']:
        for time_limit in ['hour', 'day', 'week', 'month', 'year', 'all']:
            reddit_sort = sort_type + time_limit
            mock_requests.reset_mock()
            url_format = 'http://www.reddit.com/r/cats/{0}.json?sort={0}&t={1}'
            expected_url = url_format.format(sort_type, time_limit)

            res = getitems('cats', reddit_sort=reddit_sort)

            mock_requests.assert_called_once_with(expected_url, headers=mock.ANY)

@mock.patch('redditdownload.reddit.urlopen')
@mock.patch('redditdownload.reddit.Request')
def test_advanced_sort_and_last_id(mock_requests, mock_urlopen):
    """test for advanced sort and last id."""
    last_id = '44h81z'
    mock_resp = mock.Mock()
    mock_items = range(5)
    mock_data = [{'data' :x} for x in mock_items]
    mock_resp.read.return_value = json.dumps({'data':{'children':mock_data}})
    mock_urlopen.return_value = mock_resp

    # test with advanced_sort
    for sort_type in ['controversial', 'top']:
        for time_limit in ['hour', 'day', 'week', 'month', 'year', 'all']:
            mock_requests.reset_mock()

            reddit_sort = sort_type + time_limit
            url_format = 'http://www.reddit.com/r/cats/{0}.json?after=t3_{2}&sort={0}&t={1}'
            expected_url = url_format.format(sort_type, time_limit, last_id)

            res = getitems('cats', reddit_sort=reddit_sort, previd=last_id)

            mock_requests.assert_called_once_with(expected_url, headers=mock.ANY)


@mock.patch('redditdownload.reddit.Request')
def test_raise_error_on_request(mock_requests):
    """test when error raised on requests."""
    errors = [
        HTTPError(None, 404, 'mock error', None, None), KeyboardInterrupt]
    for error in  errors:
        mock_requests.side_effect = error

        with pytest.raises(SystemExit):
            getitems('cats')

@mock.patch('redditdownload.reddit.Request')
def test_value_error_on_request(mock_requests):
    """test value error on requests."""
    mock_requests.side_effect = ValueError('Mock error')
    with pytest.raises(ValueError):
        getitems('cats')

    # value error contain specific message which raise other error.
    msg = 'No JSON object could be decoded'
    mock_requests.side_effect = ValueError(msg)
    with pytest.raises(SystemExit):
        getitems('cats')

def test_error_on_multireddit_input():
    """test wrong multireddit flag on multireddit input."""
    # multireddit flag raised but input is normal subreddit
    with pytest.raises(SystemExit):
        getitems('cats', multireddit=True)

    # multireddit input given but multireddit flag is False
    with pytest.raises(SystemExit):
        getitems('someuser/m/some_multireddit', multireddit=False)
