try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

from codecs import open
from os import path
import os
import subprocess

config = {

}

current_path = os.getcwd()
try:
    GIT_VERSION = subprocess.check_output(["git", "describe", "--tags"]).strip().decode('utf-8')
    GIT_VERSION = GIT_VERSION.split('-')[0]
except subprocess.CalledProcessError as e:
    GIT_VERSION = "0.1"
os.chdir(current_path)

print(GIT_VERSION)

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(description='neuro time series handling utilities',
      long_description=long_description,
      url='https://github.com/MemDynLab/neuroseries',
      author='Francesco P. Battaglia',
      author_email='fpbattaglia@gmail.com',
      version=GIT_VERSION,
      license='GPL3',
      install_requires=['numpy', 'pandas', 'scipy', 'parameterized'],
      packages=find_packages(),
      package_data={'resources': ['resources/*.*']},
      include_package_data=True,
      test_suite='nose.collector',
      tests_require=['nose'],
      name='neuroseries',
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3 :: Only',
            'Topic :: Scientific/Engineering :: Bio-Informatics'
      ]
      )
