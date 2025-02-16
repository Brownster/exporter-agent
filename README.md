# ExporterGenius 🚀🤖

**AI-Powered Prometheus Exporter Generator for target platform of your choice**

[![Go Version](https://img.shields.io/badge/Go-1.20%2B-blue)](https://golang.org/)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automatically generate production-ready Prometheus exporters for target platform of choice using AI agents. This Go-based solution leverages LangChain and OpenAI to create monitoring systems that follow best practices out of the box.

![Workflow Diagram](https://via.placeholder.com/800x400.png?text=AI+Agent+Workflow+Diagram)

## Features ✨

- 🧠 AI-Driven metric discovery and code generation
- 🔍 Automatic validation with Go toolchain (gofmt, govet, gosec)
- ♻️ Smart retry mechanism with error diagnosis
- 🧪 Automated test generation and execution
- ⚙️ YAML-configurable prompts and settings

## Getting Started 🚀

### Prerequisites

- Go 1.20+
- Python 3.9+
- [OpenAI API Key](https://platform.openai.com/api-keys)
- Go tools:
  ```bash
  go install golang.org/x/lint/golint@latest
  go install github.com/securego/gosec/v2/cmd/gosec@latest

Installation

    Clone the repository:
    bash
    Copy

    git clone https://github.com/yourusername/exporter-genius.git
    cd exporter-genius

    Install Python dependencies:
    bash
    Copy

    pip install -r requirements.txt

    Set up OpenAI API key:
    bash
    Copy

    export OPENAI_API_KEY="your-api-key-here"

Usage 📖

    Configure your exporter in config/prompts.yaml

    Adjust tool settings in config/settings.yaml

    Run the generator:
    bash
    Copy

    python main.py

Example output:
Copy

=== Final Results ===
Researched Metrics: 8
Generated Files: ['exporter.go', 'exporter_test.go']
Tests Passed: True
Validation Errors: 0

Configuration ⚙️
config/prompts.yaml
yaml
Copy

research_prompts:
  main: |
    Research metrics for {target}...
    
coding_prompts:
  main: |
    Generate Go code for {metrics}...

config/settings.yaml
yaml
Copy

app_settings:
  max_retries: 3
  module_name: "my_exporter"

go_tools:
  security:
    command: gosec
    args: ["-exclude=G104", "./..."]

Example Generated Exporter 🔍
go
Copy

package main

import (
    "github.com/aws/aws-sdk-go/service/connect"
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var queueLength = prometheus.NewGauge(prometheus.GaugeOpts{
    Name: "aws_connect_queue_length",
    Help: "Number of calls waiting in queue",
})

func main() {
    prometheus.MustRegister(queueLength)
    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":8080", nil)
}

Contributing 🤝

We welcome contributions! Please follow these steps:

    Fork the repository

    Create your feature branch (git checkout -b feature/amazing-feature)

    Commit your changes (git commit -m 'Add some amazing feature')

    Push to the branch (git push origin feature/amazing-feature)

    Open a Pull Request

License 📄

This project is licensed under the MIT License - see the LICENSE file for details.
Acknowledgments 🙏

    OpenAI for the GPT models

    Prometheus community for client libraries

    AWS for Connect API access
