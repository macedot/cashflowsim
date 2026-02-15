# CashflowSim - Agent Guidelines

## Project Overview

CashflowSim is a Streamlit-based cashflow simulation web app. It calculates and visualizes income/expense flows over time.

**Tech Stack**: Python 3.12, Streamlit, Pandas, Altair, Docker  
**Location**: `app/app.py` (single-file application)

---

## Running the Application

### Local Development

```bash
# Install dependencies with uv (recommended, matches Dockerfile)
cd app
uv venv
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt

# Run the app
streamlit run app/app.py
```

### Docker (Production)

```bash
# Build and run
docker-compose up --build

# Or run just the app container
cd app
docker build -t cashflowsim .
docker run -p 8501:8501 cashflowsim
```

---

## Testing

**No tests exist yet.** The project should adopt testing.

### Recommended Setup

```bash
# Install pytest
uv pip install pytest pytest-cov

# Run all tests
pytest

# Run a single test file
pytest tests/test_core.py

# Run tests matching a pattern
pytest -k "test_cashflow"
```

### Test Naming Convention

- Test files: `tests/test_*.py`
- Test functions: `test_function_name_scenario_expected()`

---

## Linting & Formatting

**Not configured yet.** Add these tools to `requirements.txt`:

```bash
# Install (add to requirements.txt: ruff)
uv pip install ruff

# Lint
ruff check app/

# Format
ruff format app/
```

### Recommended `pyproject.toml` config

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
```

---

## Code Style Guidelines

### Imports

```python
# Standard library first, then third-party, then local
import datetime
from dateutil.relativedelta import relativedelta

import altair as alt
import pandas as pd
import streamlit as st

from mymodule import my_function  # local imports
```

### Naming Conventions

- **Functions/variables**: `snake_case` - `def get_next_date()`, `initial_balance_value`
- **Constants**: `UPPER_SNAKE_CASE` - `TODAY`, `INPUT_HEADER`
- **Classes**: `PascalCase` (if used)

### Type Annotations

Use type hints for function signatures:

```python
def get_next_date(current_date: datetime, frequency: str) -> datetime | None:
    ...
```

### Error Handling

- Avoid bare `except:`. Catch specific exceptions
- Use informative error messages

```python
# Good
try:
    df = pd.read_excel(uploadedFile)
except Exception as e:
    st.error(f"Failed to load file: {e}")
    st.stop()
```

### Code Patterns Observed

- **Constants at module level**: All caps for true constants
- **Dictionary for configuration**: Use dict literals for simple configs
- **Early returns**: Return early for error/edge cases
- **Descriptive names**: `generate_cashflows`, `balance_from_cashflows`

---

## Development Workflow

1. **Create a virtual environment**: `uv venv`
2. **Install dependencies**: `uv pip install -r requirements.txt`
3. **Run the app**: `streamlit run app/app.py`
4. **Add tests**: Create `tests/` directory
5. **Lint before committing**: `ruff check .`

---

## Docker Development Notes

- The Dockerfile uses `uv` for fast dependency management
- Streamlit runs on port 8501
- Health check: `curl http://localhost:8501/_stcore/health`

---

## Common Tasks

| Task | Command |
|------|---------|
| Add dependency | Edit `requirements.txt`, then rebuild Docker |
| Add test | Create `tests/test_<module>.py` |
| Fix lint error | `ruff check --fix app/` |
| Format code | `ruff format app/` |

---

## File Structure

```
cashflowsim/
├── app/
│   ├── app.py          # Main application
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yaml
├── nginx/
│   └── nginx.conf
└── AGENTS.md           # This file
```
