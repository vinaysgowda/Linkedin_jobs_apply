from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApplicantProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    full_name: str
    email: str
    phone: str
    country: str
    city: str | None = None
    summary: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None
    current_title: str | None = None
    years_experience: int | None = None
    skills: list[str] = Field(default_factory=list)
    work_authorized: bool = True
    cover_letter: str | None = None
    answers: dict[str, Any] = Field(default_factory=dict)
    signup_fields: dict[str, Any] = Field(default_factory=dict)
    resume_path: Path

    @field_validator("resume_path")
    @classmethod
    def expand_resume_path(cls, value: Path) -> Path:
        return value.expanduser()


class JobContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str
    company: str
    country: str
    location: str | None = None
    apply_url: str
    work_mode: str | None = None
    answers: dict[str, Any] = Field(default_factory=dict)


class JobList(BaseModel):
    jobs: list[JobContext] = Field(default_factory=list)


class SiteConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    start_url: str | None = None
    field_selectors: dict[str, str] = Field(default_factory=dict)
    select_selectors: dict[str, str] = Field(default_factory=dict)
    checkbox_selectors: dict[str, str] = Field(default_factory=dict)
    upload_selectors: dict[str, str] = Field(default_factory=dict)
    submit_selector: str | None = None
    success_text: str | None = None
    success_selector: str | None = None
    pre_submit_delay_ms: int = 300


class RunOptions(BaseModel):
    headless: bool = True
    slow_mo_ms: int = 0
    auto_submit: bool = False
    timeout_ms: int = 15_000


class ApplicationResult(BaseModel):
    success: bool
    submitted: bool
    message: str
    visited_url: str
    filled_fields: list[str] = Field(default_factory=list)


