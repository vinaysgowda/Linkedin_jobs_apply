from fastapi.testclient import TestClient

from demo_site.app import app


client = TestClient(app)


def test_demo_site_get_and_submit() -> None:
    get_response = client.get("/jobs/demo-country")
    assert get_response.status_code == 200
    assert "Demo Job Application" in get_response.text

    post_response = client.post(
        "/jobs/demo-country",
        data={
            "full_name": "Demo User",
            "email": "demo@example.com",
            "phone": "1234567890",
            "country": "India",
            "city": "Chennai",
            "linkedin": "https://linkedin.com/in/demo",
            "github": "https://github.com/demo",
            "summary": "Summary",
            "skills": "Python, FastAPI",
            "cover_letter": "Hello",
            "work_authorized": "true",
        },
        files={"resume": ("resume.txt", b"demo resume", "text/plain")},
    )

    assert post_response.status_code == 200
    assert "Application received" in post_response.text

