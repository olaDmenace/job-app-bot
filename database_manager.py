import os
import sqlite3
from datetime import datetime, timedelta
import json

class JobApplicationDB:
    def __init__(self, db_path="job_applications.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.conn = None
        self.create_database()

    def create_database(self):
        """Create database and tables"""
        try:
            # Read the schema file (assuming it's in the same directory)
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r') as f:
                schema = f.read()

            # Connect and create tables
            self.conn = sqlite3.connect(self.db_path)
            self.conn.executescript(schema)
            self.conn.commit()
            print(f"Database initialized at {self.db_path}")

        except Exception as e:
            print(f"Error creating database: {str(e)}")
            raise

    def ensure_connection(self):
        """Ensure database connection is valid, reconnect if needed"""
        try:
            if self.conn is None:
                self.conn = sqlite3.connect(self.db_path)
            else:
                # Test the connection
                self.conn.execute("SELECT 1")
        except sqlite3.Error:
            # Connection is bad, recreate it
            self.conn = sqlite3.connect(self.db_path)

    # Original job-related methods
    def add_job(self, job_data):
        """Add or update a job in the database"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # Check if job already exists
            cursor.execute("""
                SELECT id FROM jobs 
                WHERE job_source_id = ? AND source = ?
            """, (job_data['id'], job_data['source']))
            
            existing_job = cursor.fetchone()
            
            if existing_job:
                # Update existing job
                job_id = existing_job[0]
                cursor.execute("""
                    UPDATE jobs 
                    SET title = ?, company = ?, location = ?, salary = ?,
                        url = ?, tags = ?, date_posted = ?, description = ?,
                        is_remote = ?
                    WHERE id = ?
                """, (
                    job_data['title'], job_data['company'], job_data['location'],
                    job_data['salary'], job_data['url'], job_data['tags'],
                    job_data['posted'], job_data.get('description', ''),
                    'Remote' in job_data['location'], job_id
                ))
            else:
                # Insert new job
                cursor.execute("""
                    INSERT INTO jobs (
                        job_source_id, source, title, company, location,
                        salary, url, tags, date_posted, date_found,
                        description, is_remote
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_data['id'], job_data['source'], job_data['title'],
                    job_data['company'], job_data['location'], job_data['salary'],
                    job_data['url'], job_data['tags'], job_data['posted'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    job_data.get('description', ''),
                    'Remote' in job_data['location']
                ))
                
                job_id = cursor.lastrowid
                
                # Create initial application entry
                cursor.execute("""
                    INSERT INTO applications (
                        job_id, status, last_updated
                    ) VALUES (?, ?, ?)
                """, (
                    job_id, 'New', datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            self.conn.commit()
            return job_id

        except Exception as e:
            print(f"Error adding job: {str(e)}")
            self.conn.rollback()
            raise

    def update_application_status(self, job_id, status, notes=None):
        """Update the status of a job application"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                UPDATE applications 
                SET status = ?, notes = ?, last_updated = ?
                WHERE job_id = ?
            """, (
                status, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), job_id
            ))
            
            self.conn.commit()

        except Exception as e:
            print(f"Error updating application status: {str(e)}")
            self.conn.rollback()
            raise

    def get_all_applications(self):
        """Get all job applications with their current status"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    j.title, j.company, j.location, j.salary,
                    a.status, a.date_applied, a.notes, j.url
                FROM jobs j
                JOIN applications a ON j.id = a.job_id
                ORDER BY a.last_updated DESC
            """)
            
            columns = ['title', 'company', 'location', 'salary', 
                      'status', 'date_applied', 'notes', 'url']
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting applications: {str(e)}")
            raise

    # New contact-related methods
    def add_contact(self, contact_data):
        """Add or update a contact in the database"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # First check if company exists or needs to be created
            cursor.execute("""
                SELECT id FROM companies 
                WHERE name = ?
            """, (contact_data['company'],))
            
            company_row = cursor.fetchone()
            if company_row:
                company_id = company_row[0]
            else:
                # Insert new company
                cursor.execute("""
                    INSERT INTO companies (
                        name, last_updated
                    ) VALUES (?, ?)
                """, (
                    contact_data['company'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                company_id = cursor.lastrowid

            # Check if contact already exists
            cursor.execute("""
                SELECT id FROM outreach_contacts 
                WHERE name = ? AND company_id = ?
            """, (contact_data['name'], company_id))
            
            existing_contact = cursor.fetchone()
            
            if existing_contact:
                # Update existing contact
                cursor.execute("""
                    UPDATE outreach_contacts 
                    SET title = ?, linkedin_url = ?, wellfound_url = ?,
                        source = ?, is_hiring_manager = ?, is_technical = ?,
                        last_updated = ?
                    WHERE id = ?
                """, (
                    contact_data['title'],
                    contact_data.get('linkedin_url', ''),
                    contact_data.get('wellfound_url', ''),
                    contact_data['source'],
                    contact_data['is_hiring_manager'],
                    contact_data['is_technical'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    existing_contact[0]
                ))
                return existing_contact[0]
            else:
                # Insert new contact
                cursor.execute("""
                    INSERT INTO outreach_contacts (
                        company_id, name, title, linkedin_url, wellfound_url,
                        source, is_hiring_manager, is_technical, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    company_id,
                    contact_data['name'],
                    contact_data['title'],
                    contact_data.get('linkedin_url', ''),
                    contact_data.get('wellfound_url', ''),
                    contact_data['source'],
                    contact_data['is_hiring_manager'],
                    contact_data['is_technical'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                
                contact_id = cursor.lastrowid
                self.conn.commit()
                return contact_id

        except Exception as e:
            print(f"Error adding contact: {str(e)}")
            self.conn.rollback()
            raise

    def get_contacts_by_company(self, company_name):
        """Get all contacts for a specific company"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    oc.name, oc.title, oc.linkedin_url, oc.wellfound_url,
                    oc.source, oc.is_hiring_manager, oc.is_technical,
                    c.name as company_name
                FROM outreach_contacts oc
                JOIN companies c ON oc.company_id = c.id
                WHERE c.name = ?
                ORDER BY oc.last_updated DESC
            """, (company_name,))
            
            columns = ['name', 'title', 'linkedin_url', 'wellfound_url',
                      'source', 'is_hiring_manager', 'is_technical', 'company']
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting contacts: {str(e)}")
            raise

    # Email template methods
    def add_email_template(self, template_data):
        """Add or update an email template"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            # Check if template already exists
            cursor.execute("""
                SELECT id FROM email_templates 
                WHERE name = ?
            """, (template_data['name'],))
            
            existing_template = cursor.fetchone()
            
            if existing_template:
                # Update existing template
                cursor.execute("""
                    UPDATE email_templates 
                    SET subject = ?, body = ?, use_case = ?,
                        variables = ?, last_used = ?
                    WHERE id = ?
                """, (
                    template_data['subject'],
                    template_data['body'],
                    template_data['use_case'],
                    template_data.get('variables', '[]'),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    existing_template[0]
                ))
                return existing_template[0]
            else:
                # Insert new template
                cursor.execute("""
                    INSERT INTO email_templates (
                        name, subject, body, use_case,
                        variables, created_at, success_rate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    template_data['name'],
                    template_data['subject'],
                    template_data['body'],
                    template_data['use_case'],
                    template_data.get('variables', '[]'),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    0.0  # Initial success rate
                ))
                
                template_id = cursor.lastrowid
                self.conn.commit()
                return template_id

        except Exception as e:
            print(f"Error adding email template: {str(e)}")
            self.conn.rollback()
            raise

    def get_email_templates(self, use_case=None):
        """Get email templates, optionally filtered by use case"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            if use_case:
                cursor.execute("""
                    SELECT name, subject, body, use_case, variables, success_rate
                    FROM email_templates
                    WHERE use_case = ?
                    ORDER BY success_rate DESC
                """, (use_case,))
            else:
                cursor.execute("""
                    SELECT name, subject, body, use_case, variables, success_rate
                    FROM email_templates
                    ORDER BY success_rate DESC
                """)
            
            columns = ['name', 'subject', 'body', 'use_case', 'variables', 'success_rate']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting email templates: {str(e)}")
            raise

    # Outreach tracking methods
    def track_outreach_message(self, message_data):
        """Track an outreach message sent to a contact"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO outreach_messages (
                    contact_id, template_id, subject, message,
                    sent_date, status, next_follow_up_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message_data['contact_id'],
                message_data.get('template_id'),
                message_data['subject'],
                message_data['message'],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Sent',
                (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")  # Default follow-up in 7 days
            ))
            
            message_id = cursor.lastrowid
            self.conn.commit()
            return message_id

        except Exception as e:
            print(f"Error tracking outreach message: {str(e)}")
            self.conn.rollback()
            raise
        

    def update_message_status(self, message_id, status, response_type=None):
        """Update the status of an outreach message"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                UPDATE outreach_messages 
                SET status = ?, response_type = ?, response_date = ?
                WHERE id = ?
            """, (
                status,
                response_type,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == 'Replied' else None,
                message_id
            ))
            
            self.conn.commit()

        except Exception as e:
            print(f"Error updating message status: {str(e)}")
            self.conn.rollback()
            raise

    def get_pending_follow_ups(self):
        """Get all messages that need follow-up"""
        try:
            self.ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    om.id, om.subject, om.sent_date, om.next_follow_up_date,
                    oc.name, oc.title, c.name as company_name
                FROM outreach_messages om
                JOIN outreach_contacts oc ON om.contact_id = oc.id
                JOIN companies c ON oc.company_id = c.id
                WHERE om.status = 'Sent'
                AND om.next_follow_up_date <= ?
                ORDER BY om.next_follow_up_date ASC
            """, (datetime.now().strftime("%Y-%m-%d"),))
            
            columns = ['message_id', 'subject', 'sent_date', 'follow_up_date',
                      'contact_name', 'contact_title', 'company']
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting pending follow-ups: {str(e)}")
            raise

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()