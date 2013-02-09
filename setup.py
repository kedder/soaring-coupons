#!/usr/bin/python
###############################################################################
#
# Copyright 2011 by CipherHealth, LLC
#
###############################################################################
"""Setup
"""
from setuptools import setup, find_packages


with open('README.md') as f:
    long_description = f.read()

setup(
      name='soaringcoupons',
      version='1.0.0',
      author = "Andrey Lebedev",
      author_email = "andrey@lebedev.lt",
      url = "https://github.com/kedder/soaring-coupons",
      description = ("Simple app for selling soaring coupons, based on google app engine"),
      long_description = long_description,
      license = "GPLv3",
      keywords = ["soaring", "coupons", "gae"],
      classifiers = ['Development Status :: 5 - Production/Stable',
                     'Programming Language :: Python :: 2.7',
                     'Natural Language :: Lithuanian',
                     'License :: OSI Approved :: GNU Affero General Public License v3'
                     ],
      packages = find_packages('src'),
      package_dir = {'':'src'},
      extras_require = dict(test=['mock', 'webtest']),
      install_requires = ['setuptools',
                          'Pillow',
                          'jinja2',
                          'webapp2',
                          'qrcode'
                          ],
      include_package_data = True,
      zip_safe = False
      )
