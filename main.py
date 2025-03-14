#!/usr/bin/env python3
"""ExporterGenius - AI-Powered Prometheus Exporter Generator."""
import asyncio
import yaml
import os
import argparse
import sys
import types
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from orchestration.orchestrator import Orchestrator
from exceptions import ExporterAgentError, APIKeyError, ConfigError
from logging_utils import setup_logging

# Initialize rich console
console = Console()


def load_config(config_dir: Path = None) -> tuple:
    """
    Load configuration files.
    
    Args:
        config_dir: Path to config directory
        
    Returns:
        Tuple of (prompts, settings)
        
    Raises:
        ConfigError: If config files can't be loaded
    """
    if config_dir is None:
        config_dir = Path(__file__).parent / "config"
    
    try:
        with open(config_dir / "prompts.yaml") as f:
            prompts = yaml.safe_load(f)
        with open(config_dir / "settings.yaml") as f:
            settings = yaml.safe_load(f)
            
        if not prompts:
            raise ConfigError("prompts.yaml is empty or invalid")
        if not settings:
            raise ConfigError("settings.yaml is empty or invalid")
            
        return prompts, settings
    except (yaml.YAMLError, OSError) as e:
        raise ConfigError(f"Failed to load configuration: {str(e)}")


def check_environment() -> bool:
    """
    Check if required environment variables are set.
    
    Returns:
        True if all required variables are set, False otherwise
    """
    if not os.environ.get("OPENAI_API_KEY"):
        console.print(Panel.fit(
            "[bold red]ERROR:[/] OPENAI_API_KEY environment variable not set.\n"
            "Please set it with: [bold]export OPENAI_API_KEY=your-api-key[/]",
            title="Environment Error"
        ))
        return False
    return True


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="AI-Powered Prometheus Exporter Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--target", 
        type=str, 
        default="aws_connect_exporter",
        help="Name of the target exporter"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    parser.add_argument(
        "--log-file", 
        type=str, 
        default="logs/exporter_agent.log",
        help="Log file path"
    )
    parser.add_argument(
        "--no-console", 
        action="store_true",
        help="Disable console output for logs"
    )
    return parser.parse_args()


def display_results(results: dict) -> None:
    """
    Display results in a rich formatted output.
    
    Args:
        results: Results dictionary from orchestrator
    """
    # Create table for main results
    table = Table(title="Exporter Generation Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Researched Metrics", str(len(results['research'].metrics)))
    table.add_row("Generated Files", ", ".join(list(results['code'].files.keys())))
    table.add_row("Tests Passed", "✅ Yes" if results['test_result'].passed else "❌ No")
    table.add_row("Validation Errors", str(len(results['code'].validation_errors)))
    
    console.print(table)
    
    # Display dashboard design
    console.print(Panel(
        results.get("dashboard", "No dashboard design produced"),
        title="Dashboard Design",
        border_style="blue"
    ))
    
    # Display alert suggestions
    console.print(Panel(
        results.get("alerts", "No alert suggestions produced"),
        title="Alert Suggestions",
        border_style="yellow"
    ))
    
    # Display test output if tests failed
    if not results['test_result'].passed:
        console.print(Panel(
            results['test_result'].output,
            title="Test Output",
            border_style="red"
        ))


async def main() -> int:
    """
    Main function.
    
    Returns:
        Exit code
    """
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(
        log_level=args.log_level,
        log_file=args.log_file,
        console_output=not args.no_console
    )
    
    if not check_environment():
        return 1
    
    try:
        logger.info("Loading configuration")
        prompts, settings = load_config()
        
        # Inject loaded configurations into the modules by overriding the config modules.
        # This ensures that any module importing config.prompts or config.settings gets these values.
        sys.modules["config.prompts"] = types.ModuleType("prompts")
        sys.modules["config.prompts"].__dict__.update(prompts)
        sys.modules["config.settings"] = types.ModuleType("settings")
        sys.modules["config.settings"].__dict__.update(settings)
        
        logger.info(f"Starting orchestrator with target: {args.target} in {args.mode} mode")
        orchestrator = Orchestrator(
            target=args.target,
            mode=args.mode,
            exporter_path=args.exporter_path
        )
        
        # Use rich progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating exporter...", total=None)
            
            try:
                results = await orchestrator.run_agents()
                progress.update(task, description="Exporter generated successfully!", completed=True)
                display_results(results)
                return 0
            except Exception as e:
                progress.update(task, description=f"Failed: {str(e)}", completed=True)
                logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
                console.print(f"[bold red]Pipeline failed:[/] {str(e)}")
                return 1
                
    except ConfigError as e:
        console.print(f"[bold red]Configuration error:[/] {str(e)}")
        return 1
    except APIKeyError as e:
        console.print(f"[bold red]API key error:[/] {str(e)}")
        return 1
    except ExporterAgentError as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        return 1
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/] {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
