#!/usr/bin/env python
from setuptools import setup, find_packages
import tonplace

setup(name='tonplace-api',
      version=tonplace.__version__,
      description='Python Distribution Utilities',
      author='0x216',
      author_email='0x216@pm.me',
      url='https://www.python.org/sigs/distutils-sig/https://github.com/0x216/tonplace-api',
      packages=find_packages(),
      long_description=open("README.md", encoding="utf-8").read(),
      install_requires=["aiohttp", "aiodns", "aiohttp-socks", "cchardet", "aiohttp[speedups]"],
     )