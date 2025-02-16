import asyncio
import yaml
from pathlib import Path
from orchestration.orchestrator import Orchestrator

def load_config():
    config_path = Path(__file__).parent / "config"
    with open(config_path / "prompts.yaml") as f:
        prompts = yaml.safe_load(f)
    with open(config_path / "settings.yaml") as f:
        settings = yaml.safe_load(f)
    return prompts, settings

prompts, settings = load_config()

# Inject loaded configurations into the modules by overriding the config modules.
# (This is one way to make the YAML data available to our code.)
import sys
import types
sys.modules["config.prompts"] = types.ModuleType("prompts")
sys.modules["config.prompts"].__dict__.update(prompts)
sys.modules["config.settings"] = types.ModuleType("settings")
sys.modules["config.settings"].__dict__.update(settings)

async def main():
    orchestrator = Orchestrator(target="aws_connect_exporter")
    try:
        results = await orchestrator.run_agents()
        print("\n=== Final Results ===")
        print(f"Researched Metrics: {len(results['research'].metrics)}")
        print(f"Generated Files: {list(results['code'].files.keys())}")
        print(f"Tests Passed: {results['test_result'].passed}")
        print(f"Validation Errors: {len(results['code'].validation_errors)}")
        if not results['test_result'].passed:
            print("\n=== Test Output ===")
            print(results['test_result'].output)
    except Exception as e:
        print(f"Pipeline failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
