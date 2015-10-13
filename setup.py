#!/usr/bin/env python
# coding: utf8

import os
from setuptools import setup


here = os.path.dirname(__file__)
with open(os.path.join(here, 'readme.md')) as _fo:
    LONG_DESCRIPTION = _fo.read()


setup_kwargs = dict(
    name='redditdownload',
    version='1.5',
    description='',  ## XX
    long_description=LONG_DESCRIPTION,
    # classifiers=[],
    # keywords='...,...',
    author='HoverHell',
    author_email='hoverhell@gmail.com',
    url='https://github.com/HoverHell/RedditImageGrab',
    packages=['redditdownload'],
    entry_points={
        'console_scripts': [
            'redditdl.py = redditdownload.redditdownload:main',
        ],
    },
    install_requires=[
        # Actually, most of the dependencies are optional.
    ],
    extras_require={
        'recommended': [
            'beautifulsoup4', 'lxml', 'html5lib',
            'requests',
            'Pillow', 'python-magic',
            'pyaux', 'yaml', 'ipython', 'atomicfile',
        ],
    }
)


if __name__ == '__main__':
    setup(**setup_kwargs)
