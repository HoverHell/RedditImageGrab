# IPython log file

## Thoughts on imports ordering:
##   '\n\n'.join(builtin_libraries, external_libraries,
##   own_public_libraries, own_private_libraries, local_libraries,
##   same_package_modules)
import os
import re
import logging
import urlparse

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

def get_get(url):
    ## TODO: user-agent, referer, cookies
    ## TODO: Timtout and retry options
    _log.info("Getting: %r", url)
    return requests.get(url)
def get(url, cache_file=None, req_params=None, bs=True, undecoded=False):
    ## TODO!: cache_dir  (for per-url cache files with expiration)  (e.g. urlhash-named files with a hash->url logfile)
    if undecoded:
        bs = False
    if _CACHE_GET and cache_file is not None and os.path.isfile(cache_file):
        with open(cache_file) as f:
            data_bytes = f.read()
            data = data_bytes if undecoded else data_bytes.decode('utf-8')
    else:
        resp = get_get(url, **(req_params or {}))
        #if resp.status_code != 200: ...
        if undecoded:
            data = ''.join(resp.iter_content())  #, stream=True  ## XXX: Size limit?
            data_bytes = data
        else:
            data = resp.text
            data_bytes = data.encode('utf-8')
        if cache_file is not None:
            with open(cache_file, 'w') as f:
                f.write(data_bytes)
    if not bs:
        return data
    ## ...
    ## NOTE: It appears that in at least one case BS might lose some
    ##   links on unicode data (but no the same utf-8 data) with all
    ##   parser but html5lib.
    bs = bs4.BeautifulSoup(data, _BS_PARSER)
    bs._source_url = url
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
    return _preprocess((v.get('src') for v in some_bs.findAll('img')), bs=some_bs)
def bs2lnk(some_bs):
    return _preprocess((v.get('href') for v in some_bs.findAll('a')), bs=some_bs)


url1 = "http://www.flickr.com/photos/tawnyarox/6913558128/lightbox/"
url2 = "http://cghub.com/images/view/574613/"
url3 = "http://zenaly.deviantart.com/art/Chinese-City-380473959"


def do_flickr_things(url=url1):
    html, bs = get(url, cache_file='tmpf.html', bs=True)
    imgs = bs2im(bs)
    links = bs2lnk(bs)
    flickr_sizes = [v for v in links if v.endswith('sizes/')]
    if not flickr_sizes:
        return
    sl = flickr_sizes[0]
    sl_n = urlparse.urljoin(url, sl) + 'o/'
    sl_html, sl_bs = get(sl_n, cache_file='tmpf2.html', bs=True)
    _pp = lambda l: [urlparse.urljoin(url, v) for v in l if v.startswith('http')]
    links2 = _pp(_preprocess(v.get('href') for v in sl_bs.findAll('a') if 'ownloa' in v.text))
    #imgs2 = _preprocess(v for v in bs2lnk(sl_bs) '_o.' in v)
    imgs2 = _pp(_preprocess(vv for vv in bs2lnk(sl_bs) if re.match(r'.*_o\.[0-9A-Za-z]+$', vv)))
    #return locals()
    return links2 + imgs2
def do_horrible_thing(url, base_url=None):
    resp = get(url, undecoded=True)
    data = resp
    mime = magic.from_buffer(data)
    try:
        img = Image.open(StringIO(data))  ## XXX/TODO: Use Image.frombytes or something
    except IOError as e:
        _log.log(3, "Not an image file (%r): %r", mime, url)
        return
    width, height = img.size
    if width < 800 or height < 600:
        _log.log(3, "Image too small (%r, %r): %r", width, height, url)
        return
    return data
def do_horrible_things(url=url2, do_horrible_thing=do_horrible_thing):
    html, bs = get(url, cache_file='tmpf5_do_horrible_things.html', bs=True)
    ## Postprocess:
    # (urljoin should be done already though)
    # Only HTTP[S] links (not expecting `ftp://`, not needing `javascript:` and `mailto:`)
    _pp = lambda l: [urlparse.urljoin(url, v) for v in l if v.startswith('http')]
    imgs, links = _pp(bs2im(bs)), _pp(bs2lnk(bs))
    to_check = imgs + links
    ## ...
    if 'flickr' in url:
        flickr_stuff = do_flickr_things(url)
        if flickr_stuff and isinstance(flickr_stuff, list):
            to_check += flickr_stuff
    ## Synopsis: check each url on the page for being a notably large image and download all such
    ## TODO?: grab all-all URLs (including plaintext)?
    res = []
    for turl in to_check:
        stuff = do_horrible_thing(turl, base_url=url)
        if stuff:
            res.append((turl, stuff))
    return to_check, res


if __name__ == '__main__':
    pyaux.runlib.init_logging(level=1)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(21)
    pyaux.use_exc_ipdb()
    res = do_horrible_things()
    import IPython; IPython.embed(banner1="`res`.")
