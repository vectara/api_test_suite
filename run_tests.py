#!/usr/bin/env python3
"""
Vectara API Test Suite Runner

This script provides a straightforward interface for running the Vectara API
test suite with command-line or environment variable authentication.

Usage:
    # Command-line argument
    python run_tests.py --api-key YOUR_API_KEY

    # Environment variable (recommended for CI/CD)
    export VECTARA_API_KEY=your_key
    python run_tests.py

    # Run specific test categories
    python run_tests.py --tests auth,corpus

    # Generate HTML report
    python run_tests.py --html-report
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def get_console():
    """Get Rich console or None if not available."""
    if RICH_AVAILABLE:
        return Console()
    return None


def print_header(console):
    """Print welcome header."""
    if console:
        console.print(Panel.fit(
            "[bold blue]Vectara API Test Suite[/bold blue]\n"
            "[dim]Comprehensive API validation for upgrade verification[/dim]",
            border_style="blue",
        ))
    else:
        print("=" * 50)
        print("Vectara API Test Suite")
        print("Comprehensive API validation for upgrade verification")
        print("=" * 50)


def validate_api_key(api_key):
    """Basic validation of API key format."""
    errors = []

    if not api_key:
        errors.append("API key is required. Provide via --api-key or VECTARA_API_KEY environment variable")
    elif len(api_key) < 10:
        errors.append("API key appears to be too short")

    return errors


def build_pytest_args(args, test_selection):
    """Build pytest command-line arguments."""
    pytest_args = [
        "-v",  # Verbose output
        "--tb=short",  # Shorter tracebacks
    ]

    # Add HTML report if requested
    if args.html_report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path("reports") / f"test_report_{timestamp}.html"
        report_path.parent.mkdir(exist_ok=True)
        pytest_args.extend(["--html", str(report_path), "--self-contained-html"])

    # Add JSON report for CI/CD
    if args.json_report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = Path("reports") / f"test_results_{timestamp}.json"
        json_path.parent.mkdir(exist_ok=True)
        pytest_args.extend(["--json-report", f"--json-report-file={json_path}"])

    # Add parallel execution if requested
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])

    # Add test selection
    if "all" not in test_selection:
        test_files = []
        test_mapping = {
            "auth": "tests/test_01_authentication.py",
            "corpus": "tests/test_02_corpus_management.py",
            "indexing": "tests/test_03_indexing.py",
            "query": "tests/test_04_query_search.py",
            "agents": "tests/test_05_agents.py",
        }
        for sel in test_selection:
            if sel in test_mapping:
                test_files.append(test_mapping[sel])

        if test_files:
            pytest_args.extend(test_files)
        else:
            pytest_args.append("tests/")
    else:
        pytest_args.append("tests/")

    # Add API key via command-line option
    if args.api_key:
        pytest_args.extend(["--api-key", args.api_key])
    if args.base_url:
        pytest_args.extend(["--base-url", args.base_url])
    if args.llm_name:
        pytest_args.extend(["--llm-name", args.llm_name])
    if args.generation_preset:
        pytest_args.extend(["--generation-preset", args.generation_preset])

    return pytest_args


def run_tests(pytest_args, console):
    """Execute pytest with the given arguments."""
    if console:
        console.print("\n[bold green]Starting test execution...[/bold green]\n")
    else:
        print("\nStarting test execution...\n")

    # Run pytest
    cmd = [sys.executable, "-m", "pytest"] + pytest_args

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        if console:
            console.print("\n[yellow]Test execution cancelled by user.[/yellow]")
        else:
            print("\nTest execution cancelled by user.")
        return 130


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Vectara API Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --api-key YOUR_KEY              # With API key
  python run_tests.py --tests auth,corpus             # Run specific tests
  python run_tests.py --html-report                   # Generate HTML report
  python run_tests.py --llm-name mockingbird-2.0      # Specify LLM model
  python run_tests.py --generation-preset vectara-summary-ext-24-05-med-omni

Environment Variables:
  VECTARA_API_KEY            Your Personal API key (recommended for CI/CD)
  VECTARA_BASE_URL           Custom API URL for on-premise deployments
  VECTARA_LLM_NAME           LLM model name for generation
  VECTARA_GENERATION_PRESET  Generation preset name
        """,
    )

    # Credential arguments
    parser.add_argument(
        "--api-key", "-k",
        help="Vectara Personal API key (or set VECTARA_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url", "-u",
        help="Vectara API base URL for on-premise (default: https://api.vectara.io)",
    )

    # Generation config arguments
    parser.add_argument(
        "--llm-name",
        help="LLM model name for generation (or set VECTARA_LLM_NAME env var)",
    )
    parser.add_argument(
        "--generation-preset",
        help="Generation preset name (or set VECTARA_GENERATION_PRESET env var)",
    )

    # Test selection
    parser.add_argument(
        "--tests", "-t",
        help="Comma-separated list of test categories: auth,corpus,indexing,query,agents,all",
    )

    # Report options
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report",
    )
    parser.add_argument(
        "--json-report",
        action="store_true",
        help="Generate JSON report for CI/CD integration",
    )

    # Execution options
    parser.add_argument(
        "--parallel", "-p",
        type=int,
        metavar="N",
        help="Run tests in parallel with N workers",
    )

    args = parser.parse_args()
    console = get_console()

    print_header(console)

    # Determine API key from args or environment
    api_key = args.api_key or os.environ.get("VECTARA_API_KEY")
    base_url = args.base_url or os.environ.get("VECTARA_BASE_URL")

    # Validate API key
    errors = validate_api_key(api_key)
    if errors:
        if console:
            for error in errors:
                console.print(f"[red]Error: {error}[/red]")
            console.print("\n[yellow]Usage:[/yellow]")
            console.print("  python run_tests.py --api-key YOUR_API_KEY")
            console.print("  [dim]or[/dim]")
            console.print("  export VECTARA_API_KEY=your_key && python run_tests.py")
        else:
            for error in errors:
                print(f"Error: {error}")
            print("\nUsage:")
            print("  python run_tests.py --api-key YOUR_API_KEY")
            print("  or")
            print("  export VECTARA_API_KEY=your_key && python run_tests.py")
        sys.exit(1)

    # Set environment variables for pytest
    os.environ["VECTARA_API_KEY"] = api_key
    if base_url:
        os.environ["VECTARA_BASE_URL"] = base_url

    # Get test selection
    if args.tests:
        test_selection = [t.strip().lower() for t in args.tests.split(",")]
    else:
        test_selection = ["all"]

    # Show test categories
    if console:
        table = Table(title="Test Categories")
        table.add_column("Category", style="cyan")
        table.add_column("Status")

        categories = ["auth", "corpus", "indexing", "query", "agents"]
        for cat in categories:
            status = "[green]✓ Selected[/green]" if "all" in test_selection or cat in test_selection else "[dim]Skipped[/dim]"
            table.add_row(cat, status)

        console.print(table)

    # Build and run pytest
    pytest_args = build_pytest_args(args, test_selection)

    if console:
        console.print(f"\n[dim]Running: pytest {' '.join(pytest_args)}[/dim]\n")
    else:
        print(f"\nRunning: pytest {' '.join(pytest_args)}\n")

    exit_code = run_tests(pytest_args, console)

    # Summary
    if console:
        if exit_code == 0:
            console.print("\n[bold green]✔ All tests passed![/bold green]")
        else:
            console.print(f"\n[bold red]✘ Tests failed with exit code {exit_code}[/bold red]")
    else:
        if exit_code == 0:
            print("\nAll tests passed!")
        else:
            print(f"\nTests failed with exit code {exit_code}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
