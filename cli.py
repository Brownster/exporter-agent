#!/usr/bin/env python3
"""Command-line interface for the exporter-agent."""
import argparse
import asyncio
import getpass
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm

from main import main as run_main
from security import save_api_key, set_api_key_env
from exceptions import APIKeyError
from logging_utils import setup_logging

# Initialize console
console = Console()


def setup_command(args):
    """
    Set up the exporter-agent with API keys.
    
    Args:
        args: Command-line arguments
    """
    logger = setup_logging()
    
    console.print("[bold]ExporterGenius Setup[/bold]")
    console.print("This will securely store your LLM API keys for later use.\n")
    
    # Get OpenAI API key
    if Confirm.ask("Do you want to set up an OpenAI API key?"):
        openai_key = Prompt.ask("Enter your OpenAI API key", password=True)
        password = getpass.getpass("Create a password to encrypt your API keys: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            console.print("[bold red]Passwords do not match![/]")
            return 1
            
        try:
            save_api_key(openai_key, "openai", password)
            console.print("[green]OpenAI API key saved successfully![/]")
        except APIKeyError as e:
            console.print(f"[bold red]Failed to save OpenAI API key:[/] {str(e)}")
            return 1
    
    # Get Anthropic API key (optional)
    if Confirm.ask("Do you want to set up an Anthropic API key?"):
        anthropic_key = Prompt.ask("Enter your Anthropic API key", password=True)
        
        if not 'password' in locals():
            password = getpass.getpass("Create a password to encrypt your API keys: ")
            password_confirm = getpass.getpass("Confirm password: ")
            
            if password != password_confirm:
                console.print("[bold red]Passwords do not match![/]")
                return 1
                
        try:
            save_api_key(anthropic_key, "anthropic", password)
            console.print("[green]Anthropic API key saved successfully![/]")
        except APIKeyError as e:
            console.print(f"[bold red]Failed to save Anthropic API key:[/] {str(e)}")
            return 1
    
    console.print("\n[bold green]Setup complete![/] You can now run the exporter-agent.")
    return 0


def load_keys_command(args):
    """
    Load API keys from secure storage into environment variables.
    
    Args:
        args: Command-line arguments
    """
    logger = setup_logging()
    
    console.print("[bold]Loading API Keys[/bold]")
    
    password = getpass.getpass("Enter your API key password: ")
    
    try:
        # Try to load OpenAI API key
        set_api_key_env("openai", password)
        console.print("[green]Loaded OpenAI API key successfully![/]")
    except APIKeyError as e:
        console.print(f"[yellow]Note:[/] {str(e)}")
    
    try:
        # Try to load Anthropic API key
        set_api_key_env("anthropic", password)
        console.print("[green]Loaded Anthropic API key successfully![/]")
    except APIKeyError as e:
        console.print(f"[yellow]Note:[/] {str(e)}")
    
    return 0


def run_command(args):
    """
    Run the exporter-agent.
    
    Args:
        args: Command-line arguments
    """
    # Pass all arguments to the main function
    return asyncio.run(run_main())


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ExporterGenius - AI-Powered Prometheus Exporter Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up API keys")
    setup_parser.set_defaults(func=setup_command)
    
    # Load keys command
    load_keys_parser = subparsers.add_parser("load-keys", help="Load API keys into environment")
    load_keys_parser.set_defaults(func=load_keys_command)
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the exporter-agent")
    run_parser.add_argument(
        "--target", 
        type=str, 
        default="aws_connect_exporter",
        help="Name of the target exporter"
    )
    run_parser.add_argument(
        "--mode",
        type=str,
        choices=["create", "extend"],
        default="create",
        help="Whether to create new exporter or extend existing one"
    )
    run_parser.add_argument(
        "--exporter-path",
        type=str,
        help="Path to existing exporter code directory when using 'extend' mode"
    )
    run_parser.add_argument(
        "--log-level", 
        type=str, 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    run_parser.add_argument(
        "--log-file", 
        type=str, 
        default="logs/exporter_agent.log",
        help="Log file path"
    )
    run_parser.add_argument(
        "--no-console", 
        action="store_true",
        help="Disable console output for logs"
    )
    run_parser.set_defaults(func=run_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if hasattr(args, "func"):
        return args.func(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())