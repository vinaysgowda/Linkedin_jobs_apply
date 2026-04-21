from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from job_apply_bot.adapters.generic import GenericPlaywrightAdapter
from job_apply_bot.adapters.linkedin import LinkedInBatchAdapter
from job_apply_bot.models import ApplicantProfile, ApplicationResult, JobContext, RunOptions, SiteConfig


def run_application(
    profile: ApplicantProfile,
    job: JobContext,
    site: SiteConfig,
    options: RunOptions,
) -> ApplicationResult:
    adapter = GenericPlaywrightAdapter()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=options.headless, slow_mo=options.slow_mo_ms)
        page = browser.new_page()
        try:
            return adapter.apply(page, profile, job, site, options)
        finally:
            browser.close()


def run_linkedin_batch(
    keywords: list[str],
    location: str,
    max_jobs: int,
    resume_path: Path,
    options: RunOptions,
) -> list[ApplicationResult]:
    adapter = LinkedInBatchAdapter()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=options.headless, slow_mo=options.slow_mo_ms)
        page = browser.new_page()
        try:
            return adapter.run(
                page,
                keywords=keywords,
                location=location,
                max_jobs=max_jobs,
                resume_path=resume_path,
                options=options,
            )
        finally:
            browser.close()


