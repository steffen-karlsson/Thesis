#!/usr/bin/env python

from setuptools import find_packages, setup

import bdos

install_requires = [
    'Pyro4'
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
