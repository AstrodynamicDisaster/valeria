"""
State helpers for the Valeria agent.

Defines lightweight dataclasses used to track long-running operations without
relying on mutable dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional


@dataclass
class ProcessingState:
    """Top-level state that mirrors the legacy `processing_state` dictionary."""

    client_id: Optional[str] = None
    vida_laboral_processed: bool = False
    employees_created: int = 0
    nominas_processed: int = 0

    def reset(self) -> None:
        """Reset counters while keeping the current client context."""
        client_id = self.client_id
        self.__dict__.update(
            {
                "client_id": client_id,
                "vida_laboral_processed": False,
                "employees_created": 0,
                "nominas_processed": 0,
            }
        )

    def to_dict(self) -> Dict[str, object]:
        """Return a serialisable representation (for API responses)."""
        return asdict(self)


@dataclass
class VidaLaboralContext:
    """Per-run context for vida laboral CSV processing."""

    processing_state: ProcessingState
    employees_created: int = 0
    employees_updated: int = 0
    vacation_periods_created: int = 0
    create_employees: bool = True  # Set to False to only match existing employees
    periods_created: int = 0  # Track EmployeePeriod records created
    employees_not_found: int = 0  # Track skipped records when create_employees=False


@dataclass
class PayslipContext:
    """Per-run context for payroll ingestion."""

    processing_state: ProcessingState
    processed_count: int = 0
    failed_count: int = 0
