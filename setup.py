#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (
    setup,
    find_packages,
)

extras_require = {
    'bimini': [
        "parsimonious>=0.8.1,<0.9.0",
        "cytoolz>=0.9.0.1,<0.10",
    ],
    'test': [
        "pytest==4.3.0",
        "pytest-xdist",
        "tox>=2.9.1,<3",
        "hypothesis==4.7.12",
    ],
    'lint': [
        "mypy==0.670",
        "flake8==3.7.7",
        "flake8-bugbear==18.8.0",
        "isort>=4.2.15,<5",
        "pydocstyle>=3.0.0,<4",
    ],
    'doc': [
        "Sphinx>=1.6.5,<2",
        "sphinx_rtd_theme>=0.1.9",
    ],
    'dev': [
        "bumpversion>=0.5.3,<1",
        "pytest-watch>=4.1.0,<5",
        "wheel",
        "twine",
        "ipython",
    ],
}

extras_require['dev'] = (
    extras_require['dev'] +
    extras_require['test'] +
    extras_require['lint'] +
    extras_require['doc']
)

install_requires = extras_require.pop('bimini')


with open('README.md') as readme_file:
    long_description = readme_file.read()


setup(
    name='bimini',
    # *IMPORTANT*: Don't manually change the version here. Use `make bump`, as described in readme
    version='0.1.0-alpha.0',
    description="""bimini: An implementation of the Concise Streamable Serialization Scheme""",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Jason Carver',
    author_email='ethcalibur+pip@gmail.com',
    url='https://github.com/ethereum/bimini',
    include_package_data=True,
    install_requires=install_requires,
    setup_requires=['setuptools-markdown'],
    python_requires='>=3.6, <4',
    extras_require=extras_require,
    py_modules=['bimini'],
    license="MIT",
    zip_safe=False,
    keywords='ethereum',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
