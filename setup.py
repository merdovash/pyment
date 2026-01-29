#!/usr/bin/env python

from setuptools import setup, find_packages
from os import path
import pyment


curr_dir = path.abspath(path.dirname(__file__))

with open(path.join(curr_dir, "README.rst")) as f:
    long_desc = f.read()


setup(name='Pyment',
      version=pyment.__version__,
      description='Generate/convert automatically the docstrings from code signature',
      long_description=long_desc,
      long_description_content_type="text/x-rst",
      author='A. Daouzli',
      author_email='dadel@hadoly.fr',
      license='GPLv3',
      maintainer='V. Schekochihin',
      maintainer_email='merd888888@gmail.com',
      keywords="pyment docstring numpydoc googledoc restructuredtext epydoc epytext javadoc development generate auto",
      platforms=['any'],
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Documentation',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.no_spec_full_comment',
          'Programming Language :: Python :: 3.11',
          ],
      url='https://github.com/merdovash/pyment',
      packages=find_packages(),
      test_suite='tests.test_all',
      entry_points={
        'console_scripts': [
            'pyment = pyment.pymentapp:main'
            ]
        },
      )
