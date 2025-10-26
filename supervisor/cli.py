#!/usr/bin/env python
"""
CLI Interface for Supervisor Agent.

This module provides a command-line interface for the Supervisor CLI Agent,
supporting both single-query mode and interactive REPL mode.
"""
import sys
import argparse
from pathlib import Path
from supervisor.agent import SupervisorAgent


def print_banner():
    """Print welcome banner for interactive mode."""
    print("\n" + "=" * 60)
    print("Supervisor CLI Agent - Interactive Mode")
    print("=" * 60)
    print("Type your queries and press Enter.")
    print("Type 'exit' or 'quit' to end the session.")
    print("=" * 60 + "\n")


def interactive_mode(supervisor: SupervisorAgent):
    """
    Run interactive REPL mode.

    Args:
        supervisor: Initialized SupervisorAgent instance

    Returns:
        Exit code (0 for success)
    """
    print_banner()

    while True:
        try:
            # Prompt for user input
            query = input("You: ").strip()

            # Check for exit commands
            if query.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break

            # Skip empty queries
            if not query:
                continue

            # Process query
            try:
                response = supervisor.respond(query)
                print(f"\nAssistant: {response}\n")
            except ValueError as e:
                print(f"\nError: {e}\n")
            except Exception as e:
                print(f"\nError processing query: {e}\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break

    return 0


def single_query_mode(supervisor: SupervisorAgent, query: str):
    """
    Process a single query and exit.

    Args:
        supervisor: Initialized SupervisorAgent instance
        query: User query string

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        response = supervisor.respond(query)
        print(response)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error processing query: {e}", file=sys.stderr)
        return 1


def main():
    """
    Main CLI entry point.

    Parses command-line arguments and dispatches to appropriate mode.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description='Supervisor CLI Agent - Query processing with intelligent routing',
        epilog='Examples:\n'
               '  Single query:   python -m supervisor.cli "What is the capital of France?"\n'
               '  Custom config:  python -m supervisor.cli --config my_config.json "query"\n'
               '  Interactive:    python -m supervisor.cli --interactive\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'query',
        nargs='?',
        help='Query to process (omit for interactive mode if --interactive is set)'
    )

    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive REPL mode'
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Supervisor CLI Agent v0.1.0 (Stage 2)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.interactive and not args.query:
        # No query and not interactive mode - default to interactive
        args.interactive = True

    # Initialize supervisor with config
    try:
        supervisor = SupervisorAgent(config_path=args.config)
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: Invalid configuration: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error initializing supervisor: {e}", file=sys.stderr)
        return 1

    # Dispatch to appropriate mode
    if args.interactive:
        return interactive_mode(supervisor)
    else:
        return single_query_mode(supervisor, args.query)


if __name__ == "__main__":
    sys.exit(main())
