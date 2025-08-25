"""
Data models and classes for the Policy Automation Web UI.

This module contains all data classes and type definitions used throughout
the application for type safety and clear data structure definitions.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WorkflowRun:
    """Represents a GitHub Actions workflow run."""
    id: int
    status: str
    conclusion: Optional[str]
    created_at: str
    updated_at: str
    html_url: str


@dataclass
class GeneratedFile:
    """Represents a generated file available for download."""
    name: str
    path: str
    size: str
    type: str
    download_url: Optional[str] = None
    artifact_id: Optional[str] = None
