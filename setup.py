#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='mobai',
    version='0.1',
    description='A very simple moba-inspired game engine for bots',
    long_description=open('README.md', 'r').read(),
    url='https://github.com/eguven/mobai',
    author='Eren Güven',
    author_email='erenguven0@gmail.com',
    license='MIT',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Games/Entertainment',
        'Topic :: Games/Entertainment :: Turn Based Strategy',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries',
    ],
    keywords='game engine bots ai moba',
)
