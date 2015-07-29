#!/usr/bin/env python
# coding: utf8

# Thoughts on imports ordering:
#   '\n\n'.join(builtin_libraries, external_libraries,
#   own_public_libraries, own_private_libraries, local_libraries,
#   same_package_modules)
import os
import sys
import re
import json
import logging
import urlparse
import traceback

from PIL import Image
from cStringIO import StringIO
import lxml
import html5lib  # Heavily recommended for bs4 (apparently)
import bs4
import requests
import magic  # python-magic

import pyaux


# Config-ish
_requests_params = dict(timeout=20, verify=False)  ## Also global-ish stuff
_CACHE_GET = False
_BS_PARSER = "html5lib"  # "lxml"  # "html5lib", "lxml", "xml", "html.parser"


# A bit sillily extensive; still, imgur and gfycat are loved by the reddits.
img_ext_re = r'\.(?:jpe?g|png|gif|tiff|gifv|webm)$'


_log = logging.getLogger(__name__)

MiB = 2 ** 20

_common_reqr = None


def indexall(topstr, substr):
    return (m.start() for m in re.finditer(re.escape(substr), topstr))


def indexall_re(topstr, substr_re):
    return (m.start() for m in re.finditer(substr_re, topstr))


def walker(text, opening='{', closing='}'):
    """ A near-useless experiment that was intended for `get_all_objects` """
    stack = []
    for pos in xrange(len(text)):
        if text[pos:pos + len(opening)] == opening:
            stack.append(pos)
            continue
        if text[pos:pos + len(closing)] == closing:
            try:
                start_pos = stack.pop(-1)
            except IndexError:
                continue
            yield text[start_pos:pos + 1]


def try_yaml_load(some_str, **kwa):
    import yaml
    try:
        return yaml.safe_load(some_str, **kwa)
    except Exception:
        return


def get_all_objects(text, beginning=r'{', debug=False):
    """ Zealous obtainer of mappings from a text, e.g. in javascript
    or JSON or whatever. Anything between '{' and '}'

    The monstrous advanced version.

    Not performant.

    Requires pyyaml.

    >>> st = 'a str with var stuff = {a: [{"v": 12}]} and such'
    >>> next(get_all_objects(st))
    {'a': [{'v': 12}]}
    """

    def _dbg_actual(st, *ar):
        print "D: ", st % ar

    _dbg = _dbg_actual if debug else (lambda *ar: None)

    import yaml

    # Allow any escape to be treated as the character itself.
    class ddd(dict):
        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                self.__setitem__(key, key)
                return key

    class TheLoader(yaml.SafeLoader):
        ESCAPE_REPLACEMENTS = ddd(yaml.SafeLoader.ESCAPE_REPLACEMENTS)

    from cStringIO import StringIO
    # optimised slicing
    if isinstance(text, unicode):
        _dbg("encoding")
        text = text.encode('utf-8')
    _dbg("Length: %r", len(text))
    beginnings = list(indexall_re(text, beginning))
    _dbg("Beginnings amount: %r", len(beginnings))
    _dbg("Beginnings list: %r", beginnings[:15] + (beginnings[15:] and ['...']))
    text = StringIO(text)
    for from_ in beginnings:
        current_pos = text.tell()
        _dbg("At %r", current_pos)
#         if from_ < current_pos:
#             _dbg("Skipping the beginning %r" % (from_,))
#             # NOTE: this will skip the recursed structures.
#             # Which is quite helpful.
#             continue
        text.seek(from_)
        loader = TheLoader(text)
        try:
            art_res = loader.get_data()
        except Exception as exc:
            _dbg("Nope: %r / %s / %r", exc, exc, exc.args)
            text.seek(from_)
            _dbg("Stuff was: %r", repr(text.read(50)).decode('string-escape'))
            continue
        assert isinstance(part_res, dict)
        yield part_res

def get_all_objects(text, beginning=r'{'):
    import yaml
    # TODO?: somehow optimise the slicing?
    for from_ in indexall_re(text, beginning):
        loader = yaml.SafeLoader(StringIO(text))
        loader.forward(from_)
        # loader.update(from_)
        try:
            part_res = loader.get_data()
        except Exception:
            continue
        assert isinstance(part_res, dict)
        yield part_res


def get_all_objects(text):
    # Helper functions

    # Permutate them all
    results = (try_yaml_load(text[from_:to_ + 1])
               for from_ in indexall(text, '{')
               for to_ in indexall(text, '}'))
    # Drop the failures
    results = (val for val in results if val is not None)
    # assert all(isinstance(val, dict) for val in results)
    # NOTE: returns a generator
    return results


# Debug helper
def setdiff(set_a, set_b):
    """ RTFS """
    set_a, set_b = set(set_a), set(set_b)
    return set_a - set_b, set_a & set_b, set_b - set_a


def try_loads(some_str):
    try:
        return json.loads(some_str)
    except Exception:
        return some_str


def get_reqr():
    global _common_reqr
    if _common_reqr is not None:
        return _common_reqr

    _log.info("Making a requests requester")
    from requests.adapters import HTTPAdapter

    reqr = requests.Session()
    reqr.mount('http://', HTTPAdapter(max_retries=5))
    reqr.mount('https://', HTTPAdapter(max_retries=5))
    _common_reqr = reqr
    return reqr


class GetError(Exception):
    """ Common exception-container for get_get errors. """
    pass


def get_get_get(url, **kwa):
    # TODO: user-agent, referer, cookies
    _log.info("Getting: %r", url)
    params = dict(_requests_params)
    params.update(kwa)
    reqr = get_reqr()
    
    try:
        return reqr.get(url, **params)
    except Exception as exc:
        raise GetError("Error getting url %r" % (url,), exc)


def get_get(*ar, **kwa):
    retries = kwa.pop('_xretries', 5)
    for retry in xrange(retries):
        try:
            return get_get_get(*ar, **kwa)
        except Exception as exc:
            traceback.print_exc()
            ee = exc
            print "On retry #%r   (%s)" % (retry, repr(exc)[:30])
    raise GetError(ee)


def get(url, cache_file=None, req_params=None, bs=True, response=False, undecoded=False,
        _max_len=30 * MiB):
    # TODO!: cache_dir (for per-url cache files with expiration)
    # (e.g. urlhash-named files with a hash->url logfile)

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
    # ...
    # NOTE: It appears that in at least one case BS might lose some
    #   links on unicode data (but no the same utf-8 data) with all
    #   parser but html5lib.
    bs = bs4.BeautifulSoup(data, _BS_PARSER)
    bs._source_url = url
    if response:
        return data, bs, resp
    return data, bs


def _filter(l):
    return [v for v in l if v]  # filter(None, l)


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


def bs2img(some_bs):
    """ BS to <img src=... /> addresses """
    # Sometimes more processing than needed, but whatever.
    return list(_preprocess(
        (v.get('src') for v in some_bs.findAll('img')),
        bs=some_bs))


def bs2lnk(some_bs):
    """ BS to <a href=... /> addresses """
    return list(_preprocess(
        (v.get('href') for v in some_bs.findAll('a')),
        bs=some_bs))


example_flickr_url_album = "https://www.flickr.com/photos/deeplovephotography/with/15485825656/"
example_flickr_url_page = "https://www.flickr.com/photos/deeplovephotography/15527622002/"
url1 = example_flickr_url_album
url2 = "http://cghub.com/images/view/574613/"
url3 = "http://zenaly.deviantart.com/art/Chinese-City-380473959"
url4 = example_flickr_url_page


flickr_page_re = re.compile(r'flickr\.com/photos.*[0-9]{9}')
flickr_sizes = 'o k h l c'.split()  # 'z m n s t q sq'
flickr_url_re = r'("(?:http|\\/\\/)[^"]+")'


def flickr_album_to_pages(bs):
    links = bs2lnk(bs)
    page_links = [lnk for lnk in links if flickr_page_re.search(lnk)]
    page_links = sorted(page_links)
    return page_links


def do_flickr_things(url, bs=None, html=None, maybe_album=True, **kwa):
    """ ...

    returns (is_complete_success, [candidate_link, ...])
    """
    log = _log.getChild('do_flickr_things').info
    if maybe_album:
        log("Processing flickr maybe_album %r", url)
    else:
        log("Processing flickr page %r", url)

    if bs is None:
        html, bs = get(url, bs=True)

    if maybe_album:
        page_urls = flickr_album_to_pages(bs)
        # Add the self-link in case it is not an album
        page_urls = list(page_urls) + [url]
        # TODO?: exception handling? Probably don't want (yet) though.
        results = [do_flickr_things(page_url, maybe_album=False, **kwa)
                   for page_url in page_urls]

        result_links = [
            res_link
            for _, page_res_links in results
            for res_link in page_res_links]
        result_links = sorted(set(result_links))
        result = (
            all(page_res for page_res, _ in results),
            result_links)
        return result

    # Otherwise just recursed or just don't want an album

    links_by_bs = bs2lnk(bs)
    links_by_re = re.findall(flickr_url_re, html)
    # The regex can handle JSON (i.e. extra backslashes), so try to process that too.
    links_by_re = [try_loads(lnk) for lnk in links_by_re]
    page_links = sorted(set(links_by_bs) | set(links_by_re))

    # Links by extension
    img_ext_links = [lnk for lnk in page_links if re.search(img_ext_re, lnk)]
    img_ext_links = sorted(set(img_ext_links))

    links_for_sizes = []
    for size in flickr_sizes:
        size_url_re = r'_%s\.[a-zA-Z0-9]{1,7}$' % (size,)
        size_links = [lnk for lnk in page_links if re.search(size_url_re, lnk)]
        size_links = sorted(set(size_links))
        if size_links:
            links_for_sizes.append((size, size_links))  # Save all for debug

    if links_for_sizes:
        _, target_links = links_for_sizes[0]
        return True, target_links
    else:
        return False, img_ext_links


def do_horrible_thing(url, base_url=None):
    data, resp = get(url, undecoded=True, response=True)
    mime = magic.from_buffer(data)
    try:
        # XXX/TODO: Use Image.frombytes or something
        img = Image.open(StringIO(data))
    except IOError:
        _log.log(3, "dht: Not an image file (%r): %r", mime, url)
        return
    width, height = img.size
    if width < 800 or height < 600:
        _log.log(3, "dht: Image too small (%r, %r): %r", width, height, url)
        return
    _log.log(5, "dht: Image (%dx%d %db): %r", width, height, len(data), url)
    return data, resp


def do_horrible_things(url=url2, do_horrible_thing_func=do_horrible_thing, urls_to_skip=None):
    html, bs = get(url, cache_file='tmpf5_do_horrible_things.html', bs=True)

    def _pp(lst):
        """ 'postprocess' a list of links """
        # Only HTTP[S] links (not expecting `ftp://`, not needing
        # `javascript:` and `mailto:`)
        res = [val
               for val in lst
               if val.startswith('http') or val.startswith('/')]
        # (urljoin should be done already though)
        return [urlparse.urljoin(url, val) for val in res]

    imgs, links = bs2img(bs), bs2lnk(bs)
    to_check = imgs + links
    # ...
    if 'flickr.' in url:
        _log.debug("dhts: also trying flickr at %r", url)
        flickr_res, flickr_stuff = do_flickr_things(url, bs=bs, html=html)
        if flickr_stuff and isinstance(flickr_stuff, list):
            if flickr_res:
                to_check = flickr_stuff  ## Good enough, get just that
            else:
                to_check += flickr_stuff  ## Try too much things.
    # ...
    to_check_baselen = len(to_check)
    to_check = _pp(to_check)
    if urls_to_skip:
        to_check = [v for v in to_check if v not in urls_to_skip]
    # Synopsis: check each url on the page for being a notably large image and download all such
    # TODO?: grab all-all URLs (including plaintext)?
    _log.debug("dhts: %r (of %r) urls to check", len(to_check), to_check_baselen)
    res = []
    for turl in to_check:
        try:
            stuff = do_horrible_thing_func(turl, base_url=url)
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
    cres = do_horrible_things(sys.argv[1])
    import IPython
    IPython.embed(banner1="`cres`.")
