"""Data Filtering Rules and Configuration
Defines allowlists, denylists, and log-level filtering specifications.
"""

from dataclasses import dataclass, field
from typing import List, Set


DEFAULT_DENIED_FIELDS: Set[str] = {
    "raw_headers",
    "internal_env",
    "debug_stacktrace",
    "cookie",
    "session_cookie",
    "set_cookie",
    "client_ip_forwarded_for",
    "memory_dump",
    "raw_sql_query",
    "process_environ",
}

DEFAULT_MIN_LOG_LEVEL = "INFO"

LOG_LEVEL_ORDER = {
    "DEBUG": 10,
    "INFO": 20,
    "WARN": 30,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "FATAL": 50,
}


@dataclass
class FilterConfig:
    denied_fields: Set[str] = field(default_factory=lambda: set(DEFAULT_DENIED_FIELDS))
    allowlist_enabled: bool = False
    allowed_fields: Set[str] = field(default_factory=set)
    min_log_level: str = DEFAULT_MIN_LOG_LEVEL
    filter_empty_logs: bool = True
