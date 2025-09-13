# Deimos Router

A Python routing library for building rule based configurable routing systems.

See `notebooks/deimos-guide.ipynb` for instructions.


## Installation

### Development Installation

1. Clone the repository:
```bash
git clone https://github.com/withmartian/deimos-router
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

#### 1. Secrets File

`secrets.json`

```json
{
  "api_url": "https://api.withmartian.com/v1",
  "api_key": "sk-XXXxXxXxxxxxXXX"
}
```

#### 2. Environment Variables

Set the following environment variables:

```bash
export DEIMOS_API_URL="https://api.withmartian.com/v1"
export DEIMOS_API_KEY="sk-XXXxXxXxxxxxXXX"
```

On Windows:
```cmd
set DEIMOS_API_URL=https://api.withmartian.com/v1
set DEIMOS_API_KEY=sk-XXXxXxXxxxxxXXX
```


#### 3. Home Directory Configuration

You can also place a `secrets.json` file in your home directory (`~/secrets.json`) for system-wide configuration.

