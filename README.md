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

## Usage

```python
from deimos_router import hello

print(hello())  # Output: Hello from deimos-router!
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
│       └── py.typed
├── tests/
│   ├── __init__.py
│   └── test_deimos_router.py
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
