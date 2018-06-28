# Much of the content of this file is copied from the
# setup.py of the (open-source) PyPA sample project at
# https://github.com/pypa/sampleproject/blob/master/setup.py

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='qiimp',

    # Versions should comply with PEP440.
    version='0.3',

    description='Software to guide users through generating metadata templates for the Center for Microbiome Innovation',
    long_description=long_description,

    # The project's main homepage.
    url="https://github.com/ucsd-ccbb/qiimp",

    # Author details
    author='The Center for Computational Biology and Bioinformatics',
    author_email='abirmingham@ucsd.edu',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Medical Science Apps.'

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language:: Python:: 3:: Only',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    # What does your project relate to?
    keywords='microbiome screening bioinformatics',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # ,
    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed, although this can be overridden with a requirements.txt file
    install_requires=['openpyxl', 'tornado', 'xlsxwriter', 'PyYAML', 'pandas'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    package_data={
        'qiimp': [
            '*.*',
            'output/*.*',
            'client_scripts/*.*',
            'settings/*.*',
            'settings/packages/*.*',
            'templates/*.*',
            # man, I *hate* that there's no way to do recursive directory inclusion with package_data!
            'third-party/*.*',
            'third-party/bootstrap-3.3.7-dist/css/*.*',
            'third-party/bootstrap-3.3.7-dist/fonts/*.*',
            'third-party/bootstrap-3.3.7-dist/js/*.*',
            'third-party/jQuery-File-Upload-9.19.2/cors/*.*',
            'third-party/jQuery-File-Upload-9.19.2/css/*.*',
            'third-party/jQuery-File-Upload-9.19.2/img/*.*',
            'third-party/jQuery-File-Upload-9.19.2/js/*.*',
            'third-party/jQuery-File-Upload-9.19.2/js/cors/*.*',
            'third-party/jQuery-File-Upload-9.19.2/js/vendor/*.*',
            # I am leaving out the server and test sub-folders on the theory I don't need them for deployment ...
            'third-party/jquery-ui-1.12.1/external/jquery/*.*',
            'third-party/jquery-ui-1.12.1/images/*.*',
            'third-party/jquery-ui-1.12.1/*.*',
            'third-party/jquery_validation/*.*',
        ]
    },

    # I'm transferring package data with the install, which I then need to relocate.
    # This is harder to do if the data is zipped up in an egg, so no zipping!
    zip_safe=False,

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'start_qiimp_server=qiimp.metadata_wizard_server:main'
        ]
    }
)