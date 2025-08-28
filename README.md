# Deimos Router

A Python routing library for building flexible and efficient routing systems.

## Installation

### From PyPI (when published)

```bash
pip install deimos-router
```

### Development Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd deimos-router
```

2. Install with uv (recommended):
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync --dev
```

Or with pip:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Configuration

Deimos Router requires API credentials to function. You need to provide:
- **API URL**: The base URL of your API endpoint
- **API Key**: Your authentication key

### Setting up credentials

There are several ways to provide your API credentials, listed in order of precedence:

#### 1. Environment Variables (Recommended for production)

Set the following environment variables:

```bash
export DEIMOS_API_URL="https://your-api-endpoint.com/api/v1"
export DEIMOS_API_KEY="your-api-key-here"
```

On Windows:
```cmd
set DEIMOS_API_URL=https://your-api-endpoint.com/api/v1
set DEIMOS_API_KEY=your-api-key-here
```

#### 2. Configuration Files

Create one of the following files in your project directory:

**Option A: `secrets.json` (recommended)**
```json
{
  "api_url": "https://your-api-endpoint.com/api/v1",
  "api_key": "your-api-key-here"
}
```

**Option B: `config.json`**
```json
{
  "api_url": "https://your-api-endpoint.com/api/v1",
  "api_key": "your-api-key-here"
}
```

**Option C: `.secrets`**
```json
{
  "api_url": "https://your-api-endpoint.com/api/v1",
  "api_key": "your-api-key-here"
}
```

#### 3. Home Directory Configuration

You can also place a `secrets.json` file in your home directory (`~/secrets.json`) for system-wide configuration.

### For pip-installed users

If you've installed deimos-router via pip, follow these steps:

1. **Copy the example configuration file:**
   ```bash
   # Download the example file from the repository
   curl -o secrets.json https://raw.githubusercontent.com/your-repo/deimos-router/main/secrets.example.json
   ```

2. **Edit the configuration file:**
   Open `secrets.json` in your text editor and replace the placeholder values:
   ```json
   {
     "api_url": "https://your-actual-api-endpoint.com/api/v1",
     "api_key": "your-actual-api-key-here"
   }
   ```

3. **Place the file in your project directory** where you're using deimos-router.

**Important:** Never commit your `secrets.json` file to version control. The file is already included in `.gitignore` to prevent accidental commits.

## Usage

### Basic Usage

```python
from deimos_router import hello
from deimos_router.config import config

# Check if credentials are configured
if config.is_configured():
    print("API credentials are configured!")
    credentials = config.get_credentials()
    print(f"API URL: {credentials['api_url']}")
else:
    print("Please configure your API credentials. See README for instructions.")

print(hello())  # Output: Hello from deimos-router!
```

### Router System

Deimos Router provides a powerful rule-based routing system that can intelligently route requests to different models based on content analysis and custom rules.

#### Basic Router Setup

```python
from deimos_router.router import Router, register_router
from deimos_router.rules import CodeRule, TaskRule
from deimos_router.chat import ChatCompletions

# Create a router with rules
router = Router(
    name="my_router",
    models=["gpt-4", "claude-3-5-sonnet"],
    rules=[
        CodeRule(name="code_detector", code="claude-3-5-sonnet", not_code="gpt-4"),
        TaskRule(name="task_router", rules={"debug": "claude-3-5-sonnet"})
    ]
)

# Router is automatically registered when created

# Use with ChatCompletions API
chat = ChatCompletions()
response = chat.create(
    messages=[{"role": "user", "content": "Fix this Python code: def broken():"}],
    model="deimos/my_router"  # Use router with deimos/ prefix
)
```

#### Available Rules

##### CodeRule - Intelligent Code Detection

The `CodeRule` analyzes request content using advanced regex patterns to determine if it contains code with high accuracy. It can detect:

- **Programming Languages**: Python, JavaScript, Java, C++, Go, Rust, etc.
- **SQL Queries**: SELECT, INSERT, UPDATE, DELETE statements
- **HTML/CSS**: Tags, styles, and markup
- **Shell Commands**: bash, zsh, cmd commands
- **Error Messages**: Stack traces, exceptions, error logs
- **Configuration Files**: JSON, YAML, INI formats

```python
from deimos_router.rules import CodeRule

# Route code requests to Claude, natural language to GPT-4
code_rule = CodeRule(
    name="code_detector",
    code="claude-3-5-sonnet",      # Model for code-related requests
    not_code="gpt-4"               # Model for natural language requests
)
```

**Example Detection:**
- ✅ **Code**: `def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)`
- ✅ **Code**: `SELECT * FROM users WHERE active = true`
- ✅ **Code**: `<div class="container"><h1>Hello</h1></div>`
- ✅ **Code**: `pip install requests && python app.py`
- ❌ **Not Code**: `"How do I implement a binary search algorithm?"`
- ❌ **Not Code**: `"What are the benefits of renewable energy?"`

##### TaskRule - Task-Based Routing

The `TaskRule` routes requests based on task metadata in the request:

```python
from deimos_router.rules import TaskRule

# Route different tasks to specialized models
task_rule = TaskRule(
    name="task_router",
    rules={
        "debug": "claude-3-5-sonnet",
        "creative": "gpt-4",
        "analysis": "gpt-4",
        "coding": "claude-3-5-sonnet"
    }
)

# Use with task parameter
response = chat.create(
    messages=[{"role": "user", "content": "Help me debug this function"}],
    model="deimos/my_router",
    task="debug"  # This will route to claude-3-5-sonnet
)
```

#### Rule Chaining and Priorities

Rules are evaluated in the order they're added to the router. The first rule that returns a decision wins:

```python
router = Router(
    name="chained_router",
    models=["gpt-4", "claude-3-5-sonnet"],
    rules=[
        TaskRule(name="task_first", rules={"debug": "claude-3-5-sonnet"}),
        CodeRule(name="code_fallback", code="claude-3-5-sonnet", not_code="gpt-4")
    ]
)

# Priority: Task rules first, then code detection
# 1. If task="debug" -> claude-3-5-sonnet (regardless of content)
# 2. Else if content contains code -> claude-3-5-sonnet  
# 3. Else -> gpt-4
```

#### Direct Model Selection

You can also use the router directly for model selection:

```python
# Direct router usage
request_data = {
    "messages": [{"role": "user", "content": "def hello(): print('world')"}],
    "task": "coding"
}

selected_model = router.select_model(request_data)
print(f"Selected: {selected_model}")  # Output: claude-3-5-sonnet
```

### Examples

See the `example_*.py` files in the `examples/` directory for comprehensive examples:

- `examples/example_code_rule.py` - CodeRule functionality and integration
- `examples/example_rule_based_routing.py` - Rule-based routing examples  
- `examples/example_complete_system.py` - Complete system integration
- `examples/example_usage.py` - Basic usage patterns
- `examples/example_logging.py` - Logging system demonstration

Run any example:
```bash
cd examples
python example_code_rule.py
```

## Logging

Deimos Router includes a comprehensive logging system that automatically captures all requests and responses, including routing decisions, performance metrics, and cost estimates.

### Automatic Logging

By default, logging is **enabled** and will automatically log:
- All chat completion requests (both router and direct model calls)
- Routing decisions and explanations
- Request and response content
- Performance metrics (latency)
- Token usage and cost estimates
- Error information when requests fail

Logs are stored in JSON Lines format in the `./logs/` directory with daily rotation (e.g., `deimos-logs-2025-01-27.jsonl`).

### Log Entry Format

Each log entry contains comprehensive information:

```json
{
  "timestamp": "2025-01-27T10:30:00Z",
  "request_id": "uuid",
  "router_name": "my_router",
  "selected_model": "claude-3-5-sonnet",
  "routing_explanation": [
    {
      "rule_type": "CodeRule",
      "rule_name": "code_detector",
      "rule_trigger": "python_code_detected",
      "decision": "claude-3-5-sonnet"
    }
  ],
  "request": {
    "messages": [{"role": "user", "content": "def hello(): print('world')"}],
    "task": "coding"
  },
  "response": {
    "model": "claude-3-5-sonnet",
    "choices": [
      {
        "message": {
          "role": "assistant",
          "content": "This function prints 'world' when called."
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 15,
      "completion_tokens": 12,
      "total_tokens": 27
    }
  },
  "latency_ms": 1250,
  "tokens": {"prompt": 15, "completion": 12, "total": 27},
  "cost": 0.000405,
  "cost_estimated": true,
  "cost_source": "token_calculation",
  "status": "success"
}
```

### Configuring Logging

#### Environment Variables

```bash
export DEIMOS_LOGGING_ENABLED=true          # Enable/disable logging
export DEIMOS_LOG_DIRECTORY="./logs"        # Log directory
export DEIMOS_LOG_LEVEL="full"              # Log level (currently only "full")
```

#### Configuration File

Add a `logging` section to your `secrets.json` or `config.json`:

```json
{
  "api_url": "https://your-api-endpoint.com/api/v1",
  "api_key": "your-api-key-here",
  "logging": {
    "enabled": true,
    "directory": "./logs",
    "level": "full",
    "custom_pricing": {
      "gpt-4": {"input": 0.03, "output": 0.06},
      "claude-3-5-sonnet": {"input": 0.003, "output": 0.015}
    }
  }
}
```

#### Programmatic Configuration

```python
from deimos_router.logging.logger import configure_logging

# Configure logging programmatically
configure_logging(
    enabled=True,
    log_directory="./custom_logs",
    custom_pricing={
        "my-custom-model": {"input": 0.01, "output": 0.02}
    }
)
```

### Disabling Logging

To disable logging completely:

**Option 1: Environment Variable**
```bash
export DEIMOS_LOGGING_ENABLED=false
```

**Option 2: Configuration File**
```json
{
  "logging": {
    "enabled": false
  }
}
```

**Option 3: Programmatically**
```python
from deimos_router.logging.logger import configure_logging

configure_logging(enabled=False)
```

### Cost Tracking

The logging system automatically tracks costs by:

1. **Extracting actual costs** from API responses when available
2. **Estimating costs** based on token usage and model pricing when actual costs aren't provided
3. **Using configurable pricing** for custom models or updated pricing

Each log entry includes:
- `cost`: The calculated cost (actual or estimated)
- `cost_estimated`: Boolean indicating if the cost was estimated
- `cost_source`: Source of cost data ("api_response" or "token_calculation")

### Reading Log Files

Log files are stored in JSON Lines format for easy processing:

```python
import json
from pathlib import Path

# Read today's log file
log_file = Path("./logs/deimos-logs-2025-01-27.jsonl")
if log_file.exists():
    with open(log_file, 'r') as f:
        for line in f:
            entry = json.loads(line)
            print(f"Request {entry['request_id']}: {entry['selected_model']} - ${entry['cost']:.6f}")
```

Or use the built-in logger methods:

```python
from deimos_router.logging.logger import get_logger
from deimos_router.logging.json_logger import JSONFileLogger

logger = get_logger()
if isinstance(logger.backend, JSONFileLogger):
    # Read all entries
    entries = logger.backend.read_log_entries()
    
    # Get log files
    log_files = logger.backend.get_log_files()
```

### Log Analysis

The JSON format makes it easy to analyze your usage:

```python
import json
from collections import defaultdict
from pathlib import Path

def analyze_logs(log_directory="./logs"):
    """Analyze log files for usage statistics."""
    stats = {
        'total_requests': 0,
        'total_cost': 0,
        'model_usage': defaultdict(int),
        'router_usage': defaultdict(int),
        'avg_latency': 0
    }
    
    latencies = []
    
    for log_file in Path(log_directory).glob("deimos-logs-*.jsonl"):
        with open(log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                
                stats['total_requests'] += 1
                if entry.get('cost'):
                    stats['total_cost'] += entry['cost']
                
                stats['model_usage'][entry['selected_model']] += 1
                stats['router_usage'][entry.get('router_name', 'direct')] += 1
                
                if entry.get('latency_ms'):
                    latencies.append(entry['latency_ms'])
    
    if latencies:
        stats['avg_latency'] = sum(latencies) / len(latencies)
    
    return stats

# Usage
stats = analyze_logs()
print(f"Total requests: {stats['total_requests']}")
print(f"Total cost: ${stats['total_cost']:.6f}")
print(f"Average latency: {stats['avg_latency']:.2f}ms")
```

## Development

### Setting up the development environment

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv sync --dev
```

4. **Configure your API credentials for development:**
   
   Edit the `secrets.json` file in the project root and add your actual API credentials:
   ```json
   {
     "api_url": "https://your-actual-api-endpoint.com/api/v1",
     "api_key": "your-actual-api-key-here"
   }
   ```
   
   **Note:** This file is already created for you and is excluded from git commits, so your credentials will remain private.

   **Alternative:** You can also set environment variables instead:
   ```bash
   export DEIMOS_API_URL="https://your-actual-api-endpoint.com/api/v1"
   export DEIMOS_API_KEY="your-actual-api-key-here"
   ```

### Running tests

```bash
pytest
```

### Project Structure

```
deimos-router/
├── src/
│   └── deimos_router/
│       ├── __init__.py
│       ├── config.py
│       └── py.typed
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   └── test_deimos_router.py
├── secrets.example.json
├── pyproject.toml
├── README.md
├── .gitignore
└── uv.lock
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### [0.1.0] - 2025-08-26

- Initial project setup
- Basic package structure
- Development environment configuration
