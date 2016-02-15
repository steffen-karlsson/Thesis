#!/usr/bin/env python

from setuptools import setup, find_packages

import bdos

install_requires = [
    'Pyro4',
    'tornado',
]

setup(
    name='bdos',
    version=bdos.__version__,
    description=bdos.__doc__,
    url='https://github.com/steffenkarlsson/Thesis',
    download_url='https://github.com/steffenkarlsson/Thesis',
    author=bdos.__author__,
    author_email='ckh340@alumni,ku.dk',
    license=bdos.__licence__,
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "bdos.web": [
            "index.html",
            "static/custom.js",
            "static/custom.css",
            "static/bootstrap.min.css",
            "static/jumbotron-narrow.css",
            "static/general-overview.png"
        ],
        "bdos.web.docs": [
            "conf.py",
            "Makefile",
            "configparser.rst",
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
