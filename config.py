# config.py

from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Personal Information
    YOUR_NAME = os.getenv('YOUR_NAME', 'Your Name')
    YOUR_TITLE = "Frontend Developer"
    YOUR_SKILLS = "React, TypeScript, Next.js, and Web3 technologies"
    YOUR_EXPERIENCE = "3+ years"  # Add your experience level
    # YOUR_PORTFOLIO = os.getenv('PORTFOLIO_URL', 'your-portfolio-url')
    YOUR_GITHUB = os.getenv('GITHUB_URL', 'your-github-url')
    YOUR_LINKEDIN = os.getenv('LINKEDIN_URL', 'your-linkedin-url')
    
    # Highlight Projects (for referencing in emails)
    PORTFOLIO_HIGHLIGHTS = {
        'project1': {
            'name': 'Project Name',
            'description': 'Brief description',
            'url': 'project-url',
            'tech_stack': ['React', 'TypeScript', 'Web3']
        },
        # Add more projects as needed
    }

    # Email Settings (existing settings remain the same)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    
    # Enhanced Email Templates
    DEFAULT_EMAIL_TEMPLATES = {
        'initial_outreach': {
            'name': 'Initial Outreach',
            'subject': 'Experienced {{position}} interested in {{company}}',
            'body': f'''Hi {{name}},

I noticed that {{company}} is looking for a {{position}}, and I'm very interested in the opportunity. As a {YOUR_TITLE} with {YOUR_EXPERIENCE} experience in {YOUR_SKILLS}, I believe I could be a great fit for your team.

What particularly excites me about {{company}} is {{company_highlight}}. Your work in {{specific_area}} aligns perfectly with my experience in {{relevant_project}}.

Here's a quick overview of my relevant experience:
- {YOUR_EXPERIENCE} as a {YOUR_TITLE}
- Github: {YOUR_GITHUB}
- LinkedIn: {YOUR_LINKEDIN}

Would you be open to a brief conversation about how my experience could benefit {{company}}?

Best regards,
{YOUR_NAME}''',
            'variables': ['name', 'company', 'position', 'company_highlight', 'specific_area', 'relevant_project']
        },
        'follow_up': {
            'name': 'Follow Up',
            'subject': 'Following up - {{position}} role at {{company}}',
            'body': f'''Hi {{name}},

I wanted to follow up on my previous message regarding the {{position}} role at {{company}}. I remain very interested in the opportunity and wanted to ensure you received my application.

Since my last message, I've completed a new project using {{relevant_tech}}, which I believe would be particularly relevant to your team's needs. You can view it here: {{project_url}}

I would greatly appreciate the opportunity to discuss how my skills and recent project work align with {{company}}'s needs.

Best regards,
{YOUR_NAME}''',
            'variables': ['name', 'company', 'position', 'relevant_tech', 'project_url']
        },
        'thank_you': {
            'name': 'Interview Thank You',
            'subject': 'Thank you for your time - {{position}} discussion',
            'body': f'''Hi {{name}},

Thank you for taking the time to discuss the {{position}} role at {{company}} today. Our conversation about {{discussion_topic}} was particularly interesting, and I appreciate you sharing insights about {{company}}'s approach to {{specific_point}}.

{{custom_followup}}

I'm excited about the possibility of joining {{company}} and contributing to {{team_goal}}.

Best regards,
{YOUR_NAME}''',
            'variables': ['name', 'company', 'position', 'discussion_topic', 'specific_point', 'custom_followup', 'team_goal']
        }
    }
    
    # Success Metrics Configuration
    SUCCESS_METRICS = {
        'response_timeout_days': 14,
        'success_indicators': [
            'interview',
            'call',
            'meet',
            'discuss',
            'available',
            'interest',
            'consider'
        ],
        'failure_indicators': [
            'not available',
            'not interested',
            'not considering',
            'filled',
            'closed'
        ]
    }