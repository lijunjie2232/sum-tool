"""Pytest tests for multi-threading functionality."""

import os
import tempfile
import shutil
import pytest
from pathlib import Path

from sumtool.calculator import (
    calculate_checksums,
    calculate_file_hash,
    SUPPORTED_ALGORITHMS,
)
from sumtool.verifier import verify_checksums


@pytest.fixture
def large_test_directory():
    """Create a directory with multiple files for multi-threading tests."""
    test_dir = tempfile.mkdtemp()
    
    # Create 20 files of varying sizes
    for i in range(20):
        file_path = os.path.join(test_dir, f"file_{i:03d}.bin")
        # Create files from 100KB to 500KB
        size = (100 + (i % 5) * 100) * 1024
        with open(file_path, 'wb') as f:
            f.write(os.urandom(size))
    
    yield test_dir
    shutil.rmtree(test_dir)


@pytest.fixture
def nested_test_directory():
    """Create a nested directory structure for testing."""
    test_dir = tempfile.mkdtemp()
    
    # Create nested structure
    for i in range(5):
        subdir = os.path.join(test_dir, f"subdir_{i}")
        os.makedirs(subdir)
        
        # Add files in each subdirectory
        for j in range(3):
            file_path = os.path.join(subdir, f"nested_file_{j}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Content {i}-{j}" * 100)
    
    yield test_dir
    shutil.rmtree(test_dir)


class TestMultiThreadCalculation:
    """Test cases for multi-threaded checksum calculation."""

    def test_single_thread_vs_multi_thread(self, large_test_directory):
        """Test that single-thread and multi-thread produce same results."""
        # Calculate with single thread
        result_single = calculate_checksums(
            [large_test_directory],
            algorithm="sha256",
            threads=1
        )
        
        # Calculate with multiple threads
        result_multi = calculate_checksums(
            [large_test_directory],
            algorithm="sha256",
            threads=4
        )
        
        # Results should be identical
        assert len(result_single) == len(result_multi)
        
        # Sort both by path for comparison
        result_single_sorted = sorted(result_single, key=lambda x: x[1])
        result_multi_sorted = sorted(result_multi, key=lambda x: x[1])
        
        for (hash1, path1), (hash2, path2) in zip(result_single_sorted, result_multi_sorted):
            assert hash1 == hash2
            assert path1 == path2

    def test_different_thread_counts(self, large_test_directory):
        """Test calculation with different thread counts."""
        thread_counts = [1, 2, 4, 8]
        reference_result = None
        
        for threads in thread_counts:
            result = calculate_checksums(
                [large_test_directory],
                algorithm="sha256",
                threads=threads
            )
            
            if reference_result is None:
                reference_result = result
            else:
                # All results should match
                assert len(result) == len(reference_result)
                result_sorted = sorted(result, key=lambda x: x[1])
                ref_sorted = sorted(reference_result, key=lambda x: x[1])
                
                for (h1, p1), (h2, p2) in zip(result_sorted, ref_sorted):
                    assert h1 == h2

    def test_all_algorithms_multithreaded(self, large_test_directory):
        """Test all hash algorithms with multi-threading."""
        for algorithm in SUPPORTED_ALGORITHMS.keys():
            result = calculate_checksums(
                [large_test_directory],
                algorithm=algorithm,
                threads=4
            )
            
            # Should have checksums for all files
            assert len(result) == 20
            
            # Verify hash lengths
            hash_length_map = {
                "md5": 32,
                "sha1": 40,
                "sha256": 64,
                "sha512": 128
            }
            expected_length = hash_length_map[algorithm]
            
            for hash_value, _ in result:
                assert len(hash_value) == expected_length

    def test_sorted_output(self, large_test_directory):
        """Test that output is sorted by path regardless of thread count."""
        result = calculate_checksums(
            [large_test_directory],
            algorithm="sha256",
            threads=4
        )
        
        # Extract paths
        paths = [path for _, path in result]
        
        # Verify paths are sorted
        assert paths == sorted(paths)

    def test_nested_directories_multithreaded(self, nested_test_directory):
        """Test multi-threaded calculation with nested directories."""
        result = calculate_checksums(
            [nested_test_directory],
            algorithm="sha256",
            threads=4
        )
        
        # Should have 5 subdirs * 3 files = 15 files
        assert len(result) == 15
        
        # Verify all paths contain subdir information
        for _, path in result:
            assert "subdir_" in path

    def test_empty_directory_multithreaded(self):
        """Test multi-threaded calculation on empty directory."""
        test_dir = tempfile.mkdtemp()
        try:
            result = calculate_checksums(
                [test_dir],
                algorithm="sha256",
                threads=4
            )
            assert len(result) == 0
        finally:
            shutil.rmtree(test_dir)

    def test_exclude_patterns_multithreaded(self, large_test_directory):
        """Test that exclude patterns work with multi-threading."""
        # Create some files to exclude
        for i in range(5):
            tmp_file = os.path.join(large_test_directory, f"temp_{i}.tmp")
            with open(tmp_file, 'w') as f:
                f.write("temporary")
        
        result = calculate_checksums(
            [large_test_directory],
            algorithm="sha256",
            exclude_patterns=["*.tmp"],
            threads=4
        )
        
        # Should only have original 20 files
        assert len(result) == 20
        
        # Verify no .tmp files in results
        for _, path in result:
            assert not path.endswith('.tmp')

    def test_large_file_multithreaded(self):
        """Test multi-threaded calculation with large files."""
        test_dir = tempfile.mkdtemp()
        try:
            # Create a 5MB file
            large_file = os.path.join(test_dir, "large_file.bin")
            with open(large_file, 'wb') as f:
                f.write(os.urandom(5 * 1024 * 1024))
            
            # Calculate with different thread counts
            for threads in [1, 4]:
                result = calculate_checksums(
                    [test_dir],
                    algorithm="sha256",
                    threads=threads
                )
                assert len(result) == 1
                assert len(result[0][0]) == 64  # SHA256 length
        finally:
            shutil.rmtree(test_dir)

    @pytest.mark.parametrize("threads", [1, 2, 4, 8, 16])
    def test_various_thread_counts(self, large_test_directory, threads):
        """Parameterized test for various thread counts."""
        result = calculate_checksums(
            [large_test_directory],
            algorithm="sha256",
            threads=threads
        )
        
        # Should always get same number of files
        assert len(result) == 20
        
        # All hashes should be valid SHA256
        for hash_value, _ in result:
            assert len(hash_value) == 64
            assert all(c in '0123456789abcdef' for c in hash_value)


class TestMultiThreadVerification:
    """Test cases for multi-threaded verification."""

    @pytest.fixture
    def verification_setup(self, large_test_directory):
        """Setup for verification tests."""
        # Generate checksums
        sum_file = os.path.join(large_test_directory, "checksums.sum")
        calculate_checksums(
            [large_test_directory],
            algorithm="sha256",
            output_file=sum_file,
            threads=1
        )
        
        return {
            'dir': large_test_directory,
            'sum_file': sum_file
        }

    def test_verify_single_vs_multi_thread(self, verification_setup):
        """Test that single and multi-thread verification produce same results."""
        # Verify with single thread
        results_single = verify_checksums(
            verification_setup['dir'],
            verification_setup['sum_file'],
            threads=1
        )
        
        # Verify with multiple threads
        results_multi = verify_checksums(
            verification_setup['dir'],
            verification_setup['sum_file'],
            threads=4
        )
        
        # Should have same number of results
        assert len(results_single) == len(results_multi)
        
        # All should be OK
        for result in results_single:
            assert result.status == 'OK'
        
        for result in results_multi:
            assert result.status == 'OK'

    def test_verify_modified_file_multithreaded(self, verification_setup):
        """Test multi-threaded verification detects modified files."""
        # Modify one file
        files = os.listdir(verification_setup['dir'])
        non_sum_files = [f for f in files if not f.endswith('.sum')]
        
        if non_sum_files:
            modify_file = os.path.join(verification_setup['dir'], non_sum_files[0])
            with open(modify_file, 'wb') as f:
                f.write(b"modified content")
            
            results = verify_checksums(
                verification_setup['dir'],
                verification_setup['sum_file'],
                threads=4
            )
            
            # Should have one FAILED
            failed_results = [r for r in results if r.status == 'FAILED']
            assert len(failed_results) == 1

    def test_verify_missing_file_multithreaded(self, verification_setup):
        """Test multi-threaded verification detects missing files."""
        # Remove one file
        files = os.listdir(verification_setup['dir'])
        non_sum_files = [f for f in files if not f.endswith('.sum')]
        
        if non_sum_files:
            remove_file = os.path.join(verification_setup['dir'], non_sum_files[0])
            os.remove(remove_file)
            
            results = verify_checksums(
                verification_setup['dir'],
                verification_setup['sum_file'],
                threads=4
            )
            
            # Should have one MISSING
            missing_results = [r for r in results if r.status == 'MISSING']
            assert len(missing_results) == 1

    @pytest.mark.parametrize("threads", [1, 2, 4])
    def test_verify_different_thread_counts(self, verification_setup, threads):
        """Test verification with different thread counts."""
        results = verify_checksums(
            verification_setup['dir'],
            verification_setup['sum_file'],
            threads=threads
        )
        
        # All files should verify successfully
        for result in results:
            assert result.status == 'OK'


class TestEdgeCases:
    """Edge case tests for multi-threading."""

    def test_zero_threads_fallback(self, large_test_directory):
        """Test that 0 or negative threads fallback to single-thread."""
        # These should not crash and should produce valid results
        for threads in [0, -1]:
            result = calculate_checksums(
                [large_test_directory],
                algorithm="sha256",
                threads=threads
            )
            assert len(result) == 20

    def test_very_high_thread_count(self, large_test_directory):
        """Test with very high thread count (more than files)."""
        result = calculate_checksums(
            [large_test_directory],
            algorithm="sha256",
            threads=100  # More threads than files
        )
        
        # Should still work correctly
        assert len(result) == 20
        for hash_value, _ in result:
            assert len(hash_value) == 64

    def test_single_file_multithreaded(self):
        """Test multi-threaded calculation with single file."""
        test_dir = tempfile.mkdtemp()
        try:
            file_path = os.path.join(test_dir, "single.txt")
            with open(file_path, 'w') as f:
                f.write("single file content")
            
            result = calculate_checksums(
                [test_dir],
                algorithm="sha256",
                threads=4
            )
            
            assert len(result) == 1
        finally:
            shutil.rmtree(test_dir)
