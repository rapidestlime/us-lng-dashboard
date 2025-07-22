import schedule
import time
import threading
from datetime import datetime
import logging
from data_fetcher import EIADataFetcher, NewsDataFetcher
from analytics import NaturalGasAnalytics
from config import Config

logger = logging.getLogger(__name__)

class DataScheduler:
    def __init__(self):
        self.eia_fetcher = EIADataFetcher()
        self.news_fetcher = NewsDataFetcher()
        self.analytics = NaturalGasAnalytics()
        self.data_cache = {}
        self.last_update = {}
        
    def update_lng_data(self):
        """Update LNG export data"""
        logger.info("Updating LNG export data...")
        try:
            lng_series = {k: v for k, v in Config.EIA_SERIES.items() if k.startswith('lng_')}
            lng_data = self.eia_fetcher.fetch_multiple_series(lng_series)
            
            if lng_data:
                self.data_cache['lng_data'] = lng_data
                self.last_update['lng_data'] = datetime.now()
                logger.info(f"Updated LNG data for {len(lng_data)} facilities")
            else:
                logger.warning("No LNG data retrieved")
                
        except Exception as e:
            logger.error(f"Error updating LNG data: {e}")
    
    def update_storage_data(self):
        """Update storage data"""
        logger.info("Updating storage data...")
        try:
            storage_series = {k: v for k, v in Config.EIA_SERIES.items() if k.startswith('storage_')}
            storage_data = self.eia_fetcher.fetch_multiple_series(storage_series)
            
            if storage_data:
                self.data_cache['storage_data'] = storage_data
                self.last_update['storage_data'] = datetime.now()
                logger.info(f"Updated storage data for {len(storage_data)} regions")
            else:
                logger.warning("No storage data retrieved")
                
        except Exception as e:
            logger.error(f"Error updating storage data: {e}")
    
    def update_news_data(self):
        """Update news data"""
        logger.info("Updating news data...")
        try:
            news_data = self.news_fetcher.fetch_news()
            
            if news_data:
                self.data_cache['news_data'] = news_data
                self.last_update['news_data'] = datetime.now()
                logger.info(f"Updated {len(news_data)} news articles")
            else:
                logger.warning("No news data retrieved")
                
        except Exception as e:
            logger.error(f"Error updating news data: {e}")
    
    def run_scheduler(self):
        """Run the data scheduler"""
        # Schedule different update frequencies
        schedule.every(Config.LNG_DATA_REFRESH).minutes.do(self.update_lng_data)
        schedule.every(Config.STORAGE_DATA_REFRESH).minutes.do(self.update_storage_data)
        schedule.every(Config.NEWS_REFRESH).minutes.do(self.update_news_data)
        
        # Initial data load
        self.update_lng_data()
        self.update_storage_data()
        self.update_news_data()
        
        # Run scheduler in background
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start_background_scheduler(self):
        """Start scheduler in background thread"""
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Background data scheduler started")
    
    def get_cached_data(self, data_type: str):
        """Get cached data with freshness check"""
        if data_type not in self.data_cache:
            return None
            
        # Check if data is stale
        if data_type in self.last_update:
            time_diff = datetime.now() - self.last_update[data_type]
            max_age_minutes = {
                'lng_data': Config.LNG_DATA_REFRESH,
                'storage_data': Config.STORAGE_DATA_REFRESH,
                'news_data': Config.NEWS_REFRESH
            }.get(data_type, 60)
            
            if time_diff.total_seconds() > max_age_minutes * 60:
                logger.warning(f"Cached {data_type} is stale")
                return None
        
        return self.data_cache[data_type]