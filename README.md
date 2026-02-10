# Resume Agent

Simple resume assistant that routes user requests through four steps:
collect user info, analyze job description, write a tailored resume, and provide feedback.

## Setup
1. Create and activate a virtual environment.
2. Install dependencies.
3. Configure environment variables.

## Quick Start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

Create a `.env` file using `.env.sample` and fill in the values.

Run the demo:
```bash
python3 run_demo.py
```

## Demo Inputs and Results
- `run_demo.py` currently includes a sample resume and job description.
- For testing, replace `sample_user_input` with your own resume text and update `sample_job_description` with the target job details.
- The generated LaTeX resume is saved to `resume_result/resume.tex`.
- Console output shows each agent’s output (summarized for readability).

## Configuration
- Environment variables are read from `.env`.
- `config.json` lists the expected configuration fields for reference.
