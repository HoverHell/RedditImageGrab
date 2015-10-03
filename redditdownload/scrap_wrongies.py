#!/usr/bin/env python
# coding: utf8
""" Scrap stuff from "wrong data type" pages of RedditImageGrab """

try:
    from redditdownload import _WRONGDATA_LOGFILE
except ImportError:
    _WRONGDATA_LOGFILE = '.wrong_type_pages.jsl'

# ### Config-ish ###
# File for putting in 'debug' metadata.
# NOTE: Also used to skip already-checked base URLs (e.g. for resuming).
_OUTDATA_LOGFILE = '.wtp_out.jsl'
# File to put in the target directory with metadata about images in it.
_DIRDATA_LOGFILE = '.wrp_meta.jsl'
# Subdirectory to make in the target directory
_DIRSUBDIR = 'wextras'


import os
import errno
import sys
import re
import json
import functools
import logging
import mimetypes
import hashlib

from atomicfile import AtomicFile
import magic

import img_scrap_stuff
from img_scrap_stuff import GetError


_log = logging.getLogger(__name__)


def _hash(val):
    """ *some* bytestring hash func (with no particular demands aside
    from collisionlessness) """
    return hashlib.md5(val).hexdigest()


def make_filename(url, imgdata, resp=None):
    mime_type = magic.from_buffer(imgdata, mime=True)
    # ... last extension in the list tends to be better (and longer)
    mime_ext = mimetypes.guess_all_extensions(mime_type)[-1]
    # # TODO: filename from `resp`
    # if resp is not None: ...
    datahash = _hash(imgdata)
    urlhash = _hash(url)
    urlv = url.rstrip('/').rsplit('/', 1)[1]
    return '%s%s' % (urlv, mime_ext)  # NOTE: cannot check for existing here.


def unjsl_g(fn):
    """ un-json-lines: filename -> streamed generator of deserialized
    objects """
    log = _log.getChild('unjsl(%r)' % (fn,))
    with open(fn) as f:
        for l in f.readlines():
            try:
                yield json.loads(l)
            except ValueError:
                log.error("JSON fail: %r", l)


def unjsl(fn):
    """ unjsl: non-generator version  """
    return list(unjsl_g(fn))


def unjsl_or_empty(fn):
    """ unjsl-if-file-exists """
    try:
        return unjsl(fn)
    except IOError as e:
        if e.errno != errno.ENOENT:  # “IOError: [Errno 2] No such file or directory: …”
            raise
        return []


def onjsl(fn, data):
    """ append data to file at filename `fn` """
    jsd = json.dumps(data) + '\n'
    with open(fn, 'a', 1) as f:
        f.write(jsd)


def mkdirs(d):
    """ `mkdir -p`, sort of """
    try:
        return os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        return


def consecutive_filename(filename):
    """ Find first non-existing filename.  (NOTE: Not atomic.)  """
    if not os.path.exists(filename):
        return filename
    fileparts = filename.rsplit('.', 1)
    if len(fileparts) == 1:
        filebase, fileext = fileparts[0], None
    else:
        filebase, fileext = fileparts
    for i in xrange(1, 9000):
        filetry = '%s__%02d' % (filebase, i)
        if fileext is not None:
            filetry = '%s.%s' % (filetry, fileext)
            if not os.path.exists(filetry):
                return filetry
    raise Exception("Either I'm insane or there's already over 9000 such files.")


def str2hash(s, hlen=8):
    """ Another hash-like func """
    fmt = '%0{}x'.format(hlen)
    res = fmt % (abs(hash(s)),)
    res = res[:hlen]
    return res


def do_scrap_wrongies(
        data_in=_WRONGDATA_LOGFILE,
        debug_out=_OUTDATA_LOGFILE, dirmeta=_DIRDATA_LOGFILE,
        dirsubdir=_DIRSUBDIR):
    # ###  Per wrongdata-logfile (with dl-continuing support)  ###
    log = _log.getChild("do_scrap_wrongies")
    # Assuming the files are not too giant (reasonably enough):
    in_data = unjsl(data_in)
    debug_data_base = unjsl_or_empty(debug_out)
    debug_data = {d['url']: d for d in debug_data_base}
    to_debug = functools.partial(onjsl, debug_out)  # lambda data: onjsl(debug_out, data)
    all_checked_urls = {}
    # to_meta = lambda target_dir, data: onjsl(os.path.join(target_dir, dirmeta), data)
    # ...
    existing_cache = {}  # meta_file -> {url -> rmeta}

    def get_meta_existing(meta_file, cache=existing_cache):
        try:
            return cache[meta_file]
        except KeyError:
            log.debug("Loading meta_existing %r", meta_file)
            meta_existing = {v['url']: v for v in unjsl_or_empty(meta_file)}
            cache[meta_file] = meta_existing
            return meta_existing

    # ...
    for wrongie in in_data:
        # ###  Per reddit link (basically) with possibly several images there  ###
        # Example `wrongie`: {"url": "http://500px.com/photo/29700163",
        #   "target_dir": "/home/hell/files/wp//reddit_earthporn",
        #   "_downloaded": 8, "_filecount": 0, "_filename": "1m90ui"}
        url = wrongie['url']
        if url in debug_data:
            log.log(15, "Already processed wrongie: %r", url)
            continue  # Already processed, presumably.
        log.log(13, "Processing wrongie %r  (%r)", url, wrongie)
        # ...
        target_dir = os.path.join(wrongie['target_dir'], dirsubdir)
        mkdirs(target_dir)
        # ...
        meta_file = os.path.join(target_dir, dirmeta)
        meta_existing = get_meta_existing(meta_file)  # url -> rmeta
        dmeta = dict(wrongie)  # debug-out data
        # ...
        # NOTE: long request-y process.
        try:
            stuff = img_scrap_stuff.do_horrible_things(url, urls_to_skip=all_checked_urls)
        except GetError:
            log.error("Skipping wrongie %r", wrongie)
            continue
        # stuff = ([checked_url, ...], [(image_url, image_data, {'resp': ..., ...}), ...])
        checked_urls, found_images = stuff
        all_checked_urls.update({u: 1 for u in checked_urls})
        dd_processed = debug_data.setdefault('processed', [])
        for imgurl, imgdata, extras in found_images:
            # ###  Per image file (known to be large)  ###
            if imgurl in meta_existing:
                log.log(14, "Probably already saved: %r", imgurl)
                #continue  # Actually, whatever
            log.log(12, "   ... %r", imgurl)
            # NOTE: will be duplicated on each line.
            rmeta = dict(base=wrongie)  # dirmeta-out data
            resp = extras.get('resp')
            filename_img = make_filename(imgurl, imgdata, resp=resp)
            # per-`url` small hash
            filename_group = wrongie.get('_filename', str2hash(url, 8))
            # NOTE: numeric-annotation would not make sense as found_images is url-sorted.
            filename = '%s__%s' % (filename_group, filename_img)
            filename_full = os.path.join(target_dir, filename)
            # For uniqueness (non-overwriting), assuming we don't try to re-download stuff.
            filename_target = consecutive_filename(filename_full)
            _exdata = dict(filename_base=filename, filename=filename_target, url=imgurl)
            rmeta.update(_exdata)
            with AtomicFile(filename_target) as f:
                f.write(imgdata)
            # ...
            onjsl(meta_file, rmeta)
            meta_existing[imgurl] = rmeta  # make sure we don't try it again
            # Note: might be lost (as rmeta is written already but dmeta isn't yet)
            dd_processed.append(dict(_exdata))
        # Per reddit link again (after downloading all images is done)
        # Write it down so we don't pester it again
        dmeta.update(processed=dd_processed)
        debug_data[url] = dmeta
        to_debug(dmeta)
    # Per wrongdata-logfile again. Nothing to do here after all that.
    log.info("Done, apparently")
    return locals()  # In case some post-debug is desired.


def main():
    try:
        import pyaux.runlib
        pyaux.runlib.init_logging(level=1)
        pyaux.use_exc_ipdb()
    except Exception:
        pass
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(21)
    res = do_scrap_wrongies()
    return


if __name__ == '__main__':
    sys.exit(main())
