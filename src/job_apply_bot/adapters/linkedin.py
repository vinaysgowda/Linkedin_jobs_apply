from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlencode

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page
import typer

from job_apply_bot.models import ApplicationResult, RunOptions


def parse_keywords(raw_keywords: str) -> list[str]:
    return [item.strip() for item in raw_keywords.split(",") if item.strip()]


def build_linkedin_jobs_url(keywords: list[str], location: str) -> str:
    query = {
        "keywords": " ".join(keywords).strip(),
        "location": location.strip(),
        "f_AL": "true",  # Easy Apply only
    }
    return f"https://www.linkedin.com/jobs/search/?{urlencode(query)}"


class LinkedInBatchAdapter:
    def run(
        self,
        page: Page,
        keywords: list[str],
        location: str,
        max_jobs: int,
        resume_path: Path,
        options: RunOptions,
    ) -> list[ApplicationResult]:
        page.goto("https://www.linkedin.com/jobs/", wait_until="domcontentloaded", timeout=options.timeout_ms)
        print("Please login to LinkedIn in the opened browser, then press Enter here to continue...")
        input()

        page.goto(build_linkedin_jobs_url(keywords, location), wait_until="domcontentloaded", timeout=options.timeout_ms)
        page.wait_for_timeout(2500)

        results: list[ApplicationResult] = []
        cards = page.locator("li.scaffold-layout__list-item")
        card_count = min(cards.count(), max_jobs)

        for index in range(card_count):
            try:
                result = self._process_card(page, cards.nth(index), resume_path, options)
            except PlaywrightError as exc:
                result = ApplicationResult(
                    success=False,
                    submitted=False,
                    message=f"Failed to process job card: {exc}",
                    visited_url=page.url,
                    filled_fields=[],
                )
            results.append(result)

        return results

    def _process_card(self, page: Page, card, resume_path: Path, options: RunOptions) -> ApplicationResult:
        card.click(timeout=options.timeout_ms)
        page.wait_for_timeout(1200)

        title = page.locator("h1, h2").first.text_content(timeout=options.timeout_ms) or "Unknown role"
        company = page.locator(".job-details-jobs-unified-top-card__company-name").first.text_content() or "Unknown"
        description = f"{title.strip()} at {company.strip()}"

        easy_apply_button = page.get_by_role("button", name=re.compile("Easy Apply", re.IGNORECASE)).first
        if easy_apply_button.count() == 0:
            easy_apply_button = page.locator("button:has-text('Easy Apply')")
        if easy_apply_button.count() == 0:
            return ApplicationResult(
                success=True,
                submitted=False,
                message=f"Skipped (not Easy Apply): {description}",
                visited_url=page.url,
                filled_fields=[],
            )

        if not options.auto_submit:
            return ApplicationResult(
                success=True,
                submitted=False,
                message=f"Matched Easy Apply job: {description}",
                visited_url=page.url,
                filled_fields=[],
            )

        easy_apply_button.click(timeout=options.timeout_ms)
        submitted, resume_uploaded = self._complete_easy_apply_modal(page, options, resume_path)

        return ApplicationResult(
            success=True,
            submitted=submitted,
            message=(
                f"Submitted application: {description}" if submitted else f"Opened Easy Apply but could not auto-submit: {description}"
            ),
            visited_url=page.url,
            filled_fields=["resume_path"] if resume_uploaded else [],
        )

    def _complete_easy_apply_modal(self, page: Page, options: RunOptions, resume_path: Path) -> tuple[bool, bool]:
        resume_uploaded = False
        for attempt in range(20):
            if not resume_uploaded:
                resume_uploaded = self._upload_resume_if_possible(page, resume_path, options)

            self._dismiss_update_profile_prompts(page, options)

            page.wait_for_timeout(400)

            input_fields = page.locator("textarea, input[type='text']:not([type='hidden']), select")
            if input_fields.count() > 0:
                typer.prompt("⏸  LinkedIn is asking a question. Fill it manually in the browser, then press Enter to continue")
                page.wait_for_timeout(300)
                continue

            submit = page.get_by_role("button", name=re.compile("Submit application", re.IGNORECASE))
            if submit.count() > 0:
                submit.first.click(timeout=options.timeout_ms)
                page.wait_for_timeout(800)
                self._close_modal_if_open(page, options)
                return True, resume_uploaded

            submit_alt = page.locator("button:has-text('Submit application')")
            if submit_alt.count() > 0:
                submit_alt.first.click(timeout=options.timeout_ms)
                page.wait_for_timeout(800)
                self._close_modal_if_open(page, options)
                return True, resume_uploaded

            review = page.get_by_role("button", name=re.compile("Review", re.IGNORECASE))
            if review.count() > 0:
                review.first.click(timeout=options.timeout_ms)
                page.wait_for_timeout(500)
                continue

            next_button = page.get_by_role("button", name=re.compile(r"^Next$", re.IGNORECASE))
            if next_button.count() > 0:
                next_button.first.click(timeout=options.timeout_ms)
                page.wait_for_timeout(500)
                continue

            next_alt = page.locator("button:has-text('Next')")
            if next_alt.count() > 0:
                next_alt.first.click(timeout=options.timeout_ms)
                page.wait_for_timeout(500)
                continue

            continue_btn = page.get_by_role("button", name=re.compile("Continue", re.IGNORECASE))
            if continue_btn.count() > 0:
                continue_btn.first.click(timeout=options.timeout_ms)
                page.wait_for_timeout(500)
                continue

            break

        self._close_modal_if_open(page, options)
        return False, resume_uploaded

    @staticmethod
    def _dismiss_update_profile_prompts(page: Page, options: RunOptions) -> None:
        not_now = page.get_by_role("button", name=re.compile("Not now|Skip|Dismiss", re.IGNORECASE))
        if not_now.count() > 0:
            not_now.first.click(timeout=options.timeout_ms)
            page.wait_for_timeout(300)

        not_now_alt = page.locator("button:has-text('Not now'), button:has-text('Skip')")
        if not_now_alt.count() > 0:
            not_now_alt.first.click(timeout=options.timeout_ms)
            page.wait_for_timeout(300)

    @staticmethod
    def _upload_resume_if_possible(page: Page, resume_path: Path, options: RunOptions) -> bool:
        file_inputs = page.locator("input[type='file']")
        if file_inputs.count() == 0:
            file_inputs = page.locator("input[type='file'][accept*='pdf'], input[type='file'][accept*='doc']")
        if file_inputs.count() == 0:
            return False
        try:
            file_inputs.first.set_input_files(str(resume_path), timeout=options.timeout_ms)
            page.wait_for_timeout(300)
            return True
        except (PlaywrightError, Exception):
            return False

    @staticmethod
    def _close_modal_if_open(page: Page, options: RunOptions) -> None:
        dismiss = page.get_by_role("button", name=re.compile("Dismiss|Close", re.IGNORECASE))
        if dismiss.count() > 0:
            dismiss.first.click(timeout=options.timeout_ms)
            discard = page.get_by_role("button", name=re.compile("Discard|Exit", re.IGNORECASE))
            if discard.count() > 0:
                discard.first.click(timeout=options.timeout_ms)

