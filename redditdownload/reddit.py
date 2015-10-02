#!/usr/bin/env python
"""Return list of items from a sub-reddit of reddit.com."""

import sys
from urllib2 import urlopen, Request, HTTPError
from json import JSONDecoder


def getitems(subreddit, multireddit=False, previd='', reddit_sort=None):
    """Return list of items from a subreddit.

    :param subreddit: subreddit to load the post
    :param multireddit: multireddit if given instead subreddit
    :param previd: previous post id, to get more post
    :param reddit_sort: type of sorting post
    :returns: list -- list of post url
    """

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
        url = '%s?after=t3_%s' % (url, previd)

    # query for more advanced top and controversial sort
    # available extension : hour, day, week, month, year, all
    # ie tophour, topweek, topweek etc
    # ie controversialhour, controversialweek etc

    # check if reddit_sort is advanced sort
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

        # check if url have already query
        if '?' in url.split('/')[-1] and is_advanced_sort:
            url += '&'
        else:  # url dont have query yet
            url += '?'

        # add advanced sort
        if is_advanced_sort:
            url += 'sort={}&t={}'.format(sort_type, sort_time_limit)

    try:
        req = Request(url, headers=hdr)
        json = urlopen(req).read()
        data = JSONDecoder().decode(json)
        items = [x['data'] for x in data['data']['children']]
    except HTTPError as ERROR:
        error_message = '\tHTTP ERROR: Code %s for %s' % (ERROR.code, url)
        sys.exit(error_message)
    except ValueError as ERROR:
        if ERROR.args[0] == 'No JSON object could be decoded':
            error_message = 'ERROR: subreddit "%s" does not exist' % (subreddit)
            sys.exit(error_message)
        raise ERROR
    except KeyboardInterrupt as ERROR:
        error_message = '\tKeyboardInterrupt: url:{}.'.format(url)
        sys.exit(error_message)

    return items

if __name__ == "__main__":

    print 'Recent items for Python.'
    ITEMS = getitems('python')
    for ITEM in ITEMS:
        print '\t%s - %s' % (ITEM['title'], ITEM['url'])

    print 'Previous items for Python.'
    OLDITEMS = getitems('python', ITEMS[-1]['id'])
    for ITEM in OLDITEMS:
        print '\t%s - %s' % (ITEM['title'], ITEM['url'])
