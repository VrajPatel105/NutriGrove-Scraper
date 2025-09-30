from datetime import datetime

class UniversityConfig:
    """Configuration for all supported universities"""

    UNIVERSITIES = {
        'umassd': {
            'name': 'University of Massachusetts Dartmouth',
            'short_name': 'umassd',
            'base_url': 'https://new.dineoncampus.com/umassd/whats-on-the-menu/the-grove',
            'requires_date': True,
            'requires_meal_type': True,
            'database_name': 'cleaned_data',  # Keep existing for backward compatibility
            'dining_hall': 'the-grove'
         },
        # 'wpi': {
        #     'name': 'Worcester Polytechnic Institute',
        #     'short_name': 'wpi',
        #     'base_url': 'https://new.dineoncampus.com/WPI/whats-on-the-menu/morgan-dining-hall',
        #     'requires_date': True,
        #     'requires_meal_type': True,
        #     'database_name': 'wpi_cleaned_data',
        #     'dining_hall': 'morgan-dining-hall'
        # },
        # 'northeastern': {
        #     'name': 'Northeastern University',
        #     'short_name': 'northeastern',
        #     'base_url': 'https://new.dineoncampus.com/dining/whats-on-the-menu/founders-commons',
        #     'requires_date': True,
        #     'requires_meal_type': True,
        #     'database_name': 'northeastern_cleaned_data',
        #     'dining_hall': 'founders-commons'
        # },
        # 'northwestern': {
        #     'name': 'Northwestern University',
        #     'short_name': 'northwestern',
        #     'base_url': 'https://new.dineoncampus.com/northwestern/whats-on-the-menu/allison-dining-commons',
        #     'requires_date': True,
        #     'requires_meal_type': True,
        #     'database_name': 'northwestern_cleaned_data',
        #     'dining_hall': 'allison-dining-commons'
        # },
        # 'babson': {
        #     'name': 'Babson College',
        #     'short_name': 'babson',
        #     'base_url': 'https://new.dineoncampus.com/babson/whats-on-the-menu/trim-dining-hall',
        #     'requires_date': True,
        #     'requires_meal_type': True,
        #     'database_name': 'babson_cleaned_data',
        #     'dining_hall': 'trim-dining-hall'
        # },
        # 'fitchburg': {
        #     'name': 'Fitchburg University',
        #     'short_name': 'fitchburg',
        #     'base_url': 'https://new.dineoncampus.com/fitchburg/whats-on-the-menu/holmes-dining-commons',
        #     'requires_date': True,
        #     'requires_meal_type': True,
        #     'database_name': 'fitchburg_cleaned_data',
        #     'dining_hall': 'holmes-dining-commons'
        # },
        # 'massmaritime': {
        #     'name': 'Massachusetts Maritime Academy',
        #     'short_name': 'massmaritime',
        #     'base_url': 'https://new.dineoncampus.com/MassMaritime/whats-on-the-menu/pande-hall',
        #     'requires_date': True,
        #     'requires_meal_type': True,
        #     'database_name': 'massmaritime_cleaned_data',
        #     'dining_hall': 'pande-hall'
        # },
        # 'lasell': {
        #     'name': 'Lasell University',
        #     'short_name': 'lasell',
        #     'base_url': 'https://new.dineoncampus.com/lasell/whats-on-the-menu/valentine-dining',
        #     'requires_date': True,
        #     'requires_meal_type': True,
        #     'database_name': 'lasell_cleaned_data',
        #     'dining_hall': 'valentine-dining'
        # },
        'harvard': {
            'name': 'Harvard University',
            'short_name': 'harvard',
            'base_url': 'https://api.cs50.io/dining',  # API endpoint, not web scraping
            'requires_date': False,  # Handled by API
            'requires_meal_type': False,  # Handled by API
            'database_name': 'harvard_cleaned_data',
            'dining_hall': 'annenberg-hall',
            'api_based': True  # Special flag for API-based scraping
        }
    }

    @classmethod
    def get_university_config(cls, university_key):
        """Get configuration for a specific university"""
        return cls.UNIVERSITIES.get(university_key)

    @classmethod
    def get_all_universities(cls):
        """Get all university configurations"""
        return cls.UNIVERSITIES

    @classmethod
    def build_url(cls, university_key, date=None, meal_type=None):
        """Build the complete URL for a university's dining menu"""
        config = cls.get_university_config(university_key)
        if not config:
            raise ValueError(f"Unknown university: {university_key}")

        url = config['base_url']

        # Add date if required
        if config['requires_date'] and date:
            url += f"/{date}"

        # Add meal type if required
        if config['requires_meal_type'] and meal_type:
            url += f"/{meal_type}"

        return url

    @classmethod
    def get_database_name(cls, university_key):
        """Get the database name for a specific university"""
        config = cls.get_university_config(university_key)
        return config['database_name'] if config else None
