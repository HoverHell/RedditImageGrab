# coding: utf8
"""
The 'plugin' manager.
"""

import logging

_log = logging.getLogger(__name__)


def get_plugins(context=None):
    """ Returns a list of instances/somethings with 'match' and 'download' methods """
    result = []
    try:
        from .redditupload import Plugin
    except Exception as exc:
        _log.error("Error importing redditupload: %r", exc)
    else:
        result.append(Plugin(context))
    return result


plugins = get_plugins()

# TODO: allow plugins to figure out the filename and the 'already
# downloaded' cases by themselves.

def download(url, filename=None, **kwargs):
    result = dict(url=url, filename=filename)
    for plugin in plugins:
        if plugin.match(url):
            plugin_result = plugin.download(url, filename=filename, **kwargs)
            result.update(plugin_result or {})
            return result
    return dict(result, error='unknown_url')
