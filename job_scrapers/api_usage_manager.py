import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class APIUsageManager:
    """Manages API quotas, usage tracking, and smart source selection"""
    
    def __init__(self, usage_file="jsearch_usage.json"):
        """
        Initialize the API usage manager.
        
        Args:
            usage_file (str): Path to the usage tracking file
        """
        self.usage_file = usage_file
        self.usage_data = self._load_usage_data()
        
        # API Limits (monthly)
        self.limits = {
            'jsearch': 200,    # JSearch via RapidAPI - CRITICAL LIMIT
            'adzuna': 1000,    # Adzuna API - generous limit
        }
        
        # Priority order for different query types
        self.query_priorities = {
            'high_value': ['senior', 'principal', 'lead', 'architect', 'staff'],
            'salary_research': ['glassdoor', 'salary', 'compensation'],
            'linkedin_specific': ['linkedin', 'premium'],
            'company_specific': ['google', 'facebook', 'amazon', 'microsoft', 'apple']
        }
    
    def _load_usage_data(self) -> Dict:
        """Load usage data from file"""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return {
            'jsearch': {'current_month': self._get_current_month(), 'usage': 0},
            'adzuna': {'current_month': self._get_current_month(), 'usage': 0}
        }
    
    def _save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save usage data: {e}")
    
    def _get_current_month(self) -> str:
        """Get current month in YYYY-MM format"""
        return datetime.now().strftime("%Y-%m")
    
    def _reset_if_new_month(self, api_name: str):
        """Reset usage counter if we're in a new month"""
        current_month = self._get_current_month()
        if api_name not in self.usage_data:
            self.usage_data[api_name] = {'current_month': current_month, 'usage': 0}
        elif self.usage_data[api_name]['current_month'] != current_month:
            self.usage_data[api_name] = {'current_month': current_month, 'usage': 0}
            self._save_usage_data()
    
    def can_use_api(self, api_name: str, estimated_calls: int = 1) -> bool:
        """
        Check if we can use the specified API within quota limits.
        
        Args:
            api_name (str): Name of the API ('jsearch' or 'adzuna')
            estimated_calls (int): Number of calls we plan to make
            
        Returns:
            bool: True if we have quota remaining
        """
        self._reset_if_new_month(api_name)
        
        current_usage = self.usage_data[api_name]['usage']
        limit = self.limits.get(api_name, 0)
        
        return (current_usage + estimated_calls) <= limit
    
    def get_remaining_quota(self, api_name: str) -> int:
        """
        Get remaining quota for an API.
        
        Args:
            api_name (str): Name of the API
            
        Returns:
            int: Number of calls remaining this month
        """
        self._reset_if_new_month(api_name)
        
        current_usage = self.usage_data[api_name]['usage']
        limit = self.limits.get(api_name, 0)
        
        return max(0, limit - current_usage)
    
    def log_api_usage(self, api_name: str, calls_made: int):
        """
        Log API usage.
        
        Args:
            api_name (str): Name of the API used
            calls_made (int): Number of calls made
        """
        self._reset_if_new_month(api_name)
        
        self.usage_data[api_name]['usage'] += calls_made
        self._save_usage_data()
        
        # Warn if approaching limits
        remaining = self.get_remaining_quota(api_name)
        if api_name == 'jsearch':
            if remaining <= 20:
                print(f"WARNING: Only {remaining} JSearch calls remaining this month!")
            elif remaining <= 50:
                print(f"JSearch quota: {remaining} calls remaining this month")
    
    def classify_query_priority(self, query: str) -> str:
        """
        Classify a query to determine its priority for JSearch usage.
        
        Args:
            query (str): The search query
            
        Returns:
            str: Priority level ('high', 'medium', 'low')
        """
        query_lower = query.lower()
        
        # High priority: senior roles, salary research, company-specific
        for priority_type, keywords in self.query_priorities.items():
            if any(keyword in query_lower for keyword in keywords):
                return 'high'
        
        # Medium priority: specific technologies or roles
        tech_keywords = ['react', 'nodejs', 'python', 'frontend', 'backend', 'fullstack']
        if any(keyword in query_lower for keyword in tech_keywords):
            return 'medium'
        
        # Low priority: broad searches
        return 'low'
    
    def get_optimal_api_strategy(self, query: str, platforms: List[str], max_results: int = 50) -> List[Tuple[str, str, int]]:
        """
        Get optimal API usage strategy for a query.
        
        Args:
            query (str): The search query
            platforms (List[str]): List of platforms to search
            max_results (int): Maximum results needed
            
        Returns:
            List[Tuple[str, str, int]]: List of (api_name, platform, estimated_calls) tuples
        """
        strategy = []
        query_priority = self.classify_query_priority(query)
        
        # Always try Adzuna first if available (generous quota)
        if self.can_use_api('adzuna', 1):
            adzuna_platforms = ['indeed', 'monster', 'dice', 'jobsite', 'cvlibrary']
            for platform in platforms:
                if platform.lower() in adzuna_platforms:
                    strategy.append(('adzuna', platform, 1))
        
        # Use JSearch strategically based on query priority and quota
        jsearch_remaining = self.get_remaining_quota('jsearch')
        
        if jsearch_remaining > 0:
            # High priority queries: use JSearch for LinkedIn/Glassdoor
            if query_priority == 'high':
                jsearch_platforms = ['linkedin', 'glassdoor']
                for platform in platforms:
                    if platform.lower() in jsearch_platforms and jsearch_remaining > 0:
                        strategy.append(('jsearch', platform, 1))
                        jsearch_remaining -= 1
            
            # Medium priority: use JSearch sparingly
            elif query_priority == 'medium' and jsearch_remaining > 10:
                if 'linkedin' in [p.lower() for p in platforms]:
                    strategy.append(('jsearch', 'linkedin', 1))
        
        # Fallback to working scrapers for remaining platforms
        working_scrapers = ['web3career']  # Add other working scrapers as needed
        for platform in platforms:
            if platform.lower() in working_scrapers:
                strategy.append(('scraper', platform, 0))
        
        return strategy
    
    def should_cache_results(self, api_name: str, query: str) -> bool:
        """
        Determine if results should be cached to avoid duplicate API calls.
        
        Args:
            api_name (str): Name of the API
            query (str): The search query
            
        Returns:
            bool: True if results should be cached
        """
        # Always cache JSearch results (limited quota)
        if api_name == 'jsearch':
            return True
        
        # Cache Adzuna results for broad queries
        if api_name == 'adzuna' and self.classify_query_priority(query) == 'low':
            return True
        
        return False
    
    def get_quota_status(self) -> Dict[str, Dict]:
        """
        Get current quota status for all APIs.
        
        Returns:
            Dict: Quota status for each API
        """
        status = {}
        
        for api_name in self.limits.keys():
            self._reset_if_new_month(api_name)
            
            used = self.usage_data[api_name]['usage']
            limit = self.limits[api_name]
            remaining = limit - used
            percentage_used = (used / limit) * 100
            
            status[api_name] = {
                'used': used,
                'limit': limit,
                'remaining': remaining,
                'percentage_used': round(percentage_used, 1),
                'status': self._get_quota_status_level(percentage_used)
            }
        
        return status
    
    def _get_quota_status_level(self, percentage_used: float) -> str:
        """Get quota status level based on usage percentage"""
        if percentage_used >= 90:
            return 'critical'
        elif percentage_used >= 75:
            return 'warning'
        elif percentage_used >= 50:
            return 'moderate'
        else:
            return 'healthy'
    
    def print_quota_status(self):
        """Print formatted quota status"""
        status = self.get_quota_status()
        
        print("\nAPI Quota Status:")
        print("=" * 50)
        
        for api_name, info in status.items():
            status_text = {
                'healthy': '[OK]',
                'moderate': '[WARN]',
                'warning': '[LOW]',
                'critical': '[CRITICAL]'
            }.get(info['status'], '[UNKNOWN]')
            
            print(f"{status_text} {api_name.upper()}: {info['used']}/{info['limit']} calls ({info['percentage_used']}%)")
            print(f"   Remaining: {info['remaining']} calls")
        
        print("=" * 50)
    
    def get_usage_recommendations(self, query: str, platforms: List[str]) -> List[str]:
        """
        Get recommendations for optimal API usage.
        
        Args:
            query (str): The search query
            platforms (List[str]): Requested platforms
            
        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        strategy = self.get_optimal_api_strategy(query, platforms)
        
        # Check if JSearch usage is optimal
        jsearch_remaining = self.get_remaining_quota('jsearch')
        query_priority = self.classify_query_priority(query)
        
        if jsearch_remaining <= 20:
            recommendations.append(f"WARNING: JSearch quota low ({jsearch_remaining} calls left). Use for high-priority searches only.")
        
        if query_priority == 'low' and any(api == 'jsearch' for api, _, _ in strategy):
            recommendations.append("TIP: Consider using Adzuna API for broad searches to preserve JSearch quota.")
        
        if not any(api == 'adzuna' for api, _, _ in strategy) and self.can_use_api('adzuna'):
            recommendations.append("TIP: Adzuna API available with generous quota - consider using for Indeed/Monster/Dice.")
        
        # Suggest caching
        if query_priority in ['medium', 'high']:
            recommendations.append("TIP: Results will be cached to avoid duplicate API calls.")
        
        return recommendations