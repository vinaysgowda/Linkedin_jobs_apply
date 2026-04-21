from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI(title="Demo Job Site")
SUBMISSIONS_FILE = Path(__file__).resolve().parent / "submissions.jsonl"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs/demo-country", response_class=HTMLResponse)
def job_form() -> str:
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>Demo Job Application</title>
      <style>
        body { font-family: Arial, sans-serif; max-width: 820px; margin: 2rem auto; }
        form { display: grid; gap: 0.75rem; }
        label { display: grid; gap: 0.25rem; }
      </style>
    </head>
    <body>
      <h1>Apply: Python Automation Engineer</h1>
      <form action="/jobs/demo-country" method="post" enctype="multipart/form-data">
        <label>Full name <input id="full_name" name="full_name" /></label>
        <label>Email <input id="email" name="email" type="email" /></label>
        <label>Phone <input id="phone" name="phone" /></label>
        <label>Country
          <select id="country" name="country">
            <option value="India">India</option>
            <option value="United States">United States</option>
            <option value="Germany">Germany</option>
          </select>
        </label>
        <label>City <input id="city" name="city" /></label>
        <label>LinkedIn <input id="linkedin" name="linkedin" /></label>
        <label>GitHub <input id="github" name="github" /></label>
        <label>Summary <textarea id="summary" name="summary"></textarea></label>
        <label>Skills <textarea id="skills" name="skills"></textarea></label>
        <label>Cover letter <textarea id="cover_letter" name="cover_letter"></textarea></label>
        <label>Work authorized <input id="work_authorized" name="work_authorized" type="checkbox" value="true" /></label>
        <label>Resume <input id="resume" name="resume" type="file" /></label>
        <button id="submit_application" type="submit">Submit application</button>
      </form>
    </body>
    </html>
    """


@app.post("/jobs/demo-country", response_class=HTMLResponse)
async def submit_job_form(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    country: str = Form(...),
    city: str = Form(""),
    linkedin: str = Form(""),
    github: str = Form(""),
    summary: str = Form(""),
    skills: str = Form(""),
    cover_letter: str = Form(""),
    work_authorized: str | None = Form(None),
    resume: Optional[UploadFile] = File(None),
) -> str:
    payload = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "country": country,
        "city": city,
        "linkedin": linkedin,
        "github": github,
        "summary": summary,
        "skills": skills,
        "cover_letter": cover_letter,
        "work_authorized": bool(work_authorized),
        "resume_filename": resume.filename if resume else None,
    }
    with SUBMISSIONS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")

    return f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head><meta charset=\"UTF-8\" /><title>Application received</title></head>
    <body>
      <h1 id=\"success_message\">Application received</h1>
      <p>Thanks, {full_name}. Your application for {country} has been saved.</p>
    </body>
    </html>
    """


