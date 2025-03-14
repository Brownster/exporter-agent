# ExporterGenius 🚀🤖

**AI-Powered Prometheus Exporter Generator for target platform of your choice**

[![Go Version](https://img.shields.io/badge/Go-1.20%2B-blue)](https://golang.org/)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automatically generate production-ready Prometheus exporters for target platforms using AI agents. This solution leverages LangChain and LLMs to create monitoring systems that follow best practices out of the box.

![Workflow Diagram](https://via.placeholder.com/800x400.png?text=AI+Agent+Workflow+Diagram)

## Features ✨

- 🧠 AI-Driven metric discovery and code generation
- 🔍 Automatic validation with Go toolchain (gofmt, govet, gosec)
- ♻️ Smart retry mechanism with error diagnosis
- 🧪 Automated test generation and execution
- ⚙️ YAML-configurable prompts and settings
- 🔐 Secure API key management
- 📊 Dashboard and alert suggestion generation
- 📝 Structured logging with file rotation
- ⚡ Parallel execution for improved performance

## Getting Started 🚀

### Prerequisites

- Go 1.20+
- Python 3.9+
- API Key for OpenAI or Anthropic (Claude)
- Go tools:
  ```bash
  go install golang.org/x/lint/golint@latest
  go install github.com/securego/gosec/v2/cmd/gosec@latest
  ```

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/exporter-genius.git
    cd exporter-genius
    ```

2. Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Run the setup wizard to configure your API keys securely:
    ```bash
    python cli.py setup
    ```

## Usage 📖

### Basic Usage

Run the exporter generator with default settings to create a new exporter:

```bash
python cli.py run
```

### Advanced Options

```bash
# Use a specific target name
python cli.py run --target mysql_exporter

# Set custom log level
python cli.py run --log-level DEBUG

# Specify custom log file location
python cli.py run --log-file /path/to/custom/log.txt

# Load previously stored API keys
python cli.py load-keys
```

### Extension Mode

Extend an existing exporter with new metrics:

```bash
# Extend an existing exporter
python cli.py run --mode extend --exporter-path /path/to/existing/exporter

# Extend and change the target name
python cli.py run --mode extend --exporter-path /path/to/existing/exporter --target enhanced_exporter
```

### Example Output

```
Exporter Generation Results
┌──────────────────┬─────────────────────────────────┐
│ Metric           │ Value                           │
├──────────────────┼─────────────────────────────────┤
│ Researched       │ 8                               │
│ Metrics          │                                 │
│ Generated Files  │ exporter.go, exporter_test.go   │
│ Tests Passed     │ ✅ Yes                          │
│ Validation       │ 0                               │
│ Errors           │                                 │
└──────────────────┴─────────────────────────────────┘

┌─ Dashboard Design ──────────────────────────────┐
│ # AWS Connect Dashboard                         │
│                                                 │
│ This dashboard provides monitoring for AWS      │
│ Connect metrics with the following panels:      │
│                                                 │
│ 1. Queue Length - Line chart showing queue      │
│    length over time                             │
│ 2. Agents Online - Gauge showing number of      │
│    available agents                             │
└─────────────────────────────────────────────────┘

┌─ Alert Suggestions ─────────────────────────────┐
│ # AWS Connect Alerts                            │
│                                                 │
│ - High Queue Alert: Trigger when                │
│   aws_connect_queue_length > 20 for 5min        │
│                                                 │
│ - Agent Availability: Trigger when              │
│   aws_connect_agent_online < 5 for 5min         │
└─────────────────────────────────────────────────┘
```

## Configuration ⚙️

### Prompts Configuration (`config/prompts.yaml`)

```yaml
research_prompts:
  main: |
    Research metrics for {target}...
    
coding_prompts:
  main: |
    Generate Go code for {metrics}...

tests: |
  Generate tests for the exporter...
```

### System Settings (`config/settings.yaml`)

```yaml
app_settings:
  max_retries: 3
  test_timeout: 60
  module_name: "aws_connect_exporter"

llm:
  research:
    provider: gpt-turbo
    model: gpt-3.5-turbo
  coding:
    provider: gpt-turbo
    model: gpt-3.5-turbo

go_tools:
  format:
    command: gofmt
    args: ["-w"]
  vet:
    command: go
    args: ["vet"]
```

## Project Architecture 🏗️

The project uses a modular agent-based architecture:

- **Research Agent**: Discovers appropriate metrics for the target system
- **Coding Agent**: Generates Go code for the exporter
- **Validation Agent**: Validates the generated code with Go tools
- **Testing Agent**: Runs tests against the generated exporter
- **Dashboard Agent**: Creates dashboard visualization suggestions
- **Alert Agent**: Proposes appropriate alerting rules

All agents are orchestrated through a central coordinator that manages the workflow and handles failures gracefully.

## Security 🔒

API keys are stored securely using encryption. Keys are never stored in plain text and are only decrypted when needed for API calls.

## Testing 🧪

Run the test suite with:

```bash
pytest tests/
```

## Contributing 🤝

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments 🙏

- OpenAI and Anthropic for their LLM APIs
- Prometheus community for client libraries
- AWS for Connect API access
