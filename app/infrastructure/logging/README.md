# Unified Logging System

## Tổng quan

Unified Logging System cung cấp một cách thống nhất để log across toàn bộ dự án, tuân thủ Clean Architecture principles.

## Features

- **Structured Logging**: Log với context metadata
- **Layer-aware**: Tự động tag theo layer (domain, application, infrastructure, interfaces)
- **Contextual Logging**: Rich context information
- **Singleton Pattern**: Consistent configuration
- **Backward Compatibility**: Tương thích với existing code

## Usage

### Basic Usage

```python
from app.infrastructure.logging.logger import get_logger

# Get logger với context
logger = get_logger(
    name="my_component",
    layer="application",
    component="use_cases"
)

logger.info("Message")
logger.error("Error message")
```

### Advanced Usage với Context

```python
# Create logger với rich context
logger = get_logger(
    name="destination_service",
    layer="application",
    component="use_cases",
    entity_id="dest_123",
    operation="save_destination",
    user_id="user_456"
)

# Log với additional context
logger.info(
    "Destination saved successfully",
    extra_context={
        "destination_name": "Nhà hàng ABC",
        "coordinates": "10.7769,106.7009"
    }
)
```

### Contextual Logging

```python
# Base logger
base_logger = get_logger(
    name="service",
    layer="application",
    component="use_cases"
)

# Create contextual logger
user_logger = base_logger.with_context(
    user_id="user_123",
    operation="save_destination"
)

user_logger.info("User operation started")
```

## Layer-specific Usage

### Domain Layer

```python
# Domain entities
logger = get_logger(
    name="domain_errors",
    layer="domain",
    component="validation",
    entity_id=entity_id,
    field=field_name
)

logger.error("Domain validation failed")
```

### Application Layer

```python
# Use cases
logger = get_logger(
    name="use_cases",
    layer="application",
    component="use_cases",
    operation="save_destination"
)

logger.info("Use case started")
```

### Infrastructure Layer

```python
# Database operations
logger = get_logger(
    name="database",
    layer="infrastructure",
    component="database",
    operation="connect"
)

logger.info("Database connection established")
```

### Interface Layer

```python
# MCP interface
logger = get_logger(
    name="mcp",
    layer="interfaces",
    component="mcp",
    request_id="req_123"
)

logger.info("MCP request received")
```

## Configuration

### Environment Variables

```bash
# Set log level
export LOG_LEVEL=INFO

# Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### File Logging

```python
from app.infrastructure.logging.logger import get_logger

# Configure file logging
logger = get_logger()
logger.configure_file_logging(
    log_file="app.log",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5
)
```

## Log Format

```
2025-09-26 17:07:44,964 - logger_name - INFO - [layer=domain component=entities entity_id=test_entity] Message
```

### Context Information

- **layer**: domain, application, infrastructure, interfaces
- **component**: Specific component name
- **entity_id**: Entity identifier
- **operation**: Operation being performed
- **user_id**: User identifier
- **request_id**: Request identifier
- **field**: Field name (for validation errors)
- **error_type**: Error type (for domain errors)

## Benefits

1. **Consistency**: Uniform logging across all layers
2. **Rich Context**: Detailed metadata for debugging
3. **Layer Awareness**: Easy to filter logs by layer
4. **Structured Data**: Machine-readable log format
5. **Performance**: Singleton pattern for efficiency
6. **Flexibility**: Easy to extend with new context fields

## Migration từ Old Logger

### Before (Old Logger)

```python
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

### After (Unified Logger)

```python
from app.infrastructure.logging.logger import get_logger

logger = get_logger(
    name=__name__,
    layer="application",
    component="use_cases"
)
logger.info("Message")
```

## Best Practices

1. **Always specify layer**: Helps with log filtering
2. **Use meaningful component names**: Makes logs easier to understand
3. **Include entity_id when available**: Helps track specific entities
4. **Use contextual logging**: For related operations
5. **Log at appropriate levels**: DEBUG for development, INFO for normal operations, ERROR for errors

## Examples

### Domain Entity Logging

```python
# In domain entities
logger = get_logger(
    name="domain_errors",
    layer="domain",
    component="validation",
    entity_id=self.id,
    field="name"
)

logger.error("Validation failed")
```

### Use Case Logging

```python
# In use cases
logger = get_logger(
    name="use_cases",
    layer="application",
    component="use_cases",
    operation="save_destination"
)

logger.info("Use case started")
logger.info("Use case completed")
```

### Infrastructure Logging

```python
# In infrastructure
logger = get_logger(
    name="database",
    layer="infrastructure",
    component="database",
    operation="connect"
)

logger.info("Database connection established")
```

### Interface Logging

```python
# In interfaces
logger = get_logger(
    name="mcp",
    layer="interfaces",
    component="mcp",
    request_id=request_id
)

logger.info("MCP request received")
```
