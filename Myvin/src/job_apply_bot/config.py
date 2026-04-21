from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from .models import ApplicantProfile, JobContext, SiteConfig

T = TypeVar("T", bound=BaseModel)
_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)}")


def _substitute_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env(item) for item in value]
    if isinstance(value, str):
        return _ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), match.group(0)), value)
    return value


def _load_raw_data(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def load_model(path: str | Path, model_type: type[T]) -> T:
    file_path = Path(path).expanduser().resolve()
    raw = _load_raw_data(file_path)
    prepared = _substitute_env(raw)
    if model_type is ApplicantProfile and "resume_path" in prepared:
        resume_path = Path(prepared["resume_path"]).expanduser()
        if not resume_path.is_absolute():
            prepared["resume_path"] = str((file_path.parent / resume_path).resolve())
    return model_type.model_validate(prepared)


def load_applicant_profile(path: str | Path) -> ApplicantProfile:
    return load_model(path, ApplicantProfile)


def load_job_context(path: str | Path) -> JobContext:
    return load_model(path, JobContext)


def load_job_contexts(path: str | Path) -> list[JobContext]:
    file_path = Path(path).expanduser().resolve()
    raw = _substitute_env(_load_raw_data(file_path))
    if isinstance(raw, list):
        return [JobContext.model_validate(item) for item in raw]
    if isinstance(raw, dict) and isinstance(raw.get("jobs"), list):
        return [JobContext.model_validate(item) for item in raw["jobs"]]
    return [JobContext.model_validate(raw)]


def load_site_config(path: str | Path) -> SiteConfig:
    return load_model(path, SiteConfig)



