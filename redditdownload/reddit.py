#!/usr/bin/env python
"""Return list of items from a sub-reddit of reddit.com."""

import sys
import HTMLParser
from urllib2 import urlopen, Request, HTTPError
from json import JSONDecoder

import time


def getitems(subreddit, multireddit=False, previd='', reddit_sort=None, search_timestamps=None):
    """Return list of items from a subreddit.

    :param subreddit: subreddit to load the post
    :param multireddit: multireddit if given instead subreddit
    :param previd: previous post id, to get more post
    :param reddit_sort: type of sorting post
    :param search_timestamps: performs a reddit search between two timestamps
    :returns: list -- list of post url

    :Example:

    >>> # Recent items for Python.
    >>> items = getitems('python')
    >>> for item in items:
    ...     print '\t%s - %s' % (item['title'], item['url']) # doctest: +SKIP

    >>> # Previous items for Python.
    >>> olditems = getitems('python', ITEMS[-1]['id'])
    >>> for item in olditems:
    ...     print '\t%s - %s' % (item['title'], item['url']) # doctest: +SKIP
    """

    items = []

    url_args = []

    if multireddit:
        if '/m/' not in subreddit:
            warning = ('That doesn\'t look like a multireddit. Are you sure'
                       'you need that multireddit flag?')
            print warning
            sys.exit(1)
        url = 'http://www.reddit.com/user/%s.json' % subreddit
    if not multireddit:
        if '/m/' in subreddit:
            warning = ('It looks like you are trying to fetch a multireddit. \n'
                       'Check the multireddit flag. '
                       'Call --help for more info')
            print warning
            sys.exit(1)

        if search_timestamps is not None:
            url = 'http://www.reddit.com/r/{}/search.json'.format(subreddit)
            url_args.append(('q', 'timestamp%3A{}..{}'.format(search_timestamps[0], search_timestamps[1])))
            url_args.append(('restrict_sr', 'on'))
            url_args.append(('syntax', 'cloudsearch'))
        else:
            # no sorting needed
            if reddit_sort is None:
                url = 'http://www.reddit.com/r/{}.json'.format(subreddit)
            # if sort is top or controversial, may include advanced sort (ie week, all etc)
            elif 'top' in reddit_sort:
                url = 'http://www.reddit.com/r/{}/{}.json'.format(subreddit, 'top')
            elif 'controversial' in reddit_sort:
                url = 'http://www.reddit.com/r/{}/{}.json'.format(subreddit, 'controversial')
            # use default
            else:
                url = 'http://www.reddit.com/r/{}/{}.json'.format(subreddit, reddit_sort)

    # Get items after item with 'id' of previd.

    hdr = {'User-Agent': 'RedditImageGrab script.'}

    # here where is query start
    # query for previd comment
    if previd:
        url_args.append(('after', 't3_{}'.format(previd)))

    # query for more advanced top and controversial sort
    # available extension : hour, day, week, month, year, all
    # ie tophour, topweek, topweek etc
    # ie controversialhour, controversialweek etc

    # check if reddit_sort is advanced sort
    is_advanced_sort = False
    if reddit_sort is not None:
        if reddit_sort == 'top' or reddit_sort == 'controversial':
            # dont need another additional query
            is_advanced_sort = False
        elif 'top' in reddit_sort:
            is_advanced_sort = True
            sort_time_limit = reddit_sort[3:]
            sort_type = 'top'
        elif 'controversial' in reddit_sort:
            is_advanced_sort = True
            sort_time_limit = reddit_sort[13:]
            sort_type = 'controversial'

        if is_advanced_sort:
            # add advanced sort
            url_args.append(('sort', sort_type))
            url_args.append(('t', sort_time_limit))

    if len(url_args) > 0:
        url += '?'
        for a in url_args:
            url += '{}={}&'.format(a[0], a[1])
        url = url[:-1]

    DONE = False
    while not DONE:
        try:
            req = Request(url, headers=hdr)
            json = urlopen(req).read()
            data = JSONDecoder().decode(json)
            if isinstance(data, dict):
                items.extend([x['data'] for x in data['data']['children']])
            elif isinstance(data, list):
                # e.g. https://www.reddit.com/r/photoshopbattles/comments/29evni.json
                items.extend([x['data'] for subdata in data for x in subdata['data']['children']])
                items.extend([item for item in items if item.get('url')])
            DONE = True
        except HTTPError as ERROR:
            error_message = '\tHTTP ERROR: Code %s for %s' % (ERROR.code, url)

            if ERROR.code == 503:
                # don't abort
                print('\tGot error 503, waiting 10 seconds before resuming...')
                time.sleep(10)
            else:
                DONE = True

        except ValueError as ERROR:
            if ERROR.args[0] == 'No JSON object could be decoded':
                error_message = 'ERROR: subreddit "%s" does not exist' % (subreddit)
                DONE = True
            raise ERROR
        except KeyboardInterrupt as ERROR:
            error_message = '\tKeyboardInterrupt: url:{}.'.format(url)
            sys.exit(error_message)

    # This is weird but apparently necessary: reddit's json data
    # returns `url` values html-escaped, whereas we normally need them
    # in the way they are meant to be downloaded (i.e. urlquoted at
    # most).
    htmlparser = HTMLParser.HTMLParser()
    for item in items:
        if item.get('url'):
            item['url'] = htmlparser.unescape(item['url'])

    return items
