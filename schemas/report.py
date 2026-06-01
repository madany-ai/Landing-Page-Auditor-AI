"""Report metadata schema."""

from __future__ import annotations
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel


class ReportMeta(BaseModel):
    """Metadata attached to every generated report."""

    url: str
    timestamp: datetime
    output_dir: Path

    model_config = {"arbitrary_types_allowed": True}
