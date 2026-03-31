# sum-tool

A Python tool for calculating and verifying file checksums (MD5, SHA1, SHA256, SHA512).

## Features

- **Multiple Hash Algorithms**: Support for MD5, SHA1, SHA256, and SHA512
- **Batch Processing**: Calculate checksums for entire directories recursively
- **Exclude Patterns**: Exclude files/directories using glob patterns
- **Cross-Platform Verification**: Generate checksums on one machine and verify on another
- **Multi-threading Support**: Parallel processing for faster calculation and verification
- **Standard Format**: Compatible with standard checksum file formats
- **Easy to Use**: Simple command-line interface

## Installation

### From PyPI (recommended)

```bash
pip install sum-tool
```

### From Source

```bash
git clone https://github.com/lijunjie2232/sum-tool.git
cd sum-tool
pip install -e .
```

### Development Installation

```bash
# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate     # On Windows

# Install in development mode
pip install -e .
```

## Usage

### Calculate Checksums

Basic usage (uses SHA256 by default):

```bash
sumtool calc /path/to/directory
```

Specify hash algorithm:

```bash
sumtool calc /path/to/directory --method sha256
sumtool calc /path/to/directory -m md5
sumtool calc /path/to/directory -m sha1
sumtool calc /path/to/directory -m sha512
```

Exclude files/directories:

```bash
# Exclude temporary files
sumtool calc /path/to/directory --exclude "*.tmp"

# Exclude multiple patterns
sumtool calc /path/to/directory -e "*.tmp" -e "*.log" -e "node_modules"

# Exclude specific directories
sumtool calc /path/to/directory -e ".git" -e "__pycache__"
```

Specify output file:

```bash
sumtool calc /path/to/directory --output my_checksums.sum
sumtool calc dir1 dir2 -o output.sum
```

Output to stdout (default behavior when no -o flag):

```bash
# Print checksums to stdout
sumtool calc /path/to/directory

# Suppress all output (useful for scripting)
sumtool calc /path/to/directory --quiet
sumtool calc /path/to/directory -q

# Pipe to other commands
sumtool calc /path/to/directory | grep "important.txt"
sumtool calc /path/to/directory > checksums.sum
```

Process multiple paths:

```bash
sumtool calc /path/to/dir1 /path/to/dir2 /path/to/file.txt
```

Use multi-threading for better performance:

```bash
# Use 4 threads for calculation
sumtool calc /path/to/directory --threads 4
sumtool calc /path/to/directory -t 8

# Combine with other options
sumtool calc /path/to/directory -t 4 -m sha256 -e "*.tmp" -o checksums.sum
```

### Verify Checksums

Basic verification (automatically finds .sum file):

```bash
sumtool verify /path/to/directory
```

Specify the .sum file:

```bash
sumtool verify /path/to/directory --file checksums.sum
```

Use multi-threading for faster verification:

```bash
# Use 4 threads for verification
sumtool verify /path/to/directory --threads 4
sumtool verify /path/to/directory -t 8

# Verbose mode with multi-threading
sumtool verify /path/to/directory -t 4 -v

# Specify .sum file with multi-threading
sumtool verify /path/to/directory -f checksums.sum -t 4
```

Verbose output (show all files including successful ones):

```bash
sumtool verify /path/to/directory --verbose
```

## Examples

### Example 1: Basic Workflow

```bash
# On the source machine
# Calculate SHA256 checksums for a directory
sumtool calc /home/user/my_project -e "*.pyc" -e "__pycache__"

# This creates: checksums_sha256.sum

# Transfer the directory and .sum file to another machine
# Then on the destination machine:
sumtool verify /home/user/my_project
```

### Example 2: Using Different Algorithms

```bash
# Calculate MD5 (faster but less secure)
sumtool calc /data -m md5 -o data_md5.sum

# Calculate SHA512 (more secure but slower)
sumtool calc /important_data -m sha512 -o data_sha512.sum

# Verify
sumtool verify /data -f data_md5.sum
```

### Example 3: Complex Exclusions

```bash
# Exclude build artifacts and version control
sumtool calc ./project \
  -e "build" \
  -e "dist" \
  -e "*.egg-info" \
  -e ".git" \
  -e "*.pyc" \
  -e "__pycache__" \
  -o project_clean.sum
```

### Example 4: Multi-threading for Better Performance

```bash
# Calculate checksums with 8 threads (faster for large directories)
sumtool calc /large_project -t 8 -o project.sum

# Verify with 4 threads
sumtool verify /large_project -f project.sum -t 4

# Combine multi-threading with exclusions
sumtool calc /data -t 4 -e "*.log" -e "*.tmp" -o data.sum
```

### Example 5: Verifying Files in Different Directory

When you move files to a different location, you can verify them using the original `.sum` file:

```bash
# On source machine - generate checksums
sumtool calc /home/user/my_project -o checksums.sum

# Copy files and checksums.sum to another machine/location
cp -r /home/user/my_project /mnt/backup/
cp checksums.sum /mnt/backup/

# On destination machine - verify using explicit directory path
sumtool verify /mnt/backup/my_project -f checksums.sum

# Or use relative paths from current directory
cd /mnt/backup
sumtool verify my_project -f checksums.sum
```

**How it works:**
- When you specify a directory path, `sumtool` uses that directory as the base for finding files
- The `.sum` file contains relative paths (e.g., `file.txt`, `subdir/doc.pdf`)
- If you provide a directory parameter, those relative paths are resolved from that directory
- If no directory is provided, it uses the `.sum` file's location as the base
- If you want to use the current path as base, just specify "." or "./"

## .sum File Format

The tool uses a standard checksum file format:

```
# SHA256 CHECKSUMS
a1b2c3d4e5f6...  relative/path/to/file1.txt
b2c3d4e5f6g7...  relative/path/to/file2.txt
c3d4e5f6g7h8...  file3.txt
```

- First line is a comment indicating the algorithm used
- Each subsequent line contains: `<hash_value>  <relative_path>` (two spaces between hash and path)
- Empty lines and lines starting with `#` are ignored

## Command Reference

### `sumtool calc`

Calculate checksums for files in directories.

```
usage: sumtool calc <paths> [-m METHOD] [-e PATTERN] [-o OUTPUT] [-q] [-t N]

positional arguments:
  paths                 Paths to files or directories to process

optional arguments:
  -m, --method METHOD   Hash algorithm (md5, sha1, sha256, sha512). Default: sha256
  -e, --exclude PATTERN Exclude files/directories matching pattern (can be used multiple times)
  -o, --output FILE     Output file path (if not specified, print to stdout)
  -q, --quiet           Suppress output when no output file is specified
  -t, --threads N       Number of parallel processes to use (default: 1)
```

### `sumtool verify`

Verify files against a .sum file.

```
usage: sumtool verify [path] [-f SUM_FILE] [-v] [-t N]

positional arguments:
  path                  Directory containing files to verify (default: current directory)

optional arguments:
  -f, --file SUM_FILE   Path to the .sum file (default: find in directory)
  -v, --verbose         Show all files including successfully verified ones
  -t, --threads N       Number of parallel processes to use (default: 1)
```

## Exit Codes

- `0`: Success (all files verified successfully or checksums calculated)
- `1`: Error (verification failed, file not found, or other errors)

## Supported Hash Algorithms

| Algorithm | Hash Length | Description |
|-----------|-------------|-------------|
| MD5       | 32 chars    | Fast but cryptographically broken |
| SHA1      | 40 chars    | Faster than SHA256, deprecated for security |
| SHA256    | 64 chars    | Good balance of speed and security (default) |
| SHA512    | 128 chars   | Most secure, slower on some systems |

**Recommendation**: Use SHA256 for general purposes. Use MD5 only for non-security integrity checks where speed is important.

## Multi-threading Performance

The tool supports parallel processing using multiple CPU cores for faster calculation and verification.

### Usage

```bash
# Single-threaded (default)
sumtool calc /path/to/dir -t 1

# Multi-threaded (recommended for large directories)
sumtool calc /path/to/dir -t 4      # 4 threads
sumtool calc /path/to/dir -t 8      # 8 threads
sumtool calc /path/to/dir           # Auto-detect based on CPU cores (future enhancement)
```

### Performance Gains

Actual performance depends on:
- Number of CPU cores
- File sizes and count
- Disk I/O speed
- System load

Typical improvements:
- **Small files (< 1MB)**: 2-4x speedup with 4 threads
- **Medium files (1-10MB)**: 3-6x speedup with 4 threads
- **Large files (> 10MB)**: 4-8x speedup with 8 threads

### Recommendations

- **1-100 files**: Use 1-2 threads (overhead may not justify multi-threading)
- **100-1000 files**: Use 2-4 threads
- **1000+ files**: Use 4-8 threads or more
- **Very large directories**: Match thread count to CPU core count

### Notes

- Results are always sorted by path, regardless of thread count
- Output is deterministic and consistent across different thread counts
- Memory usage increases slightly with more threads
- Optimal thread count is typically equal to CPU core count

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python -m pytest tests/
# or
python -m unittest discover tests/
```

### Project Structure

```
sum-tool/
├── sumtool/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── calculator.py   # Checksum calculation
│   ├── verifier.py     # Checksum verification
│   └── utils.py        # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py
│   └── test_verifier.py
├── setup.py
├── pyproject.toml
└── README.md
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Changelog

### Version 0.1.0

- Initial release
- Support for MD5, SHA1, SHA256, SHA512
- Calculate and verify commands
- Exclude patterns support
- Standard .sum file format
