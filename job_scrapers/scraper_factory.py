import importlib
import os
import inspect
from typing import Dict, Any, List
from job_scrapers.base_scraper import BaseJobScraper
from job_scrapers.api_scrapers import create_api_scraper

class JobScraperFactory:
    """Factory class for creating job scrapers"""
    
    @staticmethod
    def get_available_scrapers():
        """
        Get a list of available job scraper classes including both web and API scrapers.
        
        Returns:
            dict: Dictionary mapping scraper names to their metadata
        """
        available_scrapers = {}
        
        # Add API scrapers first
        api_scrapers = {
            'adzuna': {
                'type': 'api',
                'requires_login': False,
                'requires_credentials': True,
                'platforms_covered': ['indeed', 'monster', 'dice', 'jobsite', 'cvlibrary'],
                'quota_limit': 1000,
                'description': 'Adzuna API - covers multiple job boards'
            },
            'jsearch': {
                'type': 'api',
                'requires_login': False,
                'requires_credentials': True,
                'platforms_covered': ['linkedin', 'glassdoor', 'indeed'],
                'quota_limit': 200,
                'description': 'JSearch API - Google for Jobs aggregator (LIMITED QUOTA)'
            },
            'arbeitsnow': {
                'type': 'api',
                'requires_login': False,
                'requires_credentials': False,
                'platforms_covered': ['arbeitsnow'],
                'quota_limit': None,
                'description': 'ArbeitsNow API - free international jobs'
            }
        }
        
        available_scrapers.update(api_scrapers)
        
        # Get web scrapers from files
        scrapers_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Iterate through Python files in the scrapers directory
        excluded_files = ['__init__.py', 'base_scraper.py', 'scraper_factory.py', 
                         'scraper_coordinator.py', 'api_scrapers.py', 'api_usage_manager.py']
        
        for filename in os.listdir(scrapers_dir):
            if filename.endswith('.py') and filename not in excluded_files:
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    module = importlib.import_module(f'job_scrapers.{module_name}')
                    
                    # Find scraper classes that inherit from BaseJobScraper
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseJobScraper) and 
                            obj != BaseJobScraper):
                            
                            # Get class name and determine if requires login
                            scraper_name = name.replace('Scraper', '').replace('JobScraper', '').lower()
                            requires_login = any(login_site in name.lower() 
                                               for login_site in ['linkedin', 'glassdoor', 'dice', 'monster'])
                            
                            # Add to available scrapers
                            available_scrapers[scraper_name] = {
                                'class': obj,
                                'type': 'web',
                                'requires_login': requires_login,
                                'requires_credentials': requires_login,
                                'platforms_covered': [scraper_name],
                                'quota_limit': None,
                                'description': f'{scraper_name.title()} web scraper'
                            }
                            
                except Exception as e:
                    print(f"Error loading module {module_name}: {str(e)}")
        
        return available_scrapers
    
    @staticmethod
    def create_scraper(scraper_name, db_instance=None, prefer_api=True):
        """
        Create an instance of the specified job scraper.
        
        Args:
            scraper_name (str): Name of the scraper to create
            db_instance: Shared database instance to pass to the scraper  
            prefer_api (bool): Whether to prefer API scrapers over web scrapers
            
        Returns:
            BaseJobScraper or BaseAPIScraper: An instance of the requested scraper
        """
        available_scrapers = JobScraperFactory.get_available_scrapers()
        scraper_name_lower = scraper_name.lower()
        
        # First, try to find an exact match
        if scraper_name_lower in available_scrapers:
            scraper_info = available_scrapers[scraper_name_lower]
            
            if scraper_info['type'] == 'api':
                return create_api_scraper(scraper_name_lower, db_instance) 
            else:
                return scraper_info['class'](db_instance=db_instance)
        
        # If prefer_api is True, look for API scrapers that cover the requested platform
        if prefer_api:
            for api_name, info in available_scrapers.items():
                if (info['type'] == 'api' and 
                    scraper_name_lower in info.get('platforms_covered', [])):
                    print(f"Using {api_name} API for {scraper_name}")
                    return create_api_scraper(api_name, db_instance)
        
        # Fallback: look for web scraper by partial match
        for name, info in available_scrapers.items():
            if (info['type'] == 'web' and 
                (name.lower() == scraper_name_lower or scraper_name_lower in name.lower())):
                return info['class'](db_instance=db_instance)
        
        available_names = list(available_scrapers.keys())
        raise ValueError(f"Scraper '{scraper_name}' not found. Available scrapers: {', '.join(available_names)}")
    
    @staticmethod
    def get_scrapers_by_type(scraper_type: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Get scrapers filtered by type.
        
        Args:
            scraper_type (str): Filter by type ('api', 'web', or None for all)
            
        Returns:
            Dict: Filtered scrapers
        """
        all_scrapers = JobScraperFactory.get_available_scrapers()
        
        if scraper_type is None:
            return all_scrapers
        
        return {name: info for name, info in all_scrapers.items() 
                if info.get('type') == scraper_type}
    
    @staticmethod
    def get_platforms_covered() -> Dict[str, List[str]]:
        """
        Get all platforms and which scrapers can handle them.
        
        Returns:
            Dict: Platform -> list of scrapers that can handle it
        """
        all_scrapers = JobScraperFactory.get_available_scrapers()
        platform_coverage = {}
        
        for scraper_name, info in all_scrapers.items():
            platforms = info.get('platforms_covered', [scraper_name])
            for platform in platforms:
                if platform not in platform_coverage:
                    platform_coverage[platform] = []
                platform_coverage[platform].append({
                    'scraper': scraper_name,
                    'type': info.get('type', 'web'),
                    'quota_limit': info.get('quota_limit'),
                    'requires_credentials': info.get('requires_credentials', False)
                })
        
        return platform_coverage