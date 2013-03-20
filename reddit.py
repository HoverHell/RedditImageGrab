"""Return list of items from a sub-reddit of reddit.com."""

from urllib2 import urlopen, Request, HTTPError
from json import JSONDecoder


def getitems(subreddit, previd=''):
    """Return list of items from a subreddit."""
    url = 'http://www.reddit.com/r/%s.json' % subreddit
    # Get items after item with 'id' of previd.
    
    hdr = { 'User-Agent' : 'RedditImageGrab script.' }
    
    if previd:
        url = '%s?after=t3_%s' % (url, previd)
    try:
        req = Request(url, headers=hdr)
        json = urlopen(req).read()
        data = JSONDecoder().decode(json)
        items = [x['data'] for x in data['data']['children']]
    except HTTPError as ERROR:
        print '\tHTTP ERROR: Code %s for %s.' % (ERROR.code, url)
        items = []
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
