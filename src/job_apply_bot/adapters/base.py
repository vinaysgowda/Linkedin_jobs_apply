from __future__ import annotations

from abc import ABC, abstractmethod

from playwright.sync_api import Page

from job_apply_bot.models import ApplicantProfile, ApplicationResult, JobContext, RunOptions, SiteConfig


class JobApplicationAdapter(ABC):
    @abstractmethod
    def apply(
        self,
        page: Page,
        profile: ApplicantProfile,
        job: JobContext,
        site: SiteConfig,
        options: RunOptions,
    ) -> ApplicationResult:
        raise NotImplementedError

