"""Policy Validation Rules
Defines privacy, security, and schema constraint rules for egress validation.
"""

from dataclasses import dataclass
from typing import Set
from app.schemas.policy import ViolationSeverityEnum


@dataclass
class PolicyConfig:
    max_payload_size_bytes: int = 2 * 1024 * 1024  # 2 MB limit
    max_logs_count: int = 500                      # 500 logs per submission batch
    require_sanitization: bool = True
    disallow_prohibited_fields: bool = True
    prohibited_fields: Set[str] = None

    def __post_init__(self):
        if self.prohibited_fields is None:
            self.prohibited_fields = {
                "raw_headers",
                "internal_env",
                "debug_stacktrace",
                "cookie",
                "session_cookie",
                "process_environ",
                "raw_sql_query",
            }


DEFAULT_POLICY_CONFIG = PolicyConfig()
