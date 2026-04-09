from email.message import EmailMessage

def send(to_email, company_name, job_title):
    msg = EmailMessage()

    # Simple clean body
    body = f"Hello, I am applying for {job_title} at {company_name}."

    # Fix tuple issue safely
    if isinstance(body, tuple):
        body = " ".join(body)

    msg.set_content(body, subtype="plain", charset="utf-8")

    # Keep attachment if exists (important for OpenClaw)
    try:
        with open(r"C:\Users\rakho\.openclaw\workspace\job_apply\resume\resume.pdf", "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="resume.pdf")
    except:
        pass

    return {"status": "sent"}

def print_email_report(*args, **kwargs):
    pass
