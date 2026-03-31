"""
Command-line interface for sumtool.

Provides 'calc' and 'verify' commands for calculating and verifying file checksums.
"""

import argparse
import sys
import os
from typing import List, Optional

from .calculator import calculate_checksums, SUPPORTED_ALGORITHMS, get_algorithm_help
from .verifier import verify_checksums, print_verification_results, summarize_verification


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog='sumtool',
        description='Calculate and verify file checksums (MD5, SHA1, SHA256, SHA512)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s calc /path/to/dir                     Calculate SHA256 checksums
  %(prog)s calc dir1 dir2 -m md5                 Calculate MD5 checksums
  %(prog)s calc . -e "*.tmp" -e "node_modules"   Exclude patterns
  %(prog)s verify /path/to/dir                   Verify files
  %(prog)s verify -f checksums.sum               Verify with specific file
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Calc command
    calc_parser = subparsers.add_parser(
        'calc',
        help='Calculate checksums for files in directories'
    )
    calc_parser.add_argument(
        'paths',
        nargs='+',
        help='Paths to files or directories to process'
    )
    calc_parser.add_argument(
        '-m', '--method',
        choices=list(SUPPORTED_ALGORITHMS.keys()),
        default='sha256',
        help='Hash algorithm to use (default: sha256). ' + get_algorithm_help()
    )
    calc_parser.add_argument(
        '-e', '--exclude',
        action='append',
        dest='exclude_patterns',
        metavar='PATTERN',
        help='Exclude files/directories matching PATTERN (can be used multiple times)'
    )
    calc_parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Output file path (default: generates .sum file in current directory)'
    )
    calc_parser.set_defaults(func=cmd_calc)
    
    # Verify command
    verify_parser = subparsers.add_parser(
        'verify',
        help='Verify files against a .sum file'
    )
    verify_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory containing files to verify (default: current directory)'
    )
    verify_parser.add_argument(
        '-f', '--file',
        metavar='SUM_FILE',
        help='Path to the .sum file (default: find in directory)'
    )
    verify_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show all files including successfully verified ones'
    )
    verify_parser.set_defaults(func=cmd_verify)
    
    return parser


def cmd_calc(args: argparse.Namespace) -> int:
    """
    Execute the 'calc' command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Determine output file path
        output_file = args.output
        if output_file is None:
            # Generate default filename based on algorithm
            output_file = f"checksums_{args.method}.sum"
        
        # Calculate checksums
        checksums = calculate_checksums(
            paths=args.paths,
            algorithm=args.method,
            exclude_patterns=args.exclude_patterns,
            output_file=output_file
        )
        
        print(f"Calculated checksums for {len(checksums)} file(s)")
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_verify(args: argparse.Namespace) -> int:
    """
    Execute the 'verify' command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Verify checksums
        results = verify_checksums(
            directory=args.path,
            sum_file=args.file
        )
        
        # Print results
        ok, failed, missing, errors = print_verification_results(
            results,
            verbose=args.verbose
        )
        
        # Print summary
        success = summarize_verification(ok, failed, missing, errors)
        
        return 0 if success else 1
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
