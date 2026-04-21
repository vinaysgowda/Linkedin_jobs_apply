from pathlib import Path

from job_apply_bot.config import load_applicant_profile, load_job_contexts


def test_profile_loader_resolves_relative_resume_and_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("APPLICANT_EMAIL", "candidate@example.com")

    resume = tmp_path / "resume.pdf"
    resume.write_text("demo resume", encoding="utf-8")

    profile_file = tmp_path / "profile.yaml"
    profile_file.write_text(
        """
full_name: Demo User
email: ${APPLICANT_EMAIL}
phone: "+1-123"
country: India
city: Chennai
resume_path: ./resume.pdf
""".strip(),
        encoding="utf-8",
    )

    profile = load_applicant_profile(profile_file)

    assert profile.email == "candidate@example.com"
    assert profile.resume_path == resume.resolve()


def test_load_job_contexts_from_jobs_list(tmp_path: Path) -> None:
    jobs_file = tmp_path / "jobs.yaml"
    jobs_file.write_text(
        """
jobs:
  - title: Python Engineer
    company: Demo One
    country: India
    apply_url: https://example.com/apply/1
  - title: Backend Engineer
    company: Demo Two
    country: India
    apply_url: https://example.com/apply/2
""".strip(),
        encoding="utf-8",
    )

    jobs = load_job_contexts(jobs_file)

    assert len(jobs) == 2
    assert jobs[0].company == "Demo One"
    assert jobs[1].title == "Backend Engineer"


