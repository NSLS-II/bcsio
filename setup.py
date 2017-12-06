
import pathlib

import setuptools


docs_requires = ["sphinx"]
tests_requires = ['pytest>=3.0.0', 'pytest-asyncio', 'pytest-tornasync']
aiohttp_requires = ["aiohttp"]

long_description = pathlib.Path("README.rst").read_text("utf-8")

setuptools.setup(
    name="bcsio",
    version="0.0.1",
    description="An async Basecamp API library",
    long_description=long_description,
    url="https://gidgethub.readthedocs.io",
    author="Thomas A Caswell",
    author_email="tcaswell@bnl.gov",
    license="BSD",
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
    ],
    keywords="basecamp sans-io async",
    packages=setuptools.find_packages(),
    zip_safe=True,
    python_requires=">=3.6.0",
    setup_requires=['pytest-runner>=2.11.0'],
    tests_require=tests_requires,
    install_requires=['uritemplate>=3.0.0'],
    extras_require={
        "docs": docs_requires,
        "tests": tests_requires,
        "aiohttp": aiohttp_requires,
        "dev": (docs_requires + tests_requires + aiohttp_requires),
    },
)
