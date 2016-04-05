#!/usr/bin/env python

from setuptools import setup, find_packages

__author__ = 'Steffen Karlsson'
__version__ = '0.1-dev'
__licence__ = 'GNU LESSER GENERAL PUBLIC LICENSE Version 3'
__doc__ = "BDAE"

install_requires = [
    'Pyro4',
    'ujson',
    'tornado'
]

setup(
    name='bdae',
    version=__version__,
    description=__doc__,
    url='https://github.com/steffenkarlsson/Thesis',
    download_url='https://github.com/steffenkarlsson/Thesis',
    author=__author__,
    author_email='ckh340@alumni,ku.dk',
    license=__licence__,
    packages=find_packages(),
    install_requires=install_requires,
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
            "absdatasetcollection.rst",
            "libs.rst",
            "libbdaeadmin.rst",
            "libbdaemanager.rst",
            "libbdaescientist.rst",
            "index.rst",
            "conf.py"
        ]
    },
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
