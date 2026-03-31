"""Pytest tests for stdout output functionality."""

import os
import tempfile
import shutil
import pytest
from io import StringIO
from contextlib import redirect_stdout

from sumtool.calculator import calculate_checksums


@pytest.fixture
def simple_test_directory():
    """Create a simple directory with a few files for testing."""
    test_dir = tempfile.mkdtemp()
    
    # Create 3 simple files
    for name in ['file1.txt', 'file2.txt', 'file3.txt']:
        with open(os.path.join(test_dir, name), 'w') as f:
            f.write(f"content of {name}")
    
    yield test_dir
    shutil.rmtree(test_dir)


class TestStdoutOutput:
    """Test cases for stdout output when no -o parameter is specified."""

    def test_output_to_stdout_without_o_flag(self, simple_test_directory):
        """Test that results are printed to stdout when no -o flag."""
        captured_output = StringIO()
        
        with redirect_stdout(captured_output):
            result = calculate_checksums(
                [simple_test_directory],
                algorithm="sha256",
                threads=1,
                quiet=False
            )
        
        output = captured_output.getvalue()
        
        # Should have header comment
        assert "# SHA256 checksums" in output
        
        # Should have all files
        assert "file1.txt" in output
        assert "file2.txt" in output
        assert "file3.txt" in output
        
        # Should have valid SHA256 hashes (64 hex chars)
        lines = [l for l in output.strip().split('\n') if not l.startswith('#')]
        assert len(lines) == 3
        
        for line in lines:
            parts = line.split('  ', 1)
            assert len(parts) == 2
            hash_value, path = parts
            assert len(hash_value) == 64
            assert all(c in '0123456789abcdef' for c in hash_value)

    def test_quiet_mode_no_output(self, simple_test_directory):
        """Test that quiet mode suppresses stdout output."""
        captured_output = StringIO()
        
        with redirect_stdout(captured_output):
            result = calculate_checksums(
                [simple_test_directory],
                algorithm="sha256",
                threads=1,
                quiet=True
            )
        
        output = captured_output.getvalue()
        
        # Should be empty or only contain the summary comment
        lines = [l for l in output.strip().split('\n') if l]
        assert len(lines) == 0 or (len(lines) == 1 and lines[0].startswith('# Calculated'))

    def test_output_format_matches_standard(self, simple_test_directory):
        """Test that stdout output format matches standard checksum format."""
        captured_output = StringIO()
        
        with redirect_stdout(captured_output):
            result = calculate_checksums(
                [simple_test_directory],
                algorithm="sha256",
                threads=1,
                quiet=False
            )
        
        output = captured_output.getvalue()
        lines = [l for l in output.strip().split('\n') if l and not l.startswith('# Calculated')]
        
        # First line should be header comment
        assert lines[0] == "# SHA256 checksums"
        
        # Remaining lines should be in "hash  path" format
        for line in lines[1:]:
            # Should have exactly two spaces between hash and path
            assert '  ' in line
            parts = line.split('  ', 1)
            assert len(parts) == 2
            
            hash_value, path = parts
            # Hash should be lowercase hex
            assert hash_value == hash_value.lower()
            assert all(c in '0123456789abcdef' for c in hash_value)

    def test_different_algorithms_stdout(self, simple_test_directory):
        """Test stdout output for different hash algorithms."""
        for algorithm in ["md5", "sha1", "sha256", "sha512"]:
            captured_output = StringIO()
            
            with redirect_stdout(captured_output):
                result = calculate_checksums(
                    [simple_test_directory],
                    algorithm=algorithm,
                    threads=1,
                    quiet=False
                )
            
            output = captured_output.getvalue()
            
            # Header should indicate correct algorithm
            assert f"# {algorithm.upper()} checksums" in output
            
            # Should have all files
            assert "file1.txt" in output
            assert "file2.txt" in output
            assert "file3.txt" in output

    def test_multithread_stdout_output(self, simple_test_directory):
        """Test that multi-threaded calculation also outputs to stdout."""
        captured_output_single = StringIO()
        captured_output_multi = StringIO()
        
        # Single thread
        with redirect_stdout(captured_output_single):
            result_single = calculate_checksums(
                [simple_test_directory],
                algorithm="sha256",
                threads=1,
                quiet=False
            )
        
        # Multi thread
        with redirect_stdout(captured_output_multi):
            result_multi = calculate_checksums(
                [simple_test_directory],
                algorithm="sha256",
                threads=4,
                quiet=False
            )
        
        # Both should produce output
        assert len(captured_output_single.getvalue()) > 0
        assert len(captured_output_multi.getvalue()) > 0
        
        # Results should be identical
        assert result_single == result_multi

    def test_sorted_output_in_stdout(self, simple_test_directory):
        """Test that stdout output is sorted by path."""
        captured_output = StringIO()
        
        with redirect_stdout(captured_output):
            calculate_checksums(
                [simple_test_directory],
                algorithm="sha256",
                threads=4,
                quiet=False
            )
        
        output = captured_output.getvalue()
        lines = [l for l in output.strip().split('\n') 
                 if l and not l.startswith('#') and '  ' in l]
        
        # Extract paths
        paths = [line.split('  ', 1)[1] for line in lines]
        
        # Verify paths are sorted
        assert paths == sorted(paths)

    def test_empty_directory_quiet(self):
        """Test quiet mode with empty directory."""
        test_dir = tempfile.mkdtemp()
        try:
            captured_output = StringIO()
            
            with redirect_stdout(captured_output):
                result = calculate_checksums(
                    [test_dir],
                    algorithm="sha256",
                    threads=1,
                    quiet=True
                )
            
            output = captured_output.getvalue()
            assert output.strip() == ""
            assert len(result) == 0
        finally:
            shutil.rmtree(test_dir)

    def test_exclude_patterns_with_stdout(self, simple_test_directory):
        """Test that exclude patterns work correctly with stdout output."""
        # Add a file to exclude
        tmp_file = os.path.join(simple_test_directory, "temp.tmp")
        with open(tmp_file, 'w') as f:
            f.write("temporary")
        
        captured_output = StringIO()
        
        with redirect_stdout(captured_output):
            result = calculate_checksums(
                [simple_test_directory],
                algorithm="sha256",
                exclude_patterns=["*.tmp"],
                threads=1,
                quiet=False
            )
        
        output = captured_output.getvalue()
        
        # Should have 3 original files
        assert len([l for l in output.split('\n') if '  ' in l and not l.startswith('#')]) == 3
        
        # temp.tmp should not be in output
        assert "temp.tmp" not in output
