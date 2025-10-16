"""
Service layer for API business logic.

This package implements the Service Layer pattern with Dependency Injection:
- Services contain business logic
- Repositories handle data access
- Container manages dependencies
"""

from .code_execution_service import CodeExecutionService
from .container import ServiceContainer, container

__all__ = [
    'CodeExecutionService',
    'ServiceContainer',
    'container',
]