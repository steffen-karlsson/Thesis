#!/usr/bin/env python

from setuptools import setup, find_packages

import bdae

install_requires = [
    'Pyro4',
    'tornado',
    'ujson',
    'apscheduler',
]

setup(
    name='bdae',
    version=bdae.__version__,
    description=bdae.__doc__,
    url='https://github.com/steffenkarlsson/Thesis',
    download_url='https://github.com/steffenkarlsson/Thesis',
    author=bdae.__author__,
    author_email='ckh340@alumni,ku.dk',
    license=bdae.__licence__,
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "bdae.web": [
            "index.html",
            "static/custom.js",
            "static/custom.css",
            "static/bootstrap.min.css",
            "static/bootstrap.min.js",
            "static/bootstrap-dialog.min.css",
            "static/bootstrap-dialog.min.js",
            "static/jumbotron-narrow.css",
            "static/glyphicons-halflings-regular.ttf"
        ],
        "bdae.web.docs": [
            "conf.py",
            "Makefile",
            "configparser.rst",
            "absdatasetcontext.rst",
            "libbdaeadmin.rst",
            "index.rst"
        ]
    },
    install_requires=install_requires,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU LESSER GENERAL PUBLIC LICENSE Version 3',
        'Topic :: Software Development',
        'Topic :: Terminals',
        'Topic :: Utilities'
    ],
)
