from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from job_apply_bot.adapters.base import JobApplicationAdapter
from job_apply_bot.models import ApplicantProfile, ApplicationResult, JobContext, RunOptions, SiteConfig


class GenericPlaywrightAdapter(JobApplicationAdapter):
    """Config-driven adapter for generic job application forms."""

    def apply(
        self,
        page: Page,
        profile: ApplicantProfile,
        job: JobContext,
        site: SiteConfig,
        options: RunOptions,
    ) -> ApplicationResult:
        target_url = site.start_url or job.apply_url
        page.goto(target_url, wait_until="domcontentloaded", timeout=options.timeout_ms)

        filled_fields: list[str] = []

        for field_name, selector in site.field_selectors.items():
            value = self.resolve_value(field_name, profile, job)
            if value in (None, ""):
                continue
            page.locator(selector).fill(self.stringify(value), timeout=options.timeout_ms)
            filled_fields.append(field_name)

        for field_name, selector in site.select_selectors.items():
            value = self.resolve_value(field_name, profile, job)
            if value in (None, ""):
                continue
            self._select_value(page, selector, self.stringify(value), options.timeout_ms)
            filled_fields.append(field_name)

        for field_name, selector in site.checkbox_selectors.items():
            if self.truthy(self.resolve_value(field_name, profile, job)):
                page.locator(selector).check(timeout=options.timeout_ms)
                filled_fields.append(field_name)

        for field_name, selector in site.upload_selectors.items():
            value = self.resolve_value(field_name, profile, job)
            if not value:
                continue
            file_path = Path(str(value)).expanduser().resolve()
            if not file_path.exists():
                raise FileNotFoundError(f"Upload file does not exist: {file_path}")
            page.locator(selector).set_input_files(str(file_path), timeout=options.timeout_ms)
            filled_fields.append(field_name)

        if not options.auto_submit:
            return ApplicationResult(
                success=True,
                submitted=False,
                message="Preview completed. Fields were filled but the form was not submitted.",
                visited_url=page.url,
                filled_fields=filled_fields,
            )

        if site.pre_submit_delay_ms:
            page.wait_for_timeout(site.pre_submit_delay_ms)

        if not site.submit_selector:
            raise ValueError("auto_submit was requested, but submit_selector is missing in site config")

        page.locator(site.submit_selector).click(timeout=options.timeout_ms)

        if site.success_selector:
            page.locator(site.success_selector).wait_for(timeout=options.timeout_ms)
        elif site.success_text:
            page.get_by_text(site.success_text, exact=False).wait_for(timeout=options.timeout_ms)

        return ApplicationResult(
            success=True,
            submitted=True,
            message="Application submitted successfully.",
            visited_url=page.url,
            filled_fields=filled_fields,
        )

    @staticmethod
    def stringify(value: Any) -> str:
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        return str(value)

    @staticmethod
    def truthy(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return bool(value)

    @classmethod
    def resolve_value(cls, field_name: str, profile: ApplicantProfile, job: JobContext) -> Any:
        profile_data = profile.model_dump()
        job_data = job.model_dump()

        for source in (profile_data, job_data):
            if field_name in source:
                return source[field_name]

        for root in (profile_data, job_data):
            value = cls._resolve_dotted(root, field_name)
            if value is not None:
                return value

        if field_name == "skills_csv":
            return ", ".join(profile.skills)
        if field_name == "signup_email":
            return profile.email

        return None

    @staticmethod
    def _resolve_dotted(container: dict[str, Any], dotted_key: str) -> Any:
        current: Any = container
        for segment in dotted_key.split("."):
            if not isinstance(current, dict) or segment not in current:
                return None
            current = current[segment]
        return current

    @staticmethod
    def _select_value(page: Page, selector: str, value: str, timeout_ms: int) -> None:
        locator = page.locator(selector)
        strategies = (
            {"label": value},
            {"value": value},
            {"index": 0} if value == "__FIRST_OPTION__" else None,
        )
        for strategy in strategies:
            if strategy is None:
                continue
            try:
                locator.select_option(**strategy, timeout=timeout_ms)
                return
            except PlaywrightError:
                continue
        raise ValueError(f"Could not select value '{value}' for selector '{selector}'")


