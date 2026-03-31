"""Pytest-style tests for the calculator module."""

import os
import tempfile
import shutil
import pytest
from pathlib import Path

from sumtool.calculator import (
    calculate_file_hash,
    calculate_checksums,
    SUPPORTED_ALGORITHMS,
)


@pytest.fixture
def test_dir():
    """Create a temporary directory for testing."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def test_file_with_content(test_dir):
    """Create a test file with known content."""
    test_file = os.path.join(test_dir, "test.txt")
    with open(test_file, 'w') as f:
        f.write("Hello, World!")
    return test_file


@pytest.fixture
def multiple_files_dir(test_dir):
    """Create a directory with multiple test files."""
    file1 = os.path.join(test_dir, "file1.txt")
    file2 = os.path.join(test_dir, "file2.txt")
    
    with open(file1, 'w') as f:
        f.write("Content 1")
    with open(file2, 'w') as f:
        f.write("Content 2")
    
    return test_dir


class TestCalculateFileHash:
    """Test cases for calculate_file_hash function."""

    def test_md5_hash(self, test_file_with_content):
        """Test MD5 hash calculation."""
        result = calculate_file_hash(test_file_with_content, "md5")
        # MD5 of "Hello, World!" is 65a8e27d8879283831b664bd8b7f0ad4
        assert result == "65a8e27d8879283831b664bd8b7f0ad4"
        assert len(result) == 32

    def test_sha1_hash(self, test_file_with_content):
        """Test SHA1 hash calculation."""
        result = calculate_file_hash(test_file_with_content, "sha1")
        assert len(result) == 40

    def test_sha256_hash(self, test_file_with_content):
        """Test SHA256 hash calculation."""
        result = calculate_file_hash(test_file_with_content, "sha256")
        # SHA256 of "Hello, World!" is dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f
        assert result == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert len(result) == 64

    def test_sha512_hash(self, test_file_with_content):
        """Test SHA512 hash calculation."""
        result = calculate_file_hash(test_file_with_content, "sha512")
        assert len(result) == 128

    def test_unsupported_algorithm(self, test_file_with_content):
        """Test that unsupported algorithm raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            calculate_file_hash(test_file_with_content, "invalid_algorithm")

    def test_case_insensitive_algorithm(self, test_file_with_content):
        """Test that algorithm names are case-insensitive."""
        result_upper = calculate_file_hash(test_file_with_content, "SHA256")
        result_lower = calculate_file_hash(test_file_with_content, "sha256")
        assert result_upper == result_lower

    def test_nonexistent_file(self):
        """Test that nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            calculate_file_hash("/nonexistent/file.txt", "sha256")


class TestCalculateChecksums:
    """Test cases for calculate_checksums function."""

    def test_single_directory(self, multiple_files_dir):
        """Test checksum calculation for a single directory."""
        checksums = calculate_checksums([multiple_files_dir])
        assert len(checksums) == 2
        
        # Verify format
        for hash_value, rel_path in checksums:
            assert len(hash_value) == 64  # SHA256 hex length
            assert rel_path in ["file1.txt", "file2.txt"]

    def test_multiple_paths(self, multiple_files_dir):
        """Test checksum calculation for multiple paths."""
        dir2 = tempfile.mkdtemp()
        try:
            file3 = os.path.join(dir2, "file3.txt")
            with open(file3, 'w') as f:
                f.write("Content 3")
            
            checksums = calculate_checksums([multiple_files_dir, dir2])
            assert len(checksums) == 3
        finally:
            shutil.rmtree(dir2)

    def test_exclude_pattern(self, multiple_files_dir):
        """Test that exclude patterns work correctly."""
        # Create a file to exclude
        exclude_file = os.path.join(multiple_files_dir, "test.tmp")
        with open(exclude_file, 'w') as f:
            f.write("Temp content")
        
        checksums = calculate_checksums(
            [multiple_files_dir],
            exclude_patterns=["*.tmp"]
        )
        
        # Should only have 2 files (file1.txt and file2.txt)
        assert len(checksums) == 2
        
        # Verify excluded file is not in results
        rel_paths = [rel_path for _, rel_path in checksums]
        assert "test.tmp" not in rel_paths

    def test_output_file(self, multiple_files_dir):
        """Test writing checksums to output file."""
        output_file = os.path.join(multiple_files_dir, "output.sum")
        
        checksums = calculate_checksums(
            [multiple_files_dir],
            output_file=output_file
        )
        
        # Verify file was created
        assert os.path.exists(output_file)
        
        # Verify file content
        with open(output_file, 'r') as f:
            content = f.read()
            assert "# SHA256 checksums" in content
            assert len(checksums) == 2

    def test_different_algorithms(self, multiple_files_dir):
        """Test different hash algorithms."""
        for algorithm in SUPPORTED_ALGORITHMS.keys():
            checksums = calculate_checksums(
                [multiple_files_dir],
                algorithm=algorithm
            )
            assert len(checksums) == 2
            
            # Verify hash length matches algorithm
            hash_length_map = {
                "md5": 32,
                "sha1": 40,
                "sha256": 64,
                "sha512": 128
            }
            expected_length = hash_length_map[algorithm]
            for hash_value, _ in checksums:
                assert len(hash_value) == expected_length


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_directory(self, test_dir):
        """Test checksum calculation on empty directory."""
        checksums = calculate_checksums([test_dir])
        assert len(checksums) == 0

    def test_nested_directories(self, test_dir):
        """Test checksum calculation with nested directories."""
        # Create nested structure
        subdir1 = os.path.join(test_dir, "subdir1")
        subdir2 = os.path.join(test_dir, "subdir1", "subdir2")
        os.makedirs(subdir2)
        
        # Create files at different levels
        with open(os.path.join(test_dir, "root.txt"), 'w') as f:
            f.write("root")
        with open(os.path.join(subdir1, "level1.txt"), 'w') as f:
            f.write("level1")
        with open(os.path.join(subdir2, "level2.txt"), 'w') as f:
            f.write("level2")
        
        checksums = calculate_checksums([test_dir])
        assert len(checksums) == 3
        
        # Check relative paths
        rel_paths = [rel_path for _, rel_path in checksums]
        assert "root.txt" in rel_paths
        assert os.path.join("subdir1", "level1.txt") in rel_paths
        assert os.path.join("subdir1", "subdir2", "level2.txt") in rel_paths

    def test_exclude_nested_directory(self, test_dir):
        """Test excluding nested directory."""
        # Create nested structure
        node_modules = os.path.join(test_dir, "node_modules", "package")
        os.makedirs(node_modules)
        
        with open(os.path.join(test_dir, "app.py"), 'w') as f:
            f.write("print('hello')")
        with open(os.path.join(node_modules, "lib.js"), 'w') as f:
            f.write("module.exports = {}")
        
        checksums = calculate_checksums(
            [test_dir],
            exclude_patterns=["node_modules"]
        )
        
        assert len(checksums) == 1
        assert checksums[0][1] == "app.py"

    def test_large_file_handling(self, test_dir):
        """Test handling of larger files."""
        large_file = os.path.join(test_dir, "large.bin")
        
        # Create a 1MB file
        with open(large_file, 'wb') as f:
            f.write(b'\x00' * (1024 * 1024))
        
        # Should complete without error
        checksums = calculate_checksums([test_dir])
        assert len(checksums) == 1
        assert len(checksums[0][0]) == 64  # SHA256 length

    @pytest.mark.parametrize("algorithm,expected_length", [
        ("md5", 32),
        ("sha1", 40),
        ("sha256", 64),
        ("sha512", 128),
    ])
    def test_algorithm_parameters(self, test_file_with_content, algorithm, expected_length):
        """Test all supported algorithms with parameterized testing."""
        result = calculate_file_hash(test_file_with_content, algorithm)
        assert len(result) == expected_length
