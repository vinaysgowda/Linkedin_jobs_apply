from pathlib import Path

from job_apply_bot.adapters.generic import GenericPlaywrightAdapter
from job_apply_bot.models import ApplicantProfile, JobContext


def test_resolve_value_prefers_profile_then_dotted_answers(tmp_path: Path) -> None:
    resume = tmp_path / "resume.txt"
    resume.write_text("resume", encoding="utf-8")

    profile = ApplicantProfile(
        full_name="Demo User",
        email="demo@example.com",
        phone="123",
        country="India",
        city="Chennai",
        skills=["Python", "FastAPI"],
        resume_path=resume,
        answers={"notice_period": "30 days"},
    )
    job = JobContext(
        title="Backend Engineer",
        company="Example",
        country="India",
        apply_url="http://localhost/form",
        answers={"expected_salary": "Negotiable"},
    )

    assert GenericPlaywrightAdapter.resolve_value("full_name", profile, job) == "Demo User"
    assert GenericPlaywrightAdapter.resolve_value("answers.notice_period", profile, job) == "30 days"
    assert GenericPlaywrightAdapter.resolve_value("answers.expected_salary", profile, job) == "Negotiable"
    assert GenericPlaywrightAdapter.resolve_value("skills_csv", profile, job) == "Python, FastAPI"

