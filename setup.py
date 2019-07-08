#!/usr/bin/env python
import io
from datetime import datetime

from setuptools import find_packages, setup

version = '{}'.format(datetime.now().strftime('%Y-%m-%d-%H_%M_%S_%f'))
setup(
    name='nap',
    version=version,
    description='api access modeling and tools',
    author='Jacob Burch',
    author_email='jacobburch@gmail.com',
    url='https://github.com/jacobb/nap',
    long_description=io.open('README.rst', encoding='utf-8').read(),
    packages=find_packages(),
    zip_safe=False,
    setup_requires=['pytest-runner>=2.0,<3dev'],
    tests_require=[
        'pytest',
        'pytest-cov',
        'Django>=1.8.18',
        'Flask>=0.11.1',
        'Flask-Caching>=1.2.0'
    ],
    install_requires=[
        'requests>=1.2.3'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
)
