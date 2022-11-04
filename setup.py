# adapted over https://github.com/pypa/sampleproject/blob/master/setup.py

from setuptools import setup, find_packages
from os import path
import gallery_generator

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

with open(path.join(here, 'requirements/requirements.in')) as f:
    requirements = f.readlines()

with open(path.join(here, 'requirements/requirements-dev.in')) as f:
    requirements_dev = f.readlines()[1:]

setup(
    name='gallery_generator',
    version=gallery_generator.__version__,

    # Description
    description=gallery_generator.__doc__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='website',

    project_urls={
        'Bug Reports': 'https://github.com/pierre-24/pics.pierrebeaujean.net/issues',
        'Source': 'https://github.com/pics.pierrebeaujean.net/gallery_generator/',
    },

    author='Pierre Beaujean',

    # Classifiers
    classifiers=[
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions:
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],

    packages=find_packages(),
    python_requires='>=3.8',

    include_package_data=True,

    # requirements
    install_requires=requirements,

    extras_require={  # Optional
        'dev': requirements_dev,
    },

    entry_points={
        'console_scripts': [
        ]
    },
)