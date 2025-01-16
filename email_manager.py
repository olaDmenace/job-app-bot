# email_manager.py

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from config import Config
import json

class EmailManager:
    def __init__(self, db_instance):
        self.db = db_instance
        self.emails_sent_today = 0
        self.last_email_time = None
        self.config = Config()
        
        # Load default templates if they don't exist
        self._init_default_templates()

    def _init_default_templates(self):
        """Initialize default email templates in the database"""
        for template_key, template_data in self.config.DEFAULT_EMAIL_TEMPLATES.items():
            self.db.add_email_template({
                'name': template_data['name'],
                'subject': template_data['subject'],
                'body': template_data['body'],
                'use_case': template_key,
                'variables': json.dumps(['name', 'company', 'position', 'company_highlight', 'relevant_project'])
            })

    def create_email_message(self, contact_data, template_name, custom_variables=None):
        """Create an email message using a template"""
        try:
            # Get the template
            templates = self.db.get_email_templates()
            template = next((t for t in templates if t['name'] == template_name), None)
            
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
            
            # Combine contact data with custom variables
            variables = {
                'name': contact_data['name'],
                'company': contact_data['company'],
                'position': contact_data.get('position', 'Frontend Developer'),
            }
            if custom_variables:
                variables.update(custom_variables)
            
            # Replace variables in template
            subject = template['subject']
            body = template['body']
            
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                subject = subject.replace(placeholder, str(var_value))
                body = body.replace(placeholder, str(var_value))
            
            return {
                'subject': subject,
                'body': body,
                'template_id': template.get('id')
            }
            
        except Exception as e:
            print(f"Error creating email message: {str(e)}")
            raise

    def send_email(self, to_email, subject, body):
        """Send an email with rate limiting"""
        try:
            # Check rate limits
            now = datetime.now()
            
            # Reset daily counter if it's a new day
            if self.last_email_time and self.last_email_time.date() != now.date():
                self.emails_sent_today = 0
            
            # Check maximum emails per day
            if self.emails_sent_today >= self.config.MAX_EMAILS_PER_DAY:
                raise Exception("Maximum daily email limit reached")
            
            # Respect minimum delay between emails
            if self.last_email_time:
                time_since_last = (now - self.last_email_time).total_seconds()
                if time_since_last < self.config.MIN_DELAY_BETWEEN_EMAILS:
                    time.sleep(self.config.MIN_DELAY_BETWEEN_EMAILS - time_since_last)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_ADDRESS
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_ADDRESS, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            # Update counters
            self.emails_sent_today += 1
            self.last_email_time = now
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            raise

    def send_outreach_email(self, contact_id, template_name, custom_variables=None):
        """Send an outreach email to a contact"""
        try:
            # Get contact details
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT oc.*, c.name as company_name
                FROM outreach_contacts oc
                JOIN companies c ON oc.company_id = c.id
                WHERE oc.id = ?
            """, (contact_id,))
            
            contact = cursor.fetchone()
            if not contact:
                raise ValueError(f"Contact with ID {contact_id} not found")
            
            contact_data = {
                'name': contact['name'],
                'company': contact['company_name']
            }
            
            # Create email message
            email_content = self.create_email_message(contact_data, template_name, custom_variables)
            
            # Send email
            if self.send_email(contact['email'], email_content['subject'], email_content['body']):
                # Track the outreach
                message_data = {
                    'contact_id': contact_id,
                    'template_id': email_content['template_id'],
                    'subject': email_content['subject'],
                    'message': email_content['body']
                }
                self.db.track_outreach_message(message_data)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending outreach email: {str(e)}")
            raise

    def process_follow_ups(self):
        """Process all pending follow-ups"""
        try:
            pending_follow_ups = self.db.get_pending_follow_ups()
            
            for follow_up in pending_follow_ups:
                try:
                    # Create follow-up email
                    custom_vars = {
                        'original_subject': follow_up['subject'],
                        'days_ago': (datetime.now() - datetime.strptime(follow_up['sent_date'], "%Y-%m-%d %H:%M:%S")).days
                    }
                    
                    self.send_outreach_email(
                        follow_up['contact_id'],
                        'Follow Up',
                        custom_vars
                    )
                    
                except Exception as e:
                    print(f"Error processing follow-up for message {follow_up['message_id']}: {str(e)}")
                    continue
            
            return len(pending_follow_ups)
            
        except Exception as e:
            print(f"Error processing follow-ups: {str(e)}")
            raise

        # Add these methods to your email_manager.py

def analyze_response(self, message_id, response_text):
    """Analyze response content and update success metrics"""
    try:
        response_text = response_text.lower()
        
        # Check for success indicators
        is_success = any(indicator in response_text 
                        for indicator in self.config.SUCCESS_METRICS['success_indicators'])
        
        # Check for failure indicators
        is_failure = any(indicator in response_text 
                        for indicator in self.config.SUCCESS_METRICS['failure_indicators'])
        
        if is_success:
            status = 'Positive'
        elif is_failure:
            status = 'Negative'
        else:
            status = 'Neutral'
            
        # Update message status
        self.db.update_message_status(message_id, 'Replied', status)
        
        # Update template success rate
        self._update_template_metrics(message_id, status == 'Positive')
        
        return status
        
    except Exception as e:
        print(f"Error analyzing response: {str(e)}")
        raise

def _update_template_metrics(self, message_id, was_successful):
    """Update success metrics for the email template"""
    try:
        cursor = self.db.conn.cursor()
        
        # Get template ID from message
        cursor.execute("""
            SELECT template_id 
            FROM outreach_messages 
            WHERE id = ?
        """, (message_id,))
        
        template_id = cursor.fetchone()[0]
        
        # Update template success rate
        cursor.execute("""
            UPDATE email_templates 
            SET success_rate = (
                SELECT AVG(CASE 
                    WHEN response_type = 'Positive' THEN 1.0 
                    ELSE 0.0 
                END)
                FROM outreach_messages
                WHERE template_id = ? 
                AND response_type IS NOT NULL
            )
            WHERE id = ?
        """, (template_id, template_id))
        
        self.db.conn.commit()
        
    except Exception as e:
        print(f"Error updating template metrics: {str(e)}")
        raise

def get_template_performance(self):
    """Get performance metrics for all templates"""
    try:
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT 
                t.name,
                t.success_rate,
                COUNT(m.id) as total_sent,
                SUM(CASE WHEN m.response_type = 'Positive' THEN 1 ELSE 0 END) as positive_responses,
                SUM(CASE WHEN m.response_type = 'Negative' THEN 1 ELSE 0 END) as negative_responses,
                SUM(CASE WHEN m.response_type IS NULL THEN 1 ELSE 0 END) as awaiting_response
            FROM email_templates t
            LEFT JOIN outreach_messages m ON t.id = m.template_id
            GROUP BY t.id
        """)
        
        columns = ['name', 'success_rate', 'total_sent', 'positive_responses', 
                  'negative_responses', 'awaiting_response']
        
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
        
    except Exception as e:
        print(f"Error getting template performance: {str(e)}")
        raise