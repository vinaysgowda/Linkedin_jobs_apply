from pathlib import Path

import pytest
import typer

from job_apply_bot.cli import _resolve_resume_path


def test_resolve_resume_path_from_option(tmp_path: Path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_text("demo", encoding="utf-8")

    resolved = _resolve_resume_path(resume)

    assert resolved == resume.resolve()


def test_resolve_resume_path_from_prompt(monkeypatch, tmp_path: Path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_text("demo", encoding="utf-8")
    monkeypatch.setattr("job_apply_bot.cli.typer.prompt", lambda _label: str(resume))

    resolved = _resolve_resume_path(None)

    assert resolved == resume.resolve()


def test_resolve_resume_path_raises_when_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.pdf"

    with pytest.raises(typer.BadParameter) as exc:
        _resolve_resume_path(missing)

    assert "Resume file does not exist" in str(exc.value)


