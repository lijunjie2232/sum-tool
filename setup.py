"""Setup configuration for sumtool package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sum-tool",
    version="0.2.0",
    author="lijunjie2232",
    author_email="li2533584225@gmail.com",
    description="A tool for calculating and verifying file checksums",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lijunjie2232/sum-tool",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Security :: Cryptography",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "sumtool=sumtool.cli:main",
        ],
    },
    keywords="checksum hash md5 sha1 sha256 sha512 verification security",
)
