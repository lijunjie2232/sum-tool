"""
sumtool - A Python tool for calculating and verifying file checksums.

Supports MD5, SHA1, SHA256, and SHA512 hash algorithms.
"""

__version__ = "0.2.0"
__author__ = "lijunjie2232"

from .calculator import calculate_checksums
from .verifier import verify_checksums

__all__ = ["calculate_checksums", "verify_checksums"]
