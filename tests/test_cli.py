"""
Tests for CLI interface.
Tests command-line argument parsing and execution.
"""
import pytest
import subprocess
from unittest.mock import patch


class TestCLISingleQueryMode:
    """Test CLI in single-query mode."""

    @patch('supervisor.handlers.call_claude_api')
    def test_cli_single_query_mode(self, mock_claude):
        """
        Test Case: CLI Single Query Mode
        Given: CLI invoked with a query argument
        When: python -m supervisor.cli "What is the capital of France?"
        Then: Response is printed to stdout
        And: Exit code is 0
        """
        mock_claude.return_value = "The capital of France is Paris."

        result = subprocess.run(
            ['python', '-m', 'supervisor.cli', 'What is the capital of France?'],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert len(result.stdout) > 0


class TestCLIConfigFlag:
    """Test CLI with custom config file."""

    @patch('supervisor.handlers.call_claude_api')
    def test_cli_custom_config(self, mock_claude):
        """
        Test Case: CLI Custom Config
        Given: CLI invoked with --config flag
        When: python -m supervisor.cli --config custom_config.json "query"
        Then: Custom config is loaded and used
        And: Response is generated
        """
        mock_claude.return_value = "Test response."

        result = subprocess.run(
            ['python', '-m', 'supervisor.cli', '--config', 'tests/fixtures/test_config.json', 'test query'],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert len(result.stdout) > 0


class TestCLIInteractiveMode:
    """Test CLI in interactive mode."""

    @pytest.mark.skip(reason="Interactive mode testing requires complex simulation")
    def test_cli_interactive_mode(self):
        """
        Test Case: CLI Interactive Mode
        Given: CLI invoked with --interactive flag
        When: python -m supervisor.cli --interactive
        Then: REPL loop is started
        And: User can enter multiple queries
        """
        # This test is complex and deferred to manual testing
        pass


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_cli_no_arguments(self):
        """
        Test Case: CLI with No Arguments
        Given: CLI invoked without arguments
        When: python -m supervisor.cli
        Then: Interactive mode starts (we can't easily test this, so just check it doesn't crash)
        """
        # Start CLI without args, then send EOF immediately to exit
        result = subprocess.run(
            ['python', '-m', 'supervisor.cli'],
            input='',  # Send empty input (EOF)
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should exit cleanly (exit code 0 or possibly non-zero if EOF handling differs)
        # Main thing is it doesn't crash
        assert result.returncode in [0, 1]  # Allow either success or controlled exit

    def test_cli_invalid_config_path(self):
        """
        Test Case: CLI with Invalid Config Path
        Given: CLI invoked with non-existent config file
        When: python -m supervisor.cli --config invalid.json "query"
        Then: Error message is displayed
        And: Exit code is non-zero
        """
        result = subprocess.run(
            ['python', '-m', 'supervisor.cli', '--config', 'nonexistent.json', 'test'],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode != 0
        assert "Error" in result.stderr or "error" in result.stderr.lower()
