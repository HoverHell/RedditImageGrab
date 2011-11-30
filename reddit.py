"""Return list of items from a sub-reddit of reddit.com."""

from urllib2 import urlopen, HTTPError 
from json import JSONDecoder

def getitems( subreddit, previd=''):
    """Return list of items from a subreddit."""
    url = 'http://www.reddit.com/r/%s.json' % subreddit
    # Get items after item with 'id' of previd.
    if previd != '':
        url = '%s?after=t3_%s' % (url, previd)
    try:
        json = urlopen( url ).read()
        data = JSONDecoder().decode( json )
        items = [ x['data'] for x in data['data']['children'] ]
    except HTTPError as ERROR:
        print '\tHTTP ERROR: Code %s for %s.' % (ERROR.code, url)
        items = []
    return items

if __name__ == "__main__":
    LAST = ''

    print 'Recent items for Python.'
    ITEMS = getitems( 'python' )
    for ITEM in ITEMS:
        print '\t%s - %s' % (ITEM['title'], ITEM['url'])
        LAST = ITEM['id']

    print 'Previous items for Python.'
    OLDITEMS = getitems( 'python', LAST )
    for ITEM in OLDITEMS:
        print '\t%s - %s' % (ITEM['title'], ITEM['url'])
