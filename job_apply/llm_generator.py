"""
llm_generator.py - Dynamic Cold Email Generation using Free AI (g4f)
"""

import threading
from typing import Tuple, Optional
import time

try:
    import os
    os.environ["G4F_VERSION_CHECK"] = "False"
    os.environ["G4F_UPDATE_CHECK"] = "False"
    from g4f.client import Client
except ImportError:
    Client = None

from config import CANDIDATE

def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("utf-8"))

def log(msg: str, level: str = "INFO") -> None:
    from datetime import datetime
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "[INFO]", "WARN": "[WARN]", "ERROR": "[ERROR]"}
    _safe_print(f"{prefix.get(level, '[MSG]')} [{ts}] {msg}")

def generate_cold_email(job_title: str, company_name: str, timeout: int = 20) -> Tuple[Optional[str], Optional[str]]:
    """
    Generates a personalized cold email using a free LLM proxy (g4f).
    Returns (subject, body). Returns (None, None) if it fails or times out.
    """
    if not Client:
        log("g4f library not installed. Falling back to static templates.", "WARN")
        return None, None

    result_box = {"subject": None, "body": None}

    def _run_generation():
        try:
            from g4f.client import Client
            from g4f.Provider import PollinationsAI
            client = Client()

            # Select relevant project based on job title
            job_lower = job_title.lower()
            if "ml" in job_lower or "machine" in job_lower:
                project = CANDIDATE["projects"][0]
            elif "nlp" in job_lower or "llm" in job_lower or "chatbot" in job_lower:
                project = CANDIDATE["projects"][1]
            elif "automation" in job_lower:
                project = CANDIDATE["projects"][2]
            else:
                project = CANDIDATE["projects"][0]

            skills_str = ", ".join(CANDIDATE["skills"][:8])

            system_msg = (
                "You are an expert career consultant writing a professional cold email for a client. "
                "Output exactly two parts: Line 1 must be 'Subject: [Your Subject]'. "
                "The rest must be the email body. Do NOT use placeholder brackets like [Hiring Manager], "
                "instead use general greetings like 'Dear Hiring Team'. "
                "Be warm but direct, mention the resume is attached, and logically weave in the candidate's specific details provided. Keep the email concise."
            )

            user_msg = (
                f"Write a cold email applying for the role of '{job_title}' at '{company_name}'.\n"
                f"Candidate Name: {CANDIDATE['name']}\n"
                f"Contact info ending block: {CANDIDATE['email']} | {CANDIDATE['phone']}\n"
                f"Degree: {CANDIDATE['degree']} (CGPA: {CANDIDATE['cgpa']})\n"
                f"Experience: {CANDIDATE['experience']}\n"
                f"Key Skills: {skills_str}\n"
                f"Relevant Project: {project}\n"
            )

            response = client.chat.completions.create(
                model="openai",
                provider=PollinationsAI,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
            )

            content = response.choices[0].message.content.strip()

            # Parse the content safely
            lines = content.split('\n')
            subject = None
            body_lines = []

            is_subject_line = True
            for line in lines:
                if is_subject_line and line.lower().startswith('subject:'):
                    subject = line[8:].strip()
                    is_subject_line = False
                elif is_subject_line and line.strip() == "":
                    continue
                else:
                    is_subject_line = False
                    body_lines.append(line)

            if not body_lines:
                raise ValueError("Body parsing failed")

            result_box["subject"] = subject or f"Application for {job_title} - {CANDIDATE['name']}"
            result_box["body"] = '\n'.join(body_lines).strip()

        except Exception as e:
            log(f"AI Generation failed: {e}", "WARN")

    # Use thread to prevent blocking forever if free service hangs
    thread = threading.Thread(target=_run_generation)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        log("AI Generation timed out after 20 seconds. Falling back.", "WARN")
        return None, None

    return result_box["subject"], result_box["body"]
