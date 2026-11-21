"""Data Filtering Engine
Removes unnecessary fields, unwanted metadata, and noisy logs while
preserving all essential operational monitoring signals.
"""

from typing import Any, Dict, List, Optional, Tuple
from app.filtering.rules import FilterConfig, LOG_LEVEL_ORDER
from app.schemas.telemetry import TelemetryPayload, LogEntry
from app.core.logging_config import get_logger

logger = get_logger("filtering_engine")


class DataFilterEngine:
    """Filters unwanted metadata and fields from telemetry payloads."""

    def __init__(self, config: Optional[FilterConfig] = None):
        self.config = config or FilterConfig()

    def _filter_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Recursively prune denied fields from a dictionary."""
        cleaned = {}
        pruned_count = 0

        for key, value in data.items():
            lower_key = str(key).lower()
            # 1. Check denylist
            if lower_key in self.config.denied_fields:
                pruned_count += 1
                continue

            # 2. Check allowlist if enabled
            if self.config.allowlist_enabled and self.config.allowed_fields:
                if lower_key not in self.config.allowed_fields:
                    pruned_count += 1
                    continue

            # 3. Recurse if child is dict or list
            if isinstance(value, dict):
                sub_dict, sub_count = self._filter_dict(value)
                cleaned[key] = sub_dict
                pruned_count += sub_count
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, dict):
                        sub_dict, sub_count = self._filter_dict(item)
                        new_list.append(sub_dict)
                        pruned_count += sub_count
                    else:
                        new_list.append(item)
                cleaned[key] = new_list
            else:
                cleaned[key] = value

        return cleaned, pruned_count

    def _should_keep_log(self, entry: LogEntry) -> bool:
        """Evaluate whether a log entry passes log-level and relevance criteria."""
        entry_level = entry.level.upper()
        min_level = self.config.min_log_level.upper()

        entry_val = LOG_LEVEL_ORDER.get(entry_level, 20)
        min_val = LOG_LEVEL_ORDER.get(min_level, 20)

        if entry_val < min_val:
            return False

        if self.config.filter_empty_logs and not entry.message.strip():
            return False

        return True

    def filter_payload(self, payload: TelemetryPayload) -> TelemetryPayload:
        """Apply filtering rules to an entire TelemetryPayload."""
        total_pruned = 0
        total_logs_dropped = 0

        # Filter logs
        filtered_logs: List[LogEntry] = []
        for log in payload.logs:
            if not self._should_keep_log(log):
                total_logs_dropped += 1
                continue

            # Clean log attributes
            cleaned_attrs, pruned = self._filter_dict(log.attributes)
            total_pruned += pruned
            filtered_logs.append(
                LogEntry(
                    timestamp=log.timestamp,
                    level=log.level,
                    message=log.message,
                    service=log.service,
                    event_type=log.event_type,
                    attributes=cleaned_attrs,
                )
            )

        # Filter application raw metrics if present
        app_metrics = payload.application_metrics
        if app_metrics and app_metrics.raw_metrics:
            cleaned_raw, pruned = self._filter_dict(app_metrics.raw_metrics)
            total_pruned += pruned
            app_metrics = app_metrics.model_copy(update={"raw_metrics": cleaned_raw})

        # Filter metadata
        cleaned_meta, pruned = self._filter_dict(payload.metadata)
        total_pruned += pruned

        # Record filtering summary in metadata
        cleaned_meta["filtering_summary"] = {
            "fields_pruned": total_pruned,
            "logs_dropped": total_logs_dropped,
        }

        logger.info(
            f"Filtering complete for {payload.payload_id}: "
            f"pruned_fields={total_pruned}, dropped_logs={total_logs_dropped}"
        )

        return payload.model_copy(
            update={
                "logs": filtered_logs,
                "application_metrics": app_metrics,
                "metadata": cleaned_meta,
            }
        )
