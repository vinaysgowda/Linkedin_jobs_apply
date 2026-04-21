# Job Apply Bot

A small Python framework that auto-fills job application forms from a structured applicant profile and can optionally submit them.

This project is **config-driven**:
- your applicant data lives in a YAML or JSON file
- each target site is described by selectors in a YAML or JSON file
- each job can be described separately, including a country filter

A local FastAPI demo site is included so you can test the end-to-end flow without depending on any external job board.

## What this project does

- loads a structured applicant profile plus a resume file path
- loads job metadata such as title, company, URL, and country
- opens a browser with Playwright
- fills fields using CSS selectors from a site config
- optionally uploads the resume
- optionally submits the form
- supports an interactive terminal wizard that asks for name, email, phone, country, and resume path
- supports batch apply from a jobs list file

## Project structure

- `src/job_apply_bot/` - framework code
- `demo_site/` - local demo job application form
- `sample_data/` - sample applicant, resume, job, and site config
- `tests/` - unit and demo-site tests

## Install

```bash
cd /Users/PycharmProjects/Linkedin_jobs_apply
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m playwright install chromium
```

## Run the local demo site

```bash
cd /Users/PycharmProjects/Linkedin_jobs_apply
source .venv/bin/activate
uvicorn demo_site.app:app --reload
```

Open `http://127.0.0.1:8000/jobs/demo-country` if you want to inspect the form manually.

## Preview-fill the form without submitting

```bash
cd /Users/PycharmProjects/Linkedin_jobs_apply
source .venv/bin/activate
job-apply-bot preview \
  --profile sample_data/applicant_profile.yaml \
  --job sample_data/demo_job.yaml \
  --site sample_data/demo_site.yaml \
  --country India
```

## Fill and submit automatically

```bash
cd /Users/PycharmProjects/Linkedin_jobs_apply
source .venv/bin/activate
job-apply-bot submit \
  --profile sample_data/applicant_profile.yaml \
  --job sample_data/demo_job.yaml \
  --site sample_data/demo_site.yaml \
  --country India \
  --yes
```

## Interactive terminal wizard (asks for candidate details)

```bash
cd /Users/PycharmProjects/Linkedin_jobs_apply
source .venv/bin/activate
job-apply-bot wizard-apply \
  --site sample_data/demo_site.yaml \
  --jobs sample_data/demo_jobs.yaml
```

When this command runs, it prompts for:
- name
- email
- phone
- country
- resume path
- optional profile and signup fields

## LinkedIn batch by keywords and location

```bash
cd /Users/PycharmProjects/Linkedin_jobs_apply
source .venv/bin/activate
job-apply-bot linkedin-batch \
  --keywords "python,automation,backend" \
  --location "Bengaluru, India" \
  --max-jobs 20 \
  --resume-path /absolute/path/to/resume.pdf
```

This flow opens LinkedIn Jobs, waits for manual login in the browser, then processes matching Easy Apply jobs.
If `--resume-path` is not provided, the command prompts for it in terminal.
Use `--dry-run` to only list matching jobs without submitting.

**During Easy Apply, you may see:**
- ⏸ Terminal prompt asking you to fill LinkedIn questions manually in the browser, then press Enter
- LinkedIn "Update profile" suggestions — the bot automatically clicks "Not now" to skip these
- Multiple-choice, text, or file upload fields — fill them in the browser while the bot waits

## Using your own resume and country

1. Replace `sample_data/resume.txt` with your actual resume file, for example a PDF.
2. Update `resume_path` inside `sample_data/applicant_profile.yaml`.
3. Update your personal fields in `sample_data/applicant_profile.yaml`.
4. Set the target country in the job file or pass `--country` on the command line.
5. For each real website, create a new site selector config similar to `sample_data/demo_site.yaml`.

## Notes on real job sites

Real sites often differ in:
- field names and selectors
- multi-step forms
- login requirements
- anti-bot checks and terms of use

Because of that, this framework gives you a reusable base and a local demo. For real portals, create one config per site and extend the adapter if a site requires custom logic.

For security and compliance, this project does **not** store or auto-type LinkedIn credentials. Use manual sign-in when prompted.

## Run tests

```bash
cd /Users/PycharmProjects/Linkedin_jobs_apply
source .venv/bin/activate
pytest
```


