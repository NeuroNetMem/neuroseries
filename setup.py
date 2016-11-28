try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {

}

setup(description='neuro time series handling utilities',
      author='Francesco P. Battaglia',
      author_email='fpbattaglia@gmail.com',
      version='0.1',
      license='MIT',
      install_requires=['numpy', 'pandas', 'scipy', 'IPython', 'psutil'],
      packages=['neuroseries'],
      package_data={'resources': ['resources/*.*']},
      include_package_data=False,
      name='neuroseries'
      )
