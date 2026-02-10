# 1st Step.
# Analysis Agent - Gather user's background info
# input - User Conversation(natural language) -> output - structured data
# e.g., education, experience, skills, job preferences

import os
import json
import re
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


def collect_info(user_input: str, stream: bool = False) -> str:
    """Takes user conversation input and returns structured JSON with resume information."""

    # Fast path for resume-like inputs to avoid empty model outputs
    if _looks_like_resume(user_input):
        parsed = _fallback_parse(user_input)
        output = json.dumps(parsed, ensure_ascii=False, indent=2)
        if stream:
            print(output)
        return output

    # Initialize client at function level (lazy loading) to handle missing env vars in CI
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-12-01-preview"
    )

    messages = [
        {
            "role": "system",
            "content": """You are an expert Resume Information Collector.
Extract user details into a STRICT JSON OBJECT and nothing else.

Rules:
- Output must be valid JSON and start with "{" and end with "}".
- Do NOT use Markdown fences or extra text.
- If a field is not present, use null or an empty array.
- Use concise, accurate strings copied or lightly normalized from the input.
- If the name is present anywhere, it MUST be captured.
- If the input clearly contains items for a section, do NOT return an empty array for that section.
- Map common headings (Education, Skills, Employment/Experience, Projects, Certifications) to the schema.

Required JSON schema (exact keys):
{
  "name": "string or null",
  "education": ["list of strings"],
  "skills": ["list of strings"],
  "experience": ["list of strings"],
  "projects": ["list of strings"],
  "certifications": ["list of strings"],
  "summary": "brief professional summary string or null"
}
"""
        },
        {
            "role": "user",
            "content": f"User Input: {user_input}"
        }
    ]

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            stream=stream,
            messages=messages,
            max_completion_tokens=2048,
            response_format={"type": "json_object"}
        )
    except Exception:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            stream=stream,
            messages=messages,
            max_completion_tokens=2048
        )

    if stream:
        full_response = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        print()
        clean_response = full_response.replace("```json", "").replace("```", "").strip()
        if "{" in clean_response and "}" in clean_response:
            clean_response = clean_response[clean_response.find("{"):clean_response.rfind("}") + 1]
        normalized, used_fallback = _normalize_or_fallback(clean_response, user_input)
        if used_fallback:
            print(normalized)
        return normalized
    else:
        raw = response.choices[0].message.content
        clean_response = raw.replace("```json", "").replace("```", "").strip()
        if "{" in clean_response and "}" in clean_response:
            clean_response = clean_response[clean_response.find("{"):clean_response.rfind("}") + 1]
        normalized, _ = _normalize_or_fallback(clean_response, user_input)
        return normalized


def _normalize_or_fallback(raw_json: str, user_input: str) -> tuple[str, bool]:
    """Normalize model output to JSON; if empty/invalid, parse from input heuristically."""
    try:
        data = json.loads(raw_json)
        if _is_effectively_empty(data):
            raise ValueError("empty")
        return json.dumps(_normalize_schema(data), ensure_ascii=False, indent=2), False
    except Exception:
        data = _fallback_parse(user_input)
        return json.dumps(data, ensure_ascii=False, indent=2), True


def _is_effectively_empty(data: dict) -> bool:
    if not isinstance(data, dict):
        return True
    name = data.get("name")
    education = data.get("education") or []
    skills = data.get("skills") or []
    experience = data.get("experience") or []
    projects = data.get("projects") or []
    certifications = data.get("certifications") or []
    summary = data.get("summary")
    return (
        not name
        and not education
        and not skills
        and not experience
        and not projects
        and not certifications
        and not summary
    )


def _normalize_schema(data: dict) -> dict:
    """Coerce fields to expected schema types."""
    def to_list(value):
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        return [str(value).strip()] if str(value).strip() else []

    return {
        "name": data.get("name"),
        "education": to_list(data.get("education")),
        "skills": to_list(data.get("skills")),
        "experience": to_list(data.get("experience")),
        "projects": to_list(data.get("projects")),
        "certifications": to_list(data.get("certifications")),
        "summary": data.get("summary"),
    }


def _fallback_parse(user_input: str) -> dict:
    """Lightweight parser for common resume section headings."""
    lines = [line.rstrip() for line in user_input.splitlines()]
    lines = [line for line in lines if line.strip()]

    name = None
    if lines:
        name = lines[0].strip()
        # If first line contains contact info, try to grab name from prior non-empty
        if "@" in name or "|" in name or "http" in name.lower():
            name = None

    sections = {}
    current = None
    section_map = {
        "education": "education",
        "skills": "skills",
        "employment": "experience",
        "experience": "experience",
        "work experience": "experience",
        "projects": "projects",
        "software projects": "projects",
        "certifications": "certifications",
        "additional information": "additional",
    }

    for line in lines:
        key = section_map.get(line.strip().lower())
        if key:
            current = key
            sections.setdefault(current, [])
            continue
        if current:
            sections.setdefault(current, []).append(line.strip())

    education = _compact_section(sections.get("education", []))
    skills = _parse_skills(sections.get("skills", []))
    experience = _group_role_blocks(sections.get("experience", []))
    projects = _group_role_blocks(sections.get("projects", []))
    certifications = _extract_certifications(sections.get("education", []) + sections.get("certifications", []))

    return {
        "name": name,
        "education": education,
        "skills": skills,
        "experience": experience,
        "projects": projects,
        "certifications": certifications,
        "summary": None,
    }


def _looks_like_resume(user_input: str) -> bool:
    text = user_input.lower()
    hits = 0
    for key in ["education", "skills", "employment", "experience", "projects"]:
        if key in text:
            hits += 1
    return hits >= 2


def _compact_section(lines: list[str]) -> list[str]:
    items = []
    buffer = []
    for line in lines:
        if _is_heading_like(line):
            if buffer:
                items.append(" ".join(buffer).strip())
                buffer = []
            buffer.append(line)
        elif line.startswith(("-", "•")):
            buffer.append(line.lstrip("-• ").strip())
        else:
            buffer.append(line)
    if buffer:
        items.append(" ".join(buffer).strip())
    return [i for i in items if i]


def _parse_skills(lines: list[str]) -> list[str]:
    skills = []
    for line in lines:
        clean = line.lstrip("-• ").strip()
        if not clean:
            continue
        if ":" in clean:
            _, rhs = clean.split(":", 1)
            parts = [p.strip() for p in re.split(r"[|,]", rhs) if p.strip()]
            skills.extend(parts)
        else:
            parts = [p.strip() for p in re.split(r"[|,]", clean) if p.strip()]
            skills.extend(parts)
    return skills


def _group_role_blocks(lines: list[str]) -> list[str]:
    blocks = []
    current = []
    for line in lines:
        if _is_heading_like(line):
            if current:
                blocks.append(_join_block(current))
            current = [line]
        elif line.startswith(("-", "•")):
            current.append(line.lstrip("-• ").strip())
        else:
            current.append(line)
    if current:
        blocks.append(_join_block(current))
    return [b for b in blocks if b]


def _join_block(block_lines: list[str]) -> str:
    if not block_lines:
        return ""
    head = block_lines[0].strip()
    bullets = [b.strip() for b in block_lines[1:] if b.strip()]
    if bullets:
        return f"{head} — " + "; ".join(bullets)
    return head


def _extract_certifications(lines: list[str]) -> list[str]:
    certs = []
    for line in lines:
        if "cert" in line.lower() or "award" in line.lower() or "scholarship" in line.lower():
            certs.append(line.lstrip("-• ").strip())
    return [c for c in certs if c]


def _is_heading_like(line: str) -> bool:
    # Heuristic: contains a date range or role/company separator
    return bool(
        re.search(r"\b(20\d{2}|19\d{2})\b", line)
        or " | " in line
        or re.search(r"\bto\b", line, re.IGNORECASE)
        or re.search(r"\b–\b", line)
    )
