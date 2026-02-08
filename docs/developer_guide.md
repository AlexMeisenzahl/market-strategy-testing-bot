# Developer Guide

Guide for developers contributing to the Market Strategy Testing Bot.

## Project Structure

```
market-strategy-testing-bot/
├── apis/                      # External API clients
│   ├── binance_client.py
│   ├── coingecko_client.py
│   └── price_aggregator.py
├── dashboard/                 # Web dashboard
│   ├── app.py                # Flask application
│   ├── services/             # Dashboard services
│   ├── static/               # CSS, JS, images
│   └── templates/            # HTML templates
├── database/                  # Database models
│   └── settings_models.py    # SQLite models
├── docs/                      # Documentation
├── migrations/                # Database migrations
│   └── versions/
├── services/                  # Core services
│   ├── notification_service.py
│   ├── health_check.py
│   ├── audit_logger.py
│   └── strategy_analytics.py
├── strategies/                # Trading strategies
├── tests/                     # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures.py
├── utils/                     # Utilities
│   ├── config_validator.py
│   ├── api_response.py
│   ├── error_handlers.py
│   └── rate_limiter.py
├── config.yaml               # Configuration
└── requirements.txt          # Dependencies
```

---

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-username/market-strategy-testing-bot.git
cd market-strategy-testing-bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Development Tools

```bash
pip install black flake8 mypy pytest pytest-cov
```

### 5. Setup Pre-commit Hooks

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
black --check .
flake8 .
mypy .
pytest
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Architecture Overview

### Data Flow

```
External APIs → API Clients → Data Parser → Analytics → Dashboard
                                    ↓
                            Notification Service
```

### Key Components

**API Clients** (`apis/`)
- Handle external API communication
- Implement rate limiting
- Provide data normalization

**Services** (`services/`)
- Business logic layer
- Analytics calculations
- Notification routing
- Health monitoring

**Dashboard** (`dashboard/`)
- Flask web application
- REST API endpoints
- Real-time updates
- User interface

**Database** (`database/`)
- SQLite for settings
- Thread-safe connections
- Model classes

---

## Coding Standards

### Python Style

Follow PEP 8 with these additions:

```python
# Import order
import standard_library
import third_party
import local_modules

# Docstrings (Google style)
def function_name(arg1: str, arg2: int) -> bool:
    """
    Short description.
    
    Longer description if needed.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When validation fails
        
    Example:
        >>> function_name("test", 42)
        True
    """
    pass

# Type hints everywhere
from typing import Dict, List, Optional, Any

def process_data(
    data: Dict[str, Any],
    limit: Optional[int] = None
) -> List[str]:
    pass

# Constants in UPPER_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 10

# Classes in PascalCase
class DataProcessor:
    pass

# Functions/variables in snake_case
def calculate_profit_margin():
    trade_size = 100
```

### Code Formatting

```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy .
```

---

## Adding New Features

### 1. New API Client

Create `apis/new_api_client.py`:

```python
"""
New API Client

Description of the API and its purpose.
"""

import requests
from typing import Dict, Any
from utils.rate_limiter import RateLimiter
from utils.error_handlers import handle_api_error


class NewAPIClient:
    """Client for New API."""
    
    BASE_URL = "https://api.example.com"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize client.
        
        Args:
            api_key: Optional API key
        """
        self.api_key = api_key
        self.rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
    
    @handle_api_error(default_return={})
    def get_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch data for symbol.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Data dictionary
        """
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.BASE_URL}/data/{symbol}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return response.json()
```

### 2. New Service

Create `services/new_service.py`:

```python
"""
New Service

Description of service functionality.
"""

import logging
from typing import Dict, Any
from database.settings_models import get_connection


logger = logging.getLogger(__name__)


class NewService:
    """Service for new functionality."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data.
        
        Args:
            data: Input data
            
        Returns:
            Processed results
            
        Raises:
            ValueError: If data is invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        # Implementation
        result = {}
        
        self.logger.debug(f"Processed {len(data)} items")
        return result
```

### 3. New API Endpoint

Add to `dashboard/app.py`:

```python
@app.route('/api/new_endpoint', methods=['GET'])
@timed_endpoint
@handle_api_errors
def new_endpoint():
    """
    Description of endpoint.
    
    Query Parameters:
        param1 (str): Description
        param2 (int, optional): Description
        
    Returns:
        JSON response with data
    """
    param1 = request.args.get('param1')
    param2 = request.args.get('param2', type=int, default=10)
    
    # Validate
    if not param1:
        return APIResponse.error('param1 is required', status_code=400)
    
    # Process
    result = process_data(param1, param2)
    
    # Return
    return APIResponse.success(data=result)
```

### 4. New Strategy

Create `strategies/new_strategy.py`:

```python
"""
New Trading Strategy

Description of strategy logic.
"""

from typing import Dict, List, Any
from strategies.base_strategy import BaseStrategy


class NewStrategy(BaseStrategy):
    """New arbitrage strategy."""
    
    NAME = "New Strategy"
    DESCRIPTION = "Description of strategy"
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize strategy."""
        super().__init__(config)
        self.min_profit = config.get('min_profit', 0.02)
    
    def find_opportunities(
        self,
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find arbitrage opportunities.
        
        Args:
            market_data: Current market data
            
        Returns:
            List of opportunities
        """
        opportunities = []
        
        # Strategy logic here
        
        return opportunities
    
    def validate_opportunity(
        self,
        opportunity: Dict[str, Any]
    ) -> bool:
        """
        Validate if opportunity is executable.
        
        Args:
            opportunity: Opportunity to validate
            
        Returns:
            True if valid
        """
        return opportunity.get('profit', 0) >= self.min_profit
```

---

## Testing

### Writing Tests

Create `tests/unit/test_new_feature.py`:

```python
"""Tests for new feature."""

import pytest
from services.new_service import NewService


class TestNewService:
    """Tests for NewService class."""
    
    def test_basic_functionality(self):
        """Test basic service functionality."""
        service = NewService({})
        result = service.process({'key': 'value'})
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling."""
        service = NewService({})
        with pytest.raises(ValueError):
            service.process({})
    
    def test_with_mock(self, mocker):
        """Test with mocked dependencies."""
        mock_api = mocker.patch('services.new_service.api_call')
        mock_api.return_value = {'data': 'test'}
        
        service = NewService({})
        result = service.process({'key': 'value'})
        
        assert result['data'] == 'test'
        mock_api.assert_called_once()
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_new_feature.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "test_validation"
```

---

## Database

### Adding New Model

Update `database/settings_models.py`:

```python
def init_db():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # New table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS new_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_settings(user_id)
        )
    ''')
    
    conn.commit()


class NewModel:
    """New model class."""
    
    @staticmethod
    def create(name: str, value: float) -> int:
        """Create new record."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO new_table (name, value) VALUES (?, ?)',
            (name, value)
        )
        conn.commit()
        
        return cursor.lastrowid
```

### Creating Migrations

Create `migrations/versions/002_new_feature.py`:

```python
"""
Add new_table

Revision ID: 002
Revises: 001
Create Date: 2026-02-08
"""

from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'


def upgrade():
    """Create new table."""
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('value', sa.Float(), nullable=True)
    )


def downgrade():
    """Drop new table."""
    op.drop_table('new_table')
```

---

## API Development

### Standard Response Format

Always use `APIResponse` helper:

```python
from utils.api_response import APIResponse

# Success
return APIResponse.success(data={'key': 'value'})

# Error
return APIResponse.error('Error message', status_code=400)

# Paginated
return APIResponse.paginated(
    data=items,
    page=1,
    per_page=50,
    total=100
)
```

### Error Handling

```python
from utils.api_response import handle_api_errors

@app.route('/api/endpoint')
@handle_api_errors
def endpoint():
    # Any exception is caught and formatted
    raise ValueError("Invalid input")  # Returns 400
    raise PermissionError("Denied")    # Returns 403
    raise FileNotFoundError("Missing") # Returns 404
```

---

## Pull Request Process

### 1. Create Branch

```bash
git checkout -b feature/new-feature
```

### 2. Make Changes

- Write code
- Add tests
- Update documentation

### 3. Run Quality Checks

```bash
# Format
black .

# Lint
flake8 .

# Type check
mypy .

# Test
pytest --cov=.

# Validate config
python -m utils.config_validator config.yaml
```

### 4. Commit

```bash
git add .
git commit -m "Add new feature

- Implemented X
- Added tests for Y
- Updated documentation"
```

### 5. Push and Create PR

```bash
git push origin feature/new-feature
```

Create PR on GitHub with:
- Clear title
- Description of changes
- Test results
- Screenshots (if UI changes)

---

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Debug level
logger.debug("Detailed information")

# Info level
logger.info("General information")

# Warning level
logger.warning("Warning message")

# Error level
logger.error("Error occurred", exc_info=True)
```

### Debug Mode

Run dashboard in debug mode:

```bash
FLASK_DEBUG=true python dashboard/app.py
```

### Using Debugger

```python
import pdb

def buggy_function():
    x = 10
    pdb.set_trace()  # Breakpoint
    y = x * 2
    return y
```

---

## Performance

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
expensive_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Optimization Tips

1. Use database indexes
2. Cache expensive calculations
3. Use batch operations
4. Avoid N+1 queries
5. Profile before optimizing

---

## Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

## Getting Help

- Check existing issues on GitHub
- Review documentation
- Ask in discussions
- Read related code

Happy coding! 🚀
