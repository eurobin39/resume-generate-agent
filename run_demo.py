import json
import os
from pathlib import Path

from resume_assistant.agents import collect_info, analyze_job, write_resume, review_resume


def print_section_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_demo():
    sample_user_input = """
    EURO BAE
    Dublin, Ireland | +353 0834496428 | eurobin39@gmail.com

    Education
    Trinity College Dublin (September 2021 – May 2027)
    - Honors bachelor’s in integrated computer science
    - Global Excellence Undergraduate Scholarship | Trinity International Foundation Scholarship
    - Software Engineering Project Industry Award (Sustainability Award) | Huawei Tech Arena 2025 LLM Hackathon (3rd Prize)
    - Relevant modules: Software Engineering Project, Computer Architecture and Information Management, Algorithms and Data Structures,
      Concurrent Systems, Statistical Analysis
    - Joined DUCSS hackathons and coding competitions to strengthen collaborative problem-solving skills

    Skills
    - Languages & Programming: Java, Python, C, JavaScript, TypeScript, ARM, VHDL
    - Web & Front-End Development: React, React Native, Tailwind, Next.js, HTML, CSS
    - Back-End & DevOps: Node.js, Docker, Git, Linux, REST API
    - Database & Cloud: PostgreSQL, MySQL, MongoDB, GraphQL, Oracle, AWS
    - Tools & Monitoring: Grafana, Supabase, Cloudflare, OWASP ZAP, Zest, R, Expo Go
    - Languages: Fluent in English and Korean

    Employment
    Undergraduate Demonstrator | Trinity College Dublin | Dublin (09/2025 – Present)
    - Supported students in using Microsoft Expression Web 4, Python, and Excel for their coursework

    Full Stack Engineer Intern (Industry-Academic Partnership) | Workday | Dublin (01/2025 – 04/2025)
    - Developed and maintained both frontend (React) and backend (Node.js) components, contributing to over 80% of the codebase
    - Established a CI/CD pipeline by configuring GitLab Runner on a Raspberry Pi, utilizing SSH tunneling for secure remote management
    - Migrated database and server to Raspberry Pi, cutting energy use by ~93% and supporting green computing

    Software Engineer Trainee | Samsung SDS | Suwon (02/2024 – 07/2024)
    - Automated sample workflows using RPA tools during Samsung Bootcamp, improving task efficiency in demo environments
    - Prototyped a smart factory system by combining RPA, ML, and IoT during Samsung RPA Bootcamp

    Military Police Sergeant | Ministry of National Defense | Suwon (08/2022 – 02/2024)
    - Conducted thorough investigations of potential breaches of military law and policy
    - Utilized intelligence-gathering technology and implemented command structures to enhance operational efficiency

    Data Analyst Intern | Media & Data Institute | Seoul (05/2021 – 09/2021)
    - Refactored the data access layer by migrating from SQL to GraphQL, improving data flexibility and frontend integration
    - Gained hands-on experience in data governance and privacy, collaborating on policies aligned with ethical data collection practices

    Software Projects
    A.T.M. (Automated Trading Manager)
    - Built a Python-based trading bot integrating Binance API, executing automated trades based on technical signals and market conditions
    - Implemented stop-loss and entry logic, improving simulated returns in test runs
    - Analyzed transaction fees and macro indicators to optimize trade execution strategy

    AURA (AI-based Work Efficiency Enhancer)
    - Led a team of 5 to build an AI-powered productivity tracker platform combining webcam, mouse/keyboard data, and language models
    - Integrated Azure Face API and OpenAI to assess concentration levels and generate productivity insights
    - Conducted code reviews and finalized deployment, ensuring a cohesive UX across all integrated modules

    OLY (Community-Driven Expat Platform)
    - Led a 7-member development team, coordinating task allocation, version control, and technical decision-making, while deploying the app to
      TestFlight and Google Play internal testing
    - Developed a full-stack community platform app (“OLY”) using React Native, Expo, and Supabase, implementing marketplace, rental,
      currency exchange, chat, and authentication features

    Additional Information
    Team Leader, Suwon City Participation Committee
    - Led event planning and logistics for local community programs, provided English interpretation for foreign participants

    Volunteer, Korean Association of Ireland
    - Prepared and distributed meals to homeless individuals in Dublin, supporting community outreach
    """

    sample_job_description = """
    Senior Backend Engineer - FinTech Startup

    We're looking for a Senior Backend Engineer to join our core platform team. You'll design
    and build scalable APIs and services that power our next-generation payments infrastructure.

    Requirements:
    - 3+ years of backend development experience
    - Strong proficiency in Python or Go
    - Experience with microservices architecture and distributed systems
    - Familiarity with cloud platforms (AWS preferred)
    - Experience with relational databases (PostgreSQL) and caching (Redis)
    - Understanding of CI/CD pipelines and containerization (Docker, Kubernetes)

    Nice to have:
    - Experience in fintech or payments
    - AWS certification
    - Experience leading technical projects or mentoring junior engineers
    - Familiarity with event-driven architectures (Kafka, RabbitMQ)
    """

    print_section_header("RESUME ASSISTANT DEMO")
    print("This demo runs each agent once with the same inputs.\n")

    print_section_header("AGENT 1: INFO COLLECTOR")
    user_profile_raw = collect_info(sample_user_input, stream=False)
    user_profile = _clean_profile(user_profile_raw)
    print(user_profile)

    print_section_header("AGENT 2: JOB ANALYZER")
    job_analysis = analyze_job(sample_job_description, stream=False)
    print(_summarize_job_analysis(job_analysis))

    print_section_header("AGENT 3: RESUME WRITER")
    resume = write_resume(user_profile, job_analysis, stream=False)
    print(resume)
    _save_resume_artifact(resume)

    print_section_header("AGENT 4: RESUME FEEDBACK")
    feedback = review_resume(resume, job_analysis, stream=False)
    print(_summarize_feedback(feedback))

    print_section_header("DEMO COMPLETE")
    print("Done.\n")


def _clean_profile(profile_json: str) -> str:
    try:
        data = json.loads(profile_json)
    except json.JSONDecodeError:
        return profile_json

    for key in ["education", "experience", "projects"]:
        data[key] = _merge_bullets(data.get(key, []))

    data["skills"] = _merge_skills(data.get("skills", []))

    return json.dumps(data, ensure_ascii=False, indent=2)


def _merge_bullets(items: list) -> list:
    cleaned = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if text.startswith("-"):
            text = text.lstrip("-").strip()
            if cleaned:
                cleaned[-1] = f"{cleaned[-1]}\n  - {text}"
            else:
                cleaned.append(text)
        else:
            cleaned.append(text)
    return cleaned


def _merge_skills(items: list) -> list:
    cleaned = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if text.startswith("-"):
            text = text.lstrip("-").strip()
        cleaned.append(text)
    return cleaned


def _summarize_job_analysis(job_analysis: str) -> str:
    try:
        data = json.loads(job_analysis)
    except json.JSONDecodeError:
        return job_analysis
    role = data.get("role") or "Unknown"
    skills = data.get("required_skills") or []
    top_skills = ", ".join(skills[:5])
    return f"role: {role}\nrequired_skills: {top_skills}"


def _summarize_feedback(feedback: str) -> str:
    lines = [line.strip() for line in feedback.splitlines() if line.strip()]
    score_line = next((l for l in lines if "score" in l.lower()), "Overall Score: N/A")
    bullets = [l.lstrip("-• ").strip() for l in lines if l.startswith(("-", "•"))]
    top_bullets = bullets[:3]
    out = [score_line]
    if top_bullets:
        out.extend([f"- {b}" for b in top_bullets])
    return "\n".join(out)


def _save_resume_artifact(resume_tex: str) -> None:
    out_dir = Path(__file__).resolve().parent / "resume_result"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "resume.tex"
    out_path.write_text(resume_tex, encoding="utf-8")


if __name__ == "__main__":
    run_demo()
