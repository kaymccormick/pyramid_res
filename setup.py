##############################################################################
#
#
##############################################################################

import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
if sys.version_info[0] > 2:
    README = open(os.path.join(here, 'README.rst'), encoding="utf-8").read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt'), encoding="utf-8").read()
else:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid>=1.3.0', # pyramid.path.DottedNameResolver
]

try:
    import wsgiref
except ImportError:
    requires.append('wsgiref')

testing_extras = [
    'coverage',
    'nose>=1.2.0',
    'WebTest',
]
docs_extras = [
    'pylons-sphinx-themes >= 0.3',
    'Sphinx>=1.7.5',
]

setup(name='pyramid_res',
      version='0.1',
      description='pyramid resource management',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Framework :: Pyramid",
        "License :: Repoze Public License",
        ],
      keywords='web wsgi pylons pyramid jinja2',
      author="Kay McCormick",
      author_email="kay@heptet.us",
      maintainer="Kay McCormick",
      maintainer_email="kay@heptet.us",
      url="https://github.com/kaymccormick/pyramid_res",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      extras_require = {
          'testing':testing_extras,
          'docs':docs_extras,
          },
      tests_require=requires + ['WebTest'],
      test_suite="pyramid_jinja2.tests",
      entry_points="""
      """,
      )
