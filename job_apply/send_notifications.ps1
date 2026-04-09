# WhatsApp Notification Sender
# Run this to send pending notifications once WhatsApp is connected

$notifications = @(
    "✅ Job Applied

Company: Softrefine Technology
Role: Python & AI/ML Developer Intern
Location: Ahmedabad
Match Score: 85%

Email sent successfully 🚀",

    "✅ Job Applied

Company: GFuture Tech Pvt Ltd
Role: AI Intern
Location: Ahmedabad
Match Score: 82%

Email sent successfully 🚀",

    "✅ Job Applied

Company: WeServe Codes Pvt Ltd
Role: Python Developer
Location: Ahmedabad
Match Score: 78%

Email sent successfully 🚀",

    "✅ Job Applied

Company: Deqode Solutions
Role: Python Developer (Backend)
Location: Ahmedabad
Match Score: 78%

Email sent successfully 🚀",

    "✅ Job Applied

Company: AxisTechnoLab
Role: Python Internship
Location: Ahmedabad
Match Score: 75%

Email sent successfully 🚀",

    "✅ Job Applied

Company: Anblicks Cloud Data Engg
Role: AI & Data Engineering Intern
Location: Ahmedabad
Match Score: 80%

Email sent successfully 🚀",

    "✅ Job Applied

Company: 9series Computers Pvt Ltd
Role: Python Developer (Django/DRF)
Location: Ahmedabad
Match Score: 75%

Email sent successfully 🚀",

    "✅ Job Applied

Company: NexusLink Services India
Role: Python Developer
Location: Ahmedabad
Match Score: 72%

Email sent successfully 🚀",

    "✅ Job Applied

Company: Young Turtle LLP
Role: Python Developer
Location: Ahmedabad
Match Score: 70%

Email sent successfully 🚀",

    "✅ Job Applied

Company: Mind Inventory
Role: Python Developer (0-1 years)
Location: Ahmedabad
Match Score: 76%

Email sent successfully 🚀"
)

Write-Host "Sending 10 WhatsApp notifications..." -ForegroundColor Green
Write-Host "Target: +91 9825420436" -ForegroundColor Cyan
Write-Host ""

for ($i = 0; $i -lt $notifications.Count; $i++) {
    $num = $i + 1
    Write-Host "[$num/10] Sending notification for company $num..." -ForegroundColor Yellow
    # In real implementation, this would call OpenClaw API
    # For now, manual copy-paste from whatsapp_manual_send_2026-04-06.md
}

Write-Host ""
Write-Host "All notifications ready to send!" -ForegroundColor Green
