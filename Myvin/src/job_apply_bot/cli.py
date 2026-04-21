from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from job_apply_bot.config import load_applicant_profile, load_job_context, load_job_contexts, load_site_config
from job_apply_bot.adapters.linkedin import parse_keywords
from job_apply_bot.models import ApplicantProfile, JobContext, RunOptions
from job_apply_bot.runner import run_application, run_linkedin_batch

app = typer.Typer(help="Auto-fill job applications from a structured applicant profile and site config.")


def _load_inputs(profile_path: Path, job_path: Path, site_path: Path) -> tuple:
    profile = load_applicant_profile(profile_path)
    job = load_job_context(job_path)
    site = load_site_config(site_path)
    return profile, job, site


def _prompt_non_empty(label: str) -> str:
    value = typer.prompt(label).strip()
    if not value:
        raise typer.BadParameter(f"{label} cannot be empty")
    return value


def _resolve_resume_path(resume_path: Optional[Path]) -> Path:
    candidate = resume_path
    if candidate is None:
        candidate = Path(_prompt_non_empty("Resume path (PDF/DOC/TXT)"))
    resolved = candidate.expanduser().resolve()
    if not resolved.exists():
        raise typer.BadParameter(f"Resume file does not exist: {resolved}")
    return resolved


def _build_profile_from_prompts() -> ApplicantProfile:
    full_name = _prompt_non_empty("Full name")
    email = _prompt_non_empty("Candidate email")
    phone = _prompt_non_empty("Phone")
    country = _prompt_non_empty("Country")
    city = typer.prompt("City", default="").strip() or None
    resume_path = _resolve_resume_path(None)

    linkedin = typer.prompt("LinkedIn profile URL (optional)", default="").strip() or None
    summary = typer.prompt("Short summary (optional)", default="").strip() or None
    skills_csv = typer.prompt("Skills comma separated (optional)", default="").strip()
    skills = [item.strip() for item in skills_csv.split(",") if item.strip()]

    signup_fields: dict[str, str] = {}
    if typer.confirm("Does this site require account creation before applying?", default=False):
        signup_fields = {
            "email": email,
            "full_name": full_name,
            "phone": phone,
            "country": country,
            "city": city or "",
            "resume_path": str(resume_path),
        }
        username = typer.prompt("Signup username (optional)", default="").strip()
        if username:
            signup_fields["username"] = username

    return ApplicantProfile(
        full_name=full_name,
        email=email,
        phone=phone,
        country=country,
        city=city,
        linkedin=linkedin,
        summary=summary,
        skills=skills,
        resume_path=resume_path,
        signup_fields=signup_fields,
    )


def _prompt_single_job(default_country: str) -> JobContext:
    title = _prompt_non_empty("Job title")
    company = _prompt_non_empty("Company")
    country = typer.prompt("Job country", default=default_country).strip() or default_country
    apply_url = _prompt_non_empty("Direct apply URL")
    location = typer.prompt("Location (optional)", default="").strip() or None
    return JobContext(
        title=title,
        company=company,
        country=country,
        apply_url=apply_url,
        location=location,
    )


def _run_for_jobs(
    profile_data: ApplicantProfile,
    jobs: list[JobContext],
    site_path: Path,
    country: Optional[str],
    headed: bool,
    slow_mo_ms: int,
    auto_submit: bool,
) -> None:
    site_data = load_site_config(site_path)
    results = []
    for job in jobs:
        prepared_job = _apply_country_override(job, country)
        _guard_country(profile_data.country, prepared_job.country)
        result = run_application(
            profile=profile_data,
            job=prepared_job,
            site=site_data,
            options=RunOptions(headless=not headed, slow_mo_ms=slow_mo_ms, auto_submit=auto_submit),
        )
        results.append(
            {
                "job": f"{prepared_job.title} @ {prepared_job.company}",
                "country": prepared_job.country,
                "success": result.success,
                "submitted": result.submitted,
                "message": result.message,
                "url": result.visited_url,
            }
        )
    typer.echo(typer.style("Batch run completed", fg=typer.colors.GREEN))
    typer.echo(json.dumps(results, indent=2))


def _apply_country_override(job: JobContext, country: Optional[str]) -> JobContext:
    if not country:
        return job
    return job.model_copy(update={"country": country})


def _guard_country(profile_country: str, job_country: str) -> None:
    if profile_country.strip().lower() != job_country.strip().lower():
        raise typer.BadParameter(
            f"Applicant country '{profile_country}' does not match requested job country '{job_country}'."
        )


@app.command()
def preview(
    profile: Path = typer.Option(..., exists=True, readable=True, help="Path to applicant YAML or JSON file."),
    job: Path = typer.Option(..., exists=True, readable=True, help="Path to job YAML or JSON file."),
    site: Path = typer.Option(..., exists=True, readable=True, help="Path to site config YAML or JSON file."),
    country: Optional[str] = typer.Option(None, help="Optional country override for the target job."),
    headed: bool = typer.Option(False, help="Open a visible browser window instead of headless mode."),
    slow_mo_ms: int = typer.Option(0, min=0, help="Optional Playwright slow motion in milliseconds."),
) -> None:
    """Fill the form without submitting it."""

    profile_data, job_data, site_data = _load_inputs(profile, job, site)
    job_data = _apply_country_override(job_data, country)
    _guard_country(profile_data.country, job_data.country)

    result = run_application(
        profile=profile_data,
        job=job_data,
        site=site_data,
        options=RunOptions(headless=not headed, slow_mo_ms=slow_mo_ms, auto_submit=False),
    )
    typer.echo(result.model_dump_json(indent=2))


@app.command()
def submit(
    profile: Path = typer.Option(..., exists=True, readable=True, help="Path to applicant YAML or JSON file."),
    job: Path = typer.Option(..., exists=True, readable=True, help="Path to job YAML or JSON file."),
    site: Path = typer.Option(..., exists=True, readable=True, help="Path to site config YAML or JSON file."),
    country: Optional[str] = typer.Option(None, help="Optional country override for the target job."),
    headed: bool = typer.Option(False, help="Open a visible browser window instead of headless mode."),
    slow_mo_ms: int = typer.Option(0, min=0, help="Optional Playwright slow motion in milliseconds."),
    yes: bool = typer.Option(False, "--yes", help="Skip the interactive confirmation prompt."),
) -> None:
    """Fill and submit the application form."""

    profile_data, job_data, site_data = _load_inputs(profile, job, site)
    job_data = _apply_country_override(job_data, country)
    _guard_country(profile_data.country, job_data.country)

    if not yes:
        confirmed = typer.confirm(
            f"Submit application for {job_data.title} at {job_data.company} in {job_data.country}?",
            default=False,
        )
        if not confirmed:
            raise typer.Abort()

    result = run_application(
        profile=profile_data,
        job=job_data,
        site=site_data,
        options=RunOptions(headless=not headed, slow_mo_ms=slow_mo_ms, auto_submit=True),
    )
    typer.echo(result.model_dump_json(indent=2))


@app.command("wizard-apply")
def wizard_apply(
    site: Path = typer.Option(..., exists=True, readable=True, help="Path to site config YAML or JSON file."),
    jobs: Optional[Path] = typer.Option(None, exists=True, readable=True, help="Optional jobs list YAML/JSON file."),
    country: Optional[str] = typer.Option(None, help="Optional country override for all jobs."),
    headed: bool = typer.Option(False, help="Open a visible browser window instead of headless mode."),
    slow_mo_ms: int = typer.Option(0, min=0, help="Optional Playwright slow motion in milliseconds."),
    yes: bool = typer.Option(False, "--yes", help="Skip submit confirmation prompt."),
) -> None:
    """Interactive mode: ask candidate details in terminal and apply to one or many jobs."""

    typer.echo("This wizard asks for your name, email, resume path, and preferences.")
    typer.echo("LinkedIn login automation is intentionally disabled; use direct apply URLs in jobs input.")

    profile_data = _build_profile_from_prompts()

    if jobs:
        job_items = load_job_contexts(jobs)
    else:
        job_items = [_prompt_single_job(default_country=profile_data.country)]

    if not yes:
        confirmed = typer.confirm(
            f"Proceed to apply to {len(job_items)} job(s) using {profile_data.email}?",
            default=False,
        )
        if not confirmed:
            raise typer.Abort()

    _run_for_jobs(
        profile_data=profile_data,
        jobs=job_items,
        site_path=site,
        country=country,
        headed=headed,
        slow_mo_ms=slow_mo_ms,
        auto_submit=True,
    )


@app.command("linkedin-batch")
def linkedin_batch(
    keywords: str = typer.Option(..., help="Comma-separated job keywords, e.g. 'python,backend,automation'."),
    location: str = typer.Option(..., help="Preferred job location, e.g. 'Bengaluru, India'."),
    max_jobs: int = typer.Option(10, min=1, max=100, help="Maximum matching LinkedIn jobs to process."),
    resume_path: Optional[Path] = typer.Option(
        None,
        help="Resume path for Easy Apply uploads. If omitted, command will prompt.",
    ),
    dry_run: bool = typer.Option(False, help="Only detect matching Easy Apply jobs; do not submit."),
    slow_mo_ms: int = typer.Option(100, min=0, help="Playwright slow motion in milliseconds."),
) -> None:
    """Navigate LinkedIn Jobs by keyword/location and process matching Easy Apply jobs in batch."""

    parsed_keywords = parse_keywords(keywords)
    if not parsed_keywords:
        raise typer.BadParameter("At least one keyword is required.")
    resolved_resume = _resolve_resume_path(resume_path)

    typer.echo("A browser window will open. Login manually to LinkedIn, then continue in terminal.")
    results = run_linkedin_batch(
        keywords=parsed_keywords,
        location=location,
        max_jobs=max_jobs,
        resume_path=resolved_resume,
        options=RunOptions(headless=False, slow_mo_ms=slow_mo_ms, auto_submit=not dry_run),
    )

    typer.echo(json.dumps([item.model_dump() for item in results], indent=2))


if __name__ == "__main__":
    app()



