from job_apply_bot.adapters.linkedin import build_linkedin_jobs_url, parse_keywords


def test_parse_keywords_trims_and_drops_empty() -> None:
    assert parse_keywords(" python, backend , ,automation ") == ["python", "backend", "automation"]


def test_build_linkedin_jobs_url_contains_filters() -> None:
    url = build_linkedin_jobs_url(["python", "backend"], "Bengaluru, India")
    assert "linkedin.com/jobs/search" in url
    assert "f_AL=true" in url
    assert "keywords=python+backend" in url
    assert "location=Bengaluru%2C+India" in url

