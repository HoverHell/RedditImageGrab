#!/usr/bin/env python
# coding: utf8

## Thoughts on imports ordering:
##   '\n\n'.join(builtin_libraries, external_libraries,
##   own_public_libraries, own_private_libraries, local_libraries,
##   same_package_modules)
import os
import sys
import re
import logging
import urlparse
import traceback

from PIL import Image
from cStringIO import StringIO
import lxml, html5lib  ## Heavily recommended for bs4 (apparently)
import bs4
import requests
import magic  # python-magic

import pyaux


_log = logging.getLogger(__name__)


_CACHE_GET = False
_BS_PARSER = "html5lib"  # "lxml"  # "html5lib", "lxml", "xml", "html.parser"


def cfg_requests():
    from requests.adapters import HTTPAdapter

    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=5))
    s.mount('https://', HTTPAdapter(max_retries=5))


## Note: does nasty global things
cfg_requests()


class GetError(Exception):
    """ Common exception-container for get_get errors. """
    pass


_requests_params = dict(timeout=20)  ## Also global-ish stuff
def get_get_get(url, **kwa):
    ## TODO: user-agent, referer, cookies
    ## TODO: Timtout and retry options
    _log.info("Getting: %r", url)
    params = dict(_requests_params)
    params.update(kwa)
    try:
        return requests.get(url, **kwa)
    except Exception as e:
        raise GetError("Error getting url %r" % (url,), e)
def get_get(*ar, **kwa):
    retries = kwa.pop('_xretries', 5)
    for retry in xrange(retries):
        try:
            return get_get_get(*ar, **kwa)
        except Exception as e:
            traceback.print_exc()
            ee = e
            print "On retry #%r" % (retry,)
    raise GetError(ee)
def get(url, cache_file=None, req_params=None, bs=True, response=False, undecoded=False, _max_len=30*(2**20)):
    ## TODO!: cache_dir  (for per-url cache files with expiration)  (e.g. urlhash-named files with a hash->url logfile)
    if undecoded:
        bs = False
    resp = None
    if _CACHE_GET and cache_file is not None and os.path.isfile(cache_file):
        with open(cache_file) as f:
            data_bytes = f.read()
            data = data_bytes if undecoded else data_bytes.decode('utf-8')
    else:
        resp = get_get(url, stream=True, **(req_params or {}))
        #if resp.status_code != 200: ...
        if undecoded:
            data = bytearray()
            for chunk in resp.iter_content(chunk_size=16384):
                data += chunk
                if len(data) > _max_len:
                    print "Too large"
                    break
            data = bytes(data)  ## Have to, alas.
            data_bytes = data
        else:
            data = resp.text
            data_bytes = data.encode('utf-8')
        if cache_file is not None:
            with open(cache_file, 'w') as f:
                f.write(data_bytes)
    if not bs:  ## ... should've done a dict.
        if response:
            return data, resp
        return data
    ## ...
    ## NOTE: It appears that in at least one case BS might lose some
    ##   links on unicode data (but no the same utf-8 data) with all
    ##   parser but html5lib.
    bs = bs4.BeautifulSoup(data, _BS_PARSER)
    bs._source_url = url
    if response:
        return data, bs, resp
    return data, bs
def _filter(l):
    return filter(None, l)  #[v for v in l if v]
def _url_abs(l, base_url):
    return (urlparse.urljoin(base_url, v) for v in l)
def _preprocess_bs_links(bs, links):
    try:
        base_url = bs._source_url
    except AttributeError:
        return links
    return _url_abs(links, base_url)
def _preprocess(l, bs=None):
    res = sorted(set(_filter(l)))
    res = _preprocess_bs_links(bs, res) if bs is not None else res
    return res
def bs2im(some_bs):
    ## Sometimes more processing than needed but whatever.
    return list(_preprocess((v.get('src') for v in some_bs.findAll('img')), bs=some_bs))
def bs2lnk(some_bs):
    return list(_preprocess((v.get('href') for v in some_bs.findAll('a')), bs=some_bs))


url1 = "http://www.flickr.com/photos/tawnyarox/6913558128/lightbox/"
url2 = "http://cghub.com/images/view/574613/"
url3 = "http://zenaly.deviantart.com/art/Chinese-City-380473959"


def do_flickr_things(url, bs=None, html=None, recurse=True, fsize='o'):
    if bs is None:
        html, bs = get(url, cache_file='tmpf.html', bs=True)
    imgs = bs2im(bs)
    links = bs2lnk(bs)
    ## TODO!: Flickr sets; e.g. “http://www.flickr.com/photos/dougtanner/9786310375/in/set-72157635587262422/lightbox/”
    ## (link to “…/sets/…”, image-links to “…/in/set-…” there.
    #flickr_sizes = [v for v in links if re.v.endswith('siezes/')]
    flickr_sizes_base = [v for v in links if re.findall(r'/sizes/([a-z]/)?', v)]
    flickr_sizes = [re.sub(r'/sizes/([a-z]/)?', '/sizes/%s/' % (fsize,), v) for v in flickr_sizes_base]
    if not flickr_sizes:
        _log.log(19, "Failed to find flickr sizes link at %r", url)
        return False, None
    sl = flickr_sizes[0]
    sl_n = urlparse.urljoin(url, sl)
    sl_html, sl_bs, sl_resp = get(sl_n, cache_file='tmpf2.html', bs=True, response=True)[:3]
    _pp = lambda l: [vv for vv in [urlparse.urljoin(url, v) for v in l] if vv.startswith('http')]
    links3, imgs3 = bs2lnk(sl_bs), bs2im(sl_bs)
    all3 = links3 + imgs3
    links2 = _pp(_preprocess(v.get('href') for v in sl_bs.findAll('a') if 'ownloa' in v.text))
    #imgs2 = _preprocess(v for v in bs2lnk(sl_bs) '_o.' in v)
    imgs2 = _pp(_preprocess(vv for vv in all3 if re.match(r'.*_%s\.[0-9A-Za-z]+$' % (fsize,), vv)))
    if links2 or imgs2:
        return True, (links2 + imgs2)
    ## Not found - look for some other possible sizes.
    if sl_resp is not None:
        links3 += [sl_resp.url]  # for redirects
    sizes = 'o k h l c'.split()  # 'z m n s t q sq'
    link3 = link3sv = None
    for size in sizes:
        surl = '/sizes/%s/' % (size,)
        links3s = [v for v in links3 if surl in v]
        if links3s:
            link3 = links3s[0]
            link3sv = size
            break
    if link3 and recurse:  # Try that size.
        return do_flickr_things(link3, recurse=False, fsize=link3sv)
    ## TODO: Try for links to other sizes in order
    return False, imgs3
def do_horrible_thing(url, base_url=None):
    data, resp = get(url, undecoded=True, response=True)
    mime = magic.from_buffer(data)
    try:
        img = Image.open(StringIO(data))  ## XXX/TODO: Use Image.frombytes or something
    except IOError as e:
        _log.log(3, "dht: Not an image file (%r): %r", mime, url)
        return
    width, height = img.size
    if width < 800 or height < 600:
        _log.log(3, "dht: Image too small (%r, %r): %r", width, height, url)
        return
    _log.log(5, "dht: Image (%dx%d %db): %r", width, height, len(data), url)
    return data, resp
def do_horrible_things(url=url2, do_horrible_thing=do_horrible_thing, urls_to_skip=None):
    html, bs = get(url, cache_file='tmpf5_do_horrible_things.html', bs=True)
    ## Postprocess:
    # (urljoin should be done already though)
    # Only HTTP[S] links (not expecting `ftp://`, not needing `javascript:` and `mailto:`)
    _pp = lambda l: [urlparse.urljoin(url, v) for v in l if v.startswith('http')]
    imgs, links = _pp(bs2im(bs)), _pp(bs2lnk(bs))
    to_check = imgs + links
    ## ...
    if 'flickr.' in url:
        _log.debug("dhts: also trying flickr at %r", url)
        flickr_res, flickr_stuff = do_flickr_things(url, bs=bs, html=html)
        if flickr_stuff and isinstance(flickr_stuff, list):
            if flickr_res:
                to_check = flickr_stuff  ## Good enough, get just that
            else:
                to_check += flickr_stuff  ## Try too much things.
    ## ...
    to_check_baselen = len(to_check)
    if urls_to_skip:
        to_check = [v for v in to_check if v not in urls_to_skip]
    ## Synopsis: check each url on the page for being a notably large image and download all such
    ## TODO?: grab all-all URLs (including plaintext)?
    _log.debug("dhts: %r (of %r) urls to check", len(to_check), to_check_baselen)
    res = []
    for turl in to_check:
        try:
            stuff = do_horrible_thing(turl, base_url=url)
        except GetError:
            continue  ## ... will be logged anyway.
        if stuff:
            data, resp = stuff[:2]
            res.append((turl, data, dict(resp=resp)))
    _log.debug("dhts: %r images found", len(res))
    return to_check, res


if __name__ == '__main__':
    pyaux.runlib.init_logging(level=1)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(21)
    pyaux.use_exc_ipdb()
    res = do_horrible_things(sys.argv[1])
    import IPython; IPython.embed(banner1="`res`.")
