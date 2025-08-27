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

# Register the router
register_router(router)

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

See the `example_*.py` files in the project root for comprehensive examples:

- `example_code_rule.py` - CodeRule functionality and integration
- `example_rule_based_routing.py` - Rule-based routing examples  
- `example_complete_system.py` - Complete system integration
- `example_usage.py` - Basic usage patterns

Run any example:
```bash
python example_code_rule.py
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
