"""API Layer root package."""

from financial_rag.api.dependencies import (
    LoggerDep,
    SettingsDep,
    get_current_settings,
    get_request_logger,
)
from financial_rag.api.exceptions import register_exception_handlers
from financial_rag.api.middleware import register_middlewares
from financial_rag.api.v1.router import v1_router

__all__ = [
    "LoggerDep",
    "SettingsDep",
    "get_current_settings",
    "get_request_logger",
    "register_exception_handlers",
    "register_middlewares",
    "v1_router",
]
