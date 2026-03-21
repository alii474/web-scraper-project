# src/web/__init__.py
"""
Web application components.

This module contains Flask web application functionality including:
- REST API endpoints
- Real-time monitoring dashboard
- File download capabilities
- Configuration management
"""

from .flask_app import create_app, run_web_app

__all__ = [
    'create_app',
    'run_web_app'
]
