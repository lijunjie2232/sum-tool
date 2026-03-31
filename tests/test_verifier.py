"""Pytest-style tests for the verifier module."""

import os
import tempfile
import shutil
import pytest
from pathlib import Path

from sumtool.calculator import calculate_checksums
from sumtool.verifier import (
    verify_single_file,
    verify_checksums,
    detect_algorithm,
    VerificationResult,
)
from sumtool.utils import write_sum_file


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
def verification_test_setup(test_dir):
    """Create a directory with files and checksums for verification testing."""
    file1 = os.path.join(test_dir, "file1.txt")
    file2 = os.path.join(test_dir, "file2.txt")
    
    with open(file1, 'w') as f:
        f.write("Content 1")
    with open(file2, 'w') as f:
        f.write("Content 2")
    
    # Generate checksums file
    sum_file = os.path.join(test_dir, "checksums.sum")
    calculate_checksums(
        [test_dir],
        algorithm="sha256",
        output_file=sum_file
    )
    
    return {
        'dir': test_dir,
        'file1': file1,
        'file2': file2,
        'sum_file': sum_file
    }


class TestVerifySingleFile:
    """Test cases for verify_single_file function."""

    def test_verify_success(self, test_file_with_content):
        """Test successful verification."""
        expected_hash = "65a8e27d8879283831b664bd8b7f0ad4"  # MD5 of "Hello, World!"
        result = verify_single_file(test_file_with_content, expected_hash, "md5")
        
        assert result.status == 'OK'
        assert result.expected == expected_hash
        assert result.actual is not None

    def test_verify_failure(self, test_file_with_content):
        """Test failed verification with wrong hash."""
        wrong_hash = "00000000000000000000000000000000"
        result = verify_single_file(test_file_with_content, wrong_hash, "md5")
        
        assert result.status == 'FAILED'
        assert result.error_message == "Checksum mismatch"

    def test_verify_missing_file(self, test_dir):
        """Test verification of missing file."""
        missing_file = os.path.join(test_dir, "nonexistent.txt")
        result = verify_single_file(missing_file, "somehash", "md5")
        
        assert result.status == 'MISSING'
        assert result.error_message == "File not found"

    def test_verify_result_attributes(self, test_file_with_content):
        """Test that VerificationResult has all expected attributes."""
        expected_hash = "65a8e27d8879283831b664bd8b7f0ad4"
        result = verify_single_file(test_file_with_content, expected_hash, "md5")
        
        assert hasattr(result, 'filepath')
        assert hasattr(result, 'expected')
        assert hasattr(result, 'actual')
        assert hasattr(result, 'status')
        assert hasattr(result, 'error_message')
        
        assert result.filepath == test_file_with_content
        assert result.expected == expected_hash
        assert result.actual == expected_hash  # Should match for successful verification
        assert result.status == 'OK'
        assert result.error_message is None


class TestDetectAlgorithm:
    """Test cases for detect_algorithm function."""

    def test_detect_md5(self):
        """Test MD5 detection from hash length."""
        checksums = [("65a8e27d8879283831b664bd8b7f0ad4", "file.txt")]
        algorithm = detect_algorithm(checksums)
        assert algorithm == "md5"

    def test_detect_sha1(self):
        """Test SHA1 detection from hash length."""
        sha1_hash = "a" * 40
        checksums = [(sha1_hash, "file.txt")]
        algorithm = detect_algorithm(checksums)
        assert algorithm == "sha1"

    def test_detect_sha256(self):
        """Test SHA256 detection from hash length."""
        sha256_hash = "a" * 64
        checksums = [(sha256_hash, "file.txt")]
        algorithm = detect_algorithm(checksums)
        assert algorithm == "sha256"

    def test_detect_sha512(self):
        """Test SHA512 detection from hash length."""
        sha512_hash = "a" * 128
        checksums = [(sha512_hash, "file.txt")]
        algorithm = detect_algorithm(checksums)
        assert algorithm == "sha512"

    def test_detect_default(self):
        """Test default to SHA256 when no checksums provided."""
        algorithm = detect_algorithm([])
        assert algorithm == "sha256"

    @pytest.mark.parametrize("hash_value,expected_algo", [
        ("65a8e27d8879283831b664bd8b7f0ad4", "md5"),
        ("a" * 40, "sha1"),
        ("a" * 64, "sha256"),
        ("a" * 128, "sha512"),
    ])
    def test_detect_all_algorithms(self, hash_value, expected_algo):
        """Test detection of all supported algorithms."""
        checksums = [(hash_value, "file.txt")]
        algorithm = detect_algorithm(checksums)
        assert algorithm == expected_algo


class TestVerifyChecksums:
    """Test cases for verify_checksums function."""

    def test_verify_all_files_present(self, verification_test_setup):
        """Test verification when all files are present and unchanged."""
        results = verify_checksums(
            verification_test_setup['dir'],
            verification_test_setup['sum_file']
        )
        
        # All files should verify successfully
        for result in results:
            assert result.status == 'OK', \
                f"File {result.filepath} failed: {result.error_message}"

    def test_verify_file_modified(self, verification_test_setup):
        """Test verification when a file has been modified."""
        # Modify one of the files
        with open(verification_test_setup['file1'], 'w') as f:
            f.write("Modified content")
        
        results = verify_checksums(
            verification_test_setup['dir'],
            verification_test_setup['sum_file']
        )
        
        # Find the result for file1.txt
        file1_result = next(r for r in results if 'file1.txt' in r.filepath)
        assert file1_result.status == 'FAILED'
        assert file1_result.error_message == "Checksum mismatch"

    def test_verify_file_missing(self, verification_test_setup):
        """Test verification when a file is missing."""
        # Remove one of the files
        os.remove(verification_test_setup['file1'])
        
        results = verify_checksums(
            verification_test_setup['dir'],
            verification_test_setup['sum_file']
        )
        
        # Find the result for file1.txt
        file1_result = next(r for r in results if 'file1.txt' in r.filepath)
        assert file1_result.status == 'MISSING'
        assert file1_result.error_message == "File not found"

    def test_verify_auto_find_sum_file(self, verification_test_setup):
        """Test that .sum file is automatically found in directory."""
        results = verify_checksums(verification_test_setup['dir'])
        
        # Should find the checksums.sum file and verify
        assert len(results) > 0

    def test_verify_returns_correct_counts(self, verification_test_setup):
        """Test that verification returns correct result counts."""
        # Modify one file and remove another
        with open(verification_test_setup['file1'], 'w') as f:
            f.write("Modified")
        os.remove(verification_test_setup['file2'])
        
        results = verify_checksums(
            verification_test_setup['dir'],
            verification_test_setup['sum_file']
        )
        
        # Count results by status
        ok_count = sum(1 for r in results if r.status == 'OK')
        failed_count = sum(1 for r in results if r.status == 'FAILED')
        missing_count = sum(1 for r in results if r.status == 'MISSING')
        
        assert ok_count == 0
        assert failed_count == 1
        assert missing_count == 1


class TestVerificationResults:
    """Test VerificationResult dataclass."""

    def test_create_ok_result(self):
        """Test creating a successful verification result."""
        result = VerificationResult(
            filepath="/path/to/file.txt",
            expected="abc123",
            actual="abc123",
            status='OK'
        )
        
        assert result.filepath == "/path/to/file.txt"
        assert result.expected == "abc123"
        assert result.actual == "abc123"
        assert result.status == 'OK'
        assert result.error_message is None

    def test_create_failed_result(self):
        """Test creating a failed verification result."""
        result = VerificationResult(
            filepath="/path/to/file.txt",
            expected="abc123",
            actual="def456",
            status='FAILED',
            error_message="Checksum mismatch"
        )
        
        assert result.status == 'FAILED'
        assert result.error_message == "Checksum mismatch"

    def test_create_missing_result(self):
        """Test creating a missing file result."""
        result = VerificationResult(
            filepath="/path/to/missing.txt",
            expected="abc123",
            actual=None,
            status='MISSING',
            error_message="File not found"
        )
        
        assert result.status == 'MISSING'
        assert result.actual is None
        assert result.error_message == "File not found"


class TestIntegration:
    """Integration tests for the verification workflow."""

    def test_full_workflow(self, test_dir):
        """Test complete calc -> modify -> verify workflow."""
        # Create files
        file1 = os.path.join(test_dir, "original.txt")
        with open(file1, 'w') as f:
            f.write("Original content")
        
        # Calculate checksums
        sum_file = os.path.join(test_dir, "checksums.sum")
        calculate_checksums([test_dir], output_file=sum_file)
        
        # Verify original - should pass
        results = verify_checksums(test_dir, sum_file)
        assert all(r.status == 'OK' for r in results)
        
        # Modify file
        with open(file1, 'w') as f:
            f.write("Modified content")
        
        # Verify again - should fail
        results = verify_checksums(test_dir, sum_file)
        assert any(r.status == 'FAILED' for r in results)

    def test_cross_directory_verification(self, test_dir):
        """Test verifying files using checksums from different location."""
        # Create source directory with files
        source_dir = os.path.join(test_dir, "source")
        os.makedirs(source_dir)
        
        with open(os.path.join(source_dir, "file.txt"), 'w') as f:
            f.write("Test content")
        
        # Generate checksums in source
        sum_file = os.path.join(source_dir, "checksums.sum")
        calculate_checksums([source_dir], output_file=sum_file)
        
        # Copy to destination
        dest_dir = os.path.join(test_dir, "dest")
        shutil.copytree(source_dir, dest_dir, ignore=shutil.ignore_patterns('*.sum'))
        
        # Copy checksums file
        shutil.copy(sum_file, dest_dir)
        
        # Verify in destination - should work because we use relative paths
        results = verify_checksums(dest_dir)
        assert all(r.status == 'OK' for r in results)

    def test_verify_with_explicit_directory_parameter(self, test_dir):
        """Test that explicit directory parameter is used as base path."""
        # Create two directories
        dir1 = os.path.join(test_dir, "dir1")
        dir2 = os.path.join(test_dir, "dir2")
        os.makedirs(dir1)
        os.makedirs(dir2)
        
        # Create same file in both directories
        file1_dir1 = os.path.join(dir1, "file.txt")
        file1_dir2 = os.path.join(dir2, "file.txt")
        
        with open(file1_dir1, 'w') as f:
            f.write("Content 1")
        with open(file1_dir2, 'w') as f:
            f.write("Content 2")
        
        # Generate checksums in dir1
        sum_file = os.path.join(dir1, "checksums.sum")
        calculate_checksums([dir1], output_file=sum_file)
        
        # Verify dir1 with explicit directory parameter - should pass
        results = verify_checksums(dir1, sum_file)
        assert all(r.status == 'OK' for r in results)
        
        # Verify dir2 with explicit directory parameter - should fail (different content)
        results = verify_checksums(dir2, sum_file)
        assert any(r.status == 'FAILED' for r in results)

    def test_verify_directory_parameter_overrides_sum_file_location(self, test_dir):
        """Test that directory parameter takes precedence over .sum file location."""
        # Create directory structure
        base_dir = os.path.join(test_dir, "base")
        target_dir = os.path.join(test_dir, "target")
        os.makedirs(base_dir)
        os.makedirs(target_dir)
        
        # Create file in target
        target_file = os.path.join(target_dir, "file.txt")
        with open(target_file, 'w') as f:
            f.write("Target content")
        
        # Generate checksums and move .sum file to base_dir
        sum_file_in_target = os.path.join(target_dir, "checksums.sum")
        calculate_checksums([target_dir], output_file=sum_file_in_target)
        
        # Move .sum file to base_dir
        sum_file_in_base = os.path.join(base_dir, "checksums.sum")
        shutil.move(sum_file_in_target, sum_file_in_base)
        
        # Verify with explicit directory pointing to target_dir
        # Should use target_dir as base, not base_dir (where .sum file is)
        results = verify_checksums(target_dir, sum_file_in_base)
        assert all(r.status == 'OK' for r in results)
