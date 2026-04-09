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

    # Run specific services
    python run_tests.py --service corpus,auth

    # Run with a depth profile
    python run_tests.py --profile core

    # Generate HTML report
    python run_tests.py --html-report
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Profile-to-marker mapping for depth-based test selection
PROFILE_MARKERS = {
    "sanity": "sanity",
    "core": "sanity or core",
    "regression": "sanity or core or regression",
    "full": None,  # no marker filter
}

# Available services (auto-discovered from tests/services/ subdirectories)
AVAILABLE_SERVICES = ["agents", "auth", "chat", "corpus", "indexing", "llm", "pipelines", "query", "tools", "users"]


def get_console():
    """Get Rich console or None if not available."""
    if RICH_AVAILABLE:
        return Console()
    return None


def print_header(console):
    """Print welcome header."""
    if console:
        console.print(
            Panel.fit(
                "[bold blue]Vectara API Test Suite[/bold blue]\n" "[dim]Comprehensive API validation for upgrade verification[/dim]",
                border_style="blue",
            )
        )
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


def resolve_services(args):
    """Resolve the list of services to run from --service or deprecated --tests."""
    raw = args.service or args.tests
    if raw:
        return [s.strip().lower() for s in raw.split(",")]
    return []


def build_pytest_args(args, services, profile):
    """Build pytest command-line arguments.

    Returns a list of arg-lists (one per phase) when parallel execution splits
    into parallel + sequential phases, otherwise a single-element list.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- common flags shared by every phase ---
    common = [
        "-v",  # Verbose output
        "--tb=short",  # Shorter tracebacks
    ]

    # Pass-through options
    if args.api_key:
        common.extend(["--api-key", args.api_key])
    if args.base_url:
        common.extend(["--base-url", args.base_url])
    if args.llm_name:
        common.extend(["--llm-name", args.llm_name])
    if args.generation_preset:
        common.extend(["--generation-preset", args.generation_preset])

    # --- marker expression from profile ---
    marker_expr = PROFILE_MARKERS.get(profile)

    # --- target directories ---
    if services:
        targets = [f"tests/services/{svc}/" for svc in services]
    elif profile == "full":
        targets = ["tests/"]
    else:
        targets = ["tests/services/"]

    # Build a descriptive label for report filenames
    if services:
        report_label = "_".join(services)
    else:
        report_label = profile

    def add_report_flags(phase_args, phase_suffix=""):
        """Add report flags with descriptive filenames."""
        name = f"{report_label}_{phase_suffix}" if phase_suffix else report_label
        if args.html_report:
            report_path = Path("reports") / f"test_report_{timestamp}_{name}.html"
            report_path.parent.mkdir(exist_ok=True)
            phase_args.extend(["--html", str(report_path), "--self-contained-html"])
        if args.json_report:
            json_path = Path("reports") / f"test_results_{timestamp}_{name}.json"
            json_path.parent.mkdir(exist_ok=True)
            phase_args.extend(["--json-report", f"--json-report-file={json_path}"])

    # --- build phase(s) ---
    if args.parallel:
        # Phase 1: parallel run (excluding serial-marked tests)
        phase1 = list(common)
        phase1.extend(["-n", str(args.parallel)])
        if marker_expr:
            phase1.extend(["-m", f"({marker_expr}) and not serial"])
        else:
            phase1.extend(["-m", "not serial"])
        phase1.extend(targets)

        phases = [phase1]

        # Phase 2: sequential workflow tests (only when profile is full)
        if profile == "full":
            phase2 = list(common)
            if marker_expr:
                phase2.extend(["-m", marker_expr])
            phase2.append("tests/workflows/")
            phases.append(phase2)

        # Add report flags — one file per phase if multiple, no suffix if single
        if len(phases) == 1:
            add_report_flags(phases[0])
        else:
            add_report_flags(phases[0], "services")
            add_report_flags(phases[1], "workflows")

        return phases
    else:
        # Single invocation (no parallelism)
        single = list(common)
        if marker_expr:
            single.extend(["-m", marker_expr])
        single.extend(targets)
        add_report_flags(single)
        return [single]


def run_tests(phases, console):
    """Execute pytest for each phase and return the first non-zero exit code (or 0)."""
    if console:
        console.print("\n[bold green]Starting test execution...[/bold green]\n")
    else:
        print("\nStarting test execution...\n")

    for idx, pytest_args in enumerate(phases):
        if len(phases) > 1:
            label = "Phase 1 (parallel)" if idx == 0 else "Phase 2 (sequential workflows)"
            if console:
                console.print(f"\n[bold cyan]{label}[/bold cyan]")
            else:
                print(f"\n{label}")

        cmd = [sys.executable, "-m", "pytest"] + pytest_args

        if console:
            console.print(f"[dim]Running: pytest {' '.join(pytest_args)}[/dim]\n")
        else:
            print(f"Running: pytest {' '.join(pytest_args)}\n")

        try:
            result = subprocess.run(cmd, cwd=Path(__file__).parent)
            if result.returncode != 0:
                return result.returncode
        except KeyboardInterrupt:
            if console:
                console.print("\n[yellow]Test execution cancelled by user.[/yellow]")
            else:
                print("\nTest execution cancelled by user.")
            return 130

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Vectara API Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --api-key YOUR_KEY                       # With API key
  python run_tests.py --profile sanity                         # Run sanity tests only
  python run_tests.py --profile core --service corpus,auth     # Core tests for specific services
  python run_tests.py --service corpus,query                   # Run specific services (default profile: core)
  python run_tests.py --profile full -p 4                      # Full run, 4 parallel workers
  python run_tests.py --html-report                            # Generate HTML report
  python run_tests.py --llm-name mockingbird-2.0               # Specify LLM model
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
        "--api-key",
        "-k",
        help="Vectara Personal API key (or set VECTARA_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url",
        "-u",
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

    # Profile and service selection
    parser.add_argument(
        "--profile",
        choices=["sanity", "core", "regression", "full"],
        default="core",
        help="Test depth profile (default: core)",
    )
    parser.add_argument(
        "--service",
        "-s",
        help="Comma-separated list of services to test: " + ",".join(AVAILABLE_SERVICES),
    )
    parser.add_argument(
        "--tests",
        "-t",
        help="(Deprecated, use --service) Comma-separated list of services to test",
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
        "--parallel",
        "-p",
        type=int,
        metavar="N",
        help="Run tests in parallel with N workers",
    )

    args = parser.parse_args()
    console = get_console()

    print_header(console)

    # Warn about deprecated --tests flag
    if args.tests and not args.service:
        if console:
            console.print("[yellow]Warning: --tests is deprecated, use --service instead.[/yellow]")
        else:
            print("Warning: --tests is deprecated, use --service instead.")

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

    # Resolve services and profile
    services = resolve_services(args)
    profile = args.profile

    # Show configuration table
    if console:
        table = Table(title="Test Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        table.add_row("Profile", f"[bold]{profile}[/bold]")

        if services:
            table.add_row("Services", ", ".join(services))
        else:
            table.add_row("Services", "[dim]all[/dim]")

        if args.parallel:
            table.add_row("Parallelism", f"{args.parallel} workers")

        marker = PROFILE_MARKERS.get(profile)
        table.add_row("Marker filter", marker if marker else "[dim]none (full)[/dim]")

        console.print(table)

    # Build and run pytest
    phases = build_pytest_args(args, services, profile)

    exit_code = run_tests(phases, console)

    # Summary
    if console:
        if exit_code == 0:
            console.print("\n[bold green]All tests passed![/bold green]")
        else:
            console.print(f"\n[bold red]Tests failed with exit code {exit_code}[/bold red]")
    else:
        if exit_code == 0:
            print("\nAll tests passed!")
        else:
            print(f"\nTests failed with exit code {exit_code}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
