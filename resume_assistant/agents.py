"""Resume assistant agents and synchronous execution helpers."""

from __future__ import annotations

from agent_framework_utils import create_agent, run_agent_sync

_agent_collector = None
_agent_analyzer = None
_agent_writer = None
_agent_reviewer = None


def _get_collector():
    """Create or return the cached resume info collector agent."""
    global _agent_collector
    if _agent_collector is None:
        _agent_collector = create_agent(
            name="resume_info_collector",
            instructions=(
                "You are an expert Resume Information Collector.\n"
                "Extract user details into a STRICT JSON OBJECT and nothing else.\n\n"
                "Rules:\n"
                "- Output must be valid JSON and start with \"{\" and end with \"}\".\n"
                "- Do NOT use Markdown fences or extra text.\n"
                "- If a field is not present, use null or an empty array.\n"
                "- Use concise, accurate strings copied or lightly normalized from the input.\n"
                "- If the name is present anywhere, it MUST be captured.\n"
                "- If the input clearly contains items for a section, do NOT return an empty array for that section.\n"
                "- Map common headings (Education, Skills, Employment/Experience, Projects, Certifications) to the schema.\n\n"
                "Required JSON schema (exact keys):\n"
                "{\n"
                "  \"name\": \"string or null\",\n"
                "  \"education\": [\"list of strings\"],\n"
                "  \"skills\": [\"list of strings\"],\n"
                "  \"experience\": [\"list of strings\"],\n"
                "  \"projects\": [\"list of strings\"],\n"
                "  \"certifications\": [\"list of strings\"],\n"
                "  \"summary\": \"brief professional summary string or null\"\n"
                "}"
            ),
        )
    return _agent_collector


def _get_analyzer():
    """Create or return the cached job analyzer agent."""
    global _agent_analyzer
    if _agent_analyzer is None:
        _agent_analyzer = create_agent(
            name="resume_job_analyzer",
            instructions=(
                "You are an expert Job Analyst.\n"
                "Analyze the JD and output a STRICT JSON summary.\n\n"
                "Output Format (JSON only):\n"
                "{\n"
                "    \"role\": \"Job Title\",\n"
                "    \"required_skills\": [\"list of hard skills\"],\n"
                "    \"preferred_skills\": [\"list of nice-to-have skills\"],\n"
                "    \"keywords\": [\"ATS keywords\"],\n"
                "    \"experience_level\": \"Junior/Mid/Senior\",\n"
                "    \"domain\": \"Industry/Sector\"\n"
                "}\n\n"
                "Do not include markdown formatting. Just return the raw JSON string."
            ),
        )
    return _agent_analyzer


def _get_writer():
    """Create or return the cached resume writer agent."""
    global _agent_writer
    if _agent_writer is None:
        _agent_writer = create_agent(
            name="resume_writer",
            instructions=(
                "You are an expert Resume Writer.\n"
                "Write a professional resume in LaTeX format (plain LaTeX, no Markdown).\n\n"
                "Instructions:\n"
                "- Use the 'User Profile' data provided.\n"
                "- Tailor the content to match the 'Job Analysis' keywords.\n"
                "- Use professional, action-oriented language.\n"
                "- Use a clean one-page LaTeX resume layout with sections.\n"
                "- Do NOT include placeholders like '[Your Name]' if the name is missing; just use generic headers.\n"
                "- Output ONLY LaTeX. Do not wrap in code fences."
            ),
        )
    return _agent_writer


def _get_reviewer():
    """Create or return the cached resume reviewer agent."""
    global _agent_reviewer
    if _agent_reviewer is None:
        _agent_reviewer = create_agent(
            name="resume_reviewer",
            instructions=(
                "You are an expert Resume Reviewer and Career Coach.\n"
                "Analyze the provided resume against the job requirements and give actionable feedback.\n\n"
                "Output Format:\n"
                "## Overall Score\n"
                "[X/10 rating with brief justification]\n\n"
                "## Strengths\n"
                "[What the resume does well relative to the job requirements]\n\n"
                "## Areas for Improvement\n"
                "[Specific, actionable suggestions to better align with the role]\n\n"
                "## Keyword Gaps\n"
                "[Important keywords or skills from the job requirements that are missing or underrepresented]\n\n"
                "## Rewrite Suggestions\n"
                "[Concrete rewording suggestions for weak bullet points or sections]\n\n"
                "Be specific, constructive, and prioritize changes that would have the most impact on ATS scoring and recruiter appeal."
            ),
        )
    return _agent_reviewer


def get_collector_agent():
    """Public accessor for the collector agent instance."""
    return _get_collector()


def get_analyzer_agent():
    """Public accessor for the analyzer agent instance."""
    return _get_analyzer()


def get_writer_agent():
    """Public accessor for the writer agent instance."""
    return _get_writer()


def get_reviewer_agent():
    """Public accessor for the reviewer agent instance."""
    return _get_reviewer()


def collect_info(user_input: str, stream: bool = False) -> str:
    """Extract structured user profile fields from raw resume text."""
    response = run_agent_sync(_get_collector(), f"User Input: {user_input}")
    clean_response = response.replace("```json", "").replace("```", "").strip()
    if "{" in clean_response and "}" in clean_response:
        clean_response = clean_response[clean_response.find("{") : clean_response.rfind("}") + 1]
    if stream:
        print(clean_response)
    return clean_response


def analyze_job(job_description: str, stream: bool = False) -> str:
    """Analyze a job description and return structured JSON text."""
    response = run_agent_sync(_get_analyzer(), f"Job Description: {job_description}")
    clean_response = response.replace("```json", "").replace("```", "").strip()
    if stream:
        print(clean_response)
    return clean_response


def write_resume(user_profile: str, job_analysis: str, stream: bool = False) -> str:
    """Generate a LaTeX resume tailored to analyzed requirements."""
    response = run_agent_sync(
        _get_writer(),
        f"User Profile: {user_profile}\n\nJob Analysis Requirements: {job_analysis}",
    )
    clean = response.replace("```latex", "").replace("```", "").strip()
    if stream:
        print(clean)
    return clean


def review_resume(resume_content: str, job_analysis: str, stream: bool = False) -> str:
    """Review generated resume text against job requirements."""
    response = run_agent_sync(
        _get_reviewer(),
        f"Resume Content:\n{resume_content}\n\nJob Requirements:\n{job_analysis}",
    )
    if stream:
        print(response)
    return response
