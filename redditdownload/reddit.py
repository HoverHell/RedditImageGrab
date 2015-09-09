#!/usr/bin/env python
"""Return list of items from a sub-reddit of reddit.com."""

import sys
from urllib2 import urlopen, Request, HTTPError
from json import JSONDecoder


def getitems(subreddit, multireddit, previd=''):
    """Return list of items from a subreddit."""
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
        url = 'http://www.reddit.com/r/%s.json' % subreddit
    # Get items after item with 'id' of previd.

    hdr = {'User-Agent': 'RedditImageGrab script.'}

    if previd:
        url = '%s?after=t3_%s' % (url, previd)
    try:
        req = Request(url, headers=hdr)
        json = urlopen(req).read()
        data = JSONDecoder().decode(json)
        items = [x['data'] for x in data['data']['children']]
    except HTTPError as ERROR:
        error_message = '\tHTTP ERROR: Code %s for %s.' % (ERROR.code, url)
        sys.exit(error_message)
    except ValueError as ERROR:
        if ERROR.args[0] == 'No JSON object could be decoded':
            error_message = 'ERROR: subreddit "%s" does not exist' % (subreddit)
            sys.exit(error_message)
        raise ERROR
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
