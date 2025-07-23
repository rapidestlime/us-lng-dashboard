import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EIADataFetcher:
    def __init__(self):
        self.base_url = "https://api.eia.gov/v2/"
        self.api_key = Config.EIA_API_KEY
        
    def fetch_series(self, series_id: str, start_date: Optional[str] = None) -> pd.DataFrame:
        """Fetch data for a specific EIA series"""
        if not self.api_key:
            logger.error("EIA API key not configured")
            return pd.DataFrame()
            
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
            
            url = f"{self.base_url}seriesid/{series_id}"
            params = {
                'api_key': self.api_key,
                'start': start_date,
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'offset': 0,
                'length': 5000
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'response' in data and 'data' in data['response']:
                df = pd.DataFrame(data['response']['data'])
                if not df.empty:
                    df['period'] = pd.to_datetime(df['period'])
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    df = df.dropna(subset=['value'])
                    return df.sort_values('period').reset_index(drop=True)
            
            logger.warning(f"No data returned for series {series_id}")
            return pd.DataFrame()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {series_id}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching {series_id}: {e}")
            return pd.DataFrame()
    
    def fetch_multiple_series(self, series_dict: Dict[str, str]) -> Dict[str, pd.DataFrame]:
        """Fetch multiple series at once"""
        results = {}
        for name, series_id in series_dict.items():
            logger.info(f"Fetching {name} ({series_id})")
            df = self.fetch_series(series_id)
            if not df.empty:
                results[name] = df
            else:
                logger.warning(f"Failed to fetch data for {name}")
        return results

class NewsDataFetcher:
    def __init__(self):
        self.api_key = Config.NEWSAPI_KEY
        
    def fetch_news(self, keywords: str = "natural gas", limit: int = 50) -> list:
        """Fetch news from NewsAPI"""
        if not self.api_key:
            logger.error("NewsAPI API key not configured")
            return []
            
        try:
            # url = "https://www.alphavantage.co/query"
            # params = {
            #     'function': 'NEWS_SENTIMENT',
            #     'tickers': 'KOLD,UNG,BOIL,XOP,XLE',  # Natural gas and energy ETFs
            #     'topics': 'energy_transportation',
            #     'apikey': self.api_key,
            #     'limit': limit,
            #     'sort': 'LATEST'
            # }
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': '"natural gas" OR "lng"',
                'searchIn': 'content',
                'sortBy': 'publishedAt,relevancy',
                'language': 'en',
                'apikey': self.api_key,
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'articles' in data:
                logger.info(f"Fetched {len(data['articles'])} news articles") # returns latest 100 by default
                return data['articles']
            else:
                logger.warning("No news feed found in response")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching news: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []