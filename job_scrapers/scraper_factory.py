import importlib
import os
import inspect
from job_scrapers.base_scraper import BaseJobScraper

class JobScraperFactory:
    """Factory class for creating job scrapers"""
    
    @staticmethod
    def get_available_scrapers():
        """
        Get a list of available job scraper classes by inspecting the job_scrapers package.
        
        Returns:
            dict: Dictionary mapping scraper names to their requires_login status
        """
        available_scrapers = {}
        
        # Get the directory containing the scrapers
        scrapers_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Iterate through Python files in the scrapers directory
        for filename in os.listdir(scrapers_dir):
            if filename.endswith('.py') and filename != '__init__.py' and filename != 'base_scraper.py' and filename != 'scraper_factory.py' and filename != 'scraper_coordinator.py':
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    module = importlib.import_module(f'job_scrapers.{module_name}')
                    
                    # Find scraper classes that inherit from BaseJobScraper
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseJobScraper) and 
                            obj != BaseJobScraper):
                            
                            # Get class name and assume requires_login based on naming convention
                            # Most scrapers that require login have it in their class name or are known ones
                            scraper_name = name.replace('Scraper', '').replace('JobScraper', '')
                            requires_login = any(login_site in name.lower() for login_site in ['linkedin', 'glassdoor', 'dice', 'monster'])
                            
                            # Add to available scrapers
                            available_scrapers[scraper_name] = {
                                'class': obj,
                                'requires_login': requires_login
                            }
                            
                except Exception as e:
                    print(f"Error loading module {module_name}: {str(e)}")
        
        return available_scrapers
    
    @staticmethod
    def create_scraper(scraper_name, db_instance=None):
        """
        Create an instance of the specified job scraper.
        
        Args:
            scraper_name (str): Name of the scraper to create
            db_instance: Shared database instance to pass to the scraper
            
        Returns:
            BaseJobScraper: An instance of the requested scraper
        """
        available_scrapers = JobScraperFactory.get_available_scrapers()
        
        # Check if the requested scraper exists
        for name, info in available_scrapers.items():
            if name.lower() == scraper_name.lower():
                return info['class'](db_instance=db_instance)
        
        raise ValueError(f"Scraper '{scraper_name}' not found. Available scrapers: {', '.join(available_scrapers.keys())}")