# coding: utf8
"""
The 'plugin' manager.
"""

import logging
import importlib

_log = logging.getLogger(__name__)


plugin_modules = (
    # '.imgur',
    '.redditupload',
    # '.imgur_basic',
    # '.catchall',
    # '.catchall_basic',
)


def get_plugins_base(context=None):
    """ Returns a list of instances/somethings with 'match' and 'download' methods """
    result = []
    package = __name__.rsplit('.', 1)[0]
    for plugin_modname in plugin_modules:
        try:
            print(__name__)
            mod = importlib.import_module(plugin_modname, package=package)
            plugin_cls = mod.Plugin
            plugin = plugin_cls(context)
        except Exception as exc:
            _log.error("Error importing plugin %r: %r", plugin_modname, exc)
        else:
            result.append(plugin)
    return result


plugins = None

def get_plugins_cached(**kwargs):
    global plugins
    if plugins is not None:
        return plugins
    plugins = get_plugins_base(**kwargs)
    return plugins


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
