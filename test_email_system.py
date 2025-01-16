# test_email_system.py

import unittest
from database_manager import JobApplicationDB
from email_manager import EmailManager
from config import Config
import os
from datetime import datetime
import warnings
import urllib3

# Suppress SSL warnings
warnings.filterwarnings('ignore', category=urllib3.exceptions.NotOpenSSLWarning)

class TestEmailSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database and managers"""
        # Use a test database file
        cls.test_db_path = "test_job_applications.db"
        cls.db = JobApplicationDB(db_path=cls.test_db_path)
        cls.email_manager = EmailManager(cls.db)
        cls.config = Config()

    def setUp(self):
        """Set up before each test"""
        # Clear existing test data
        self.db.conn.execute("DELETE FROM outreach_messages")
        self.db.conn.execute("DELETE FROM email_templates")
        self.db.conn.execute("DELETE FROM outreach_contacts")
        self.db.conn.execute("DELETE FROM companies")
        self.db.conn.commit()

    def test_config_loading(self):
        """Test that configuration is properly loaded"""
        self.assertIsNotNone(self.config.YOUR_NAME)
        self.assertIsNotNone(self.config.EMAIL_ADDRESS)
        self.assertIn('initial_outreach', self.config.DEFAULT_EMAIL_TEMPLATES)

    def test_email_template_creation(self):
        """Test email template initialization"""
        # Templates should be automatically initialized by EmailManager
        templates = self.db.get_email_templates()
        self.assertTrue(len(templates) > 0)
        
        # Check specific template exists
        initial_template = next((t for t in templates if t['name'] == 'Initial Outreach'), None)
        self.assertIsNotNone(initial_template)
        self.assertIn(self.config.YOUR_NAME, initial_template['body'])

    def test_email_message_creation(self):
        """Test creating personalized email messages"""
        contact_data = {
            'name': 'Test Contact',
            'company': 'Test Company',
            'position': 'Senior Frontend Developer'
        }
        
        custom_vars = {
            'company_highlight': 'innovative DeFi projects',
            'specific_area': 'Web3',
            'relevant_project': 'a decentralized application'
        }
        
        email_content = self.email_manager.create_email_message(
            contact_data,
            'Initial Outreach',
            custom_vars
        )
        
        # Check that all variables are replaced
        self.assertIn(contact_data['name'], email_content['body'])
        self.assertIn(contact_data['company'], email_content['body'])
        self.assertIn(custom_vars['company_highlight'], email_content['body'])
        self.assertIn(self.config.YOUR_NAME, email_content['body'])
        self.assertNotIn('{{', email_content['body'])  # No unreplaced variables

    def test_contact_management(self):
        """Test adding and retrieving contacts"""
        # Add a test company
        company_data = {
            'name': 'Test Company',
            'website': 'https://testcompany.com',
            'industry': 'Web3'
        }
        
        company_id = self.db.add_company(company_data)
        
        # Add a test contact
        contact_data = {
            'company_id': company_id,
            'name': 'Test Contact',
            'title': 'Engineering Manager',
            'email': 'test@testcompany.com',
            'linkedin_url': 'https://linkedin.com/test',
            'source': 'LinkedIn',
            'is_hiring_manager': True,
            'is_technical': True
        }
        
        contact_id = self.db.add_contact(contact_data)
        
        # Retrieve and verify contact
        contacts = self.db.get_contacts_by_company('Test Company')
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]['name'], 'Test Contact')

    def test_email_tracking(self):
        """Test tracking email interactions"""
        # Create test contact and message
        company_id = self.db.add_company({'name': 'Test Company'})
        contact_id = self.db.add_contact({
            'company_id': company_id,
            'name': 'Test Contact',
            'email': 'test@test.com'
        })
        
        # Track an outreach message
        message_data = {
            'contact_id': contact_id,
            'subject': 'Test Subject',
            'message': 'Test Message',
            'template_id': 1
        }
        
        message_id = self.db.track_outreach_message(message_data)
        
        # Test response analysis
        positive_response = "I'd be interested in scheduling an interview"
        status = self.email_manager.analyze_response(message_id, positive_response)
        self.assertEqual(status, 'Positive')
        
        # Check metrics
        metrics = self.email_manager.get_template_performance()
        self.assertTrue(len(metrics) > 0)
        self.assertIn('success_rate', metrics[0])

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        cls.db.close()
        # Remove test database
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

def run_email_tests():
    """Run all email system tests"""
    print("\nTesting Email System...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEmailSystem)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    run_email_tests()