import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    EIA_API_KEY = os.getenv('EIA_API_KEY')
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')
    NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
    
    # Data refresh intervals (in minutes)
    LNG_DATA_REFRESH = 60  # 1 hour
    STORAGE_DATA_REFRESH = 1440  # 24 hours (storage updates weekly)
    NEWS_REFRESH = 15  # 315 minutes
    
    # EIA Series IDs
    EIA_SERIES = {
        # LNG Exports (Monthly, BCF)
        'lng_total': 'N9133US2',
        'lng_sabine_pass': 'NGM_EPG0_ENG_YSPL-Z00_MMCF',
        'lng_corpus_christi': 'NGM_EPG0_ENG_YCRP-Z00_MMCF',
        'lng_cameron': 'NGM_EPG0_ENG_YCAM-Z00_MMCF',
        'lng_freeport': 'NGM_EPG0_ENG_YFPT-Z00_MMCF',
        'lng_cove_point': 'NGM_EPG0_ENG_YCPT-Z00_MMCF',
        'lng_elba_island': 'NGM_EPG0_ENG_YELBA-Z00_MMCF',
        
        # Storage (Weekly, BCF)
        'storage_total': 'NW2_EPG0_SAO_R48_BCF',
        'storage_east': 'NW2_EPG0_SAO_R88_BCF',
        'storage_west': 'NW2_EPG0_SAO_R89_BCF',
        'storage_producing': 'NW2_EPG0_SAO_R87_BCF',
        
        # Production (Monthly, BCF)
        'production_total': 'N9050US2',
        'production_associated': 'N9060US2',
        'production_dry': 'N9070US2',
        
        # Consumption (Monthly, BCF)
        'consumption_power': 'NG.N3045US2.M',
        'consumption_industrial': 'NG.N3035US2.M',
        'consumption_residential': 'NG.N3010US2.M',
        'consumption_commercial': 'NG.N3020US2.M',
        'consumption_total': 'NG.N9140US2.M',

    }
    
    # LNG Facility Information
    LNG_FACILITIES = {
        'Sabine Pass': {
            'current_capacity': 4.2,  # Bcf/d
            'future_capacity': 4.2,
            'location': 'Louisiana',
            'operator': 'Cheniere Energy'
        },
        'Corpus Christi': {
            'current_capacity': 2.1,
            'future_capacity': 3.6,  # Expected by end 2025
            'location': 'Texas',
            'operator': 'Cheniere Energy'
        },
        'Cameron': {
            'current_capacity': 1.7,
            'future_capacity': 1.7,
            'location': 'Louisiana',
            'operator': 'Sempra Energy'
        },
        'Freeport': {
            'current_capacity': 2.1,
            'future_capacity': 2.1,
            'location': 'Texas',
            'operator': 'Freeport LNG'
        },
        'Cove Point': {
            'current_capacity': 0.75,
            'future_capacity': 0.75,
            'location': 'Maryland',
            'operator': 'Dominion Energy'
        },
        'Elba Island': {
            'current_capacity': 0.35,
            'future_capacity': 0.35,
            'location': 'Georgia',
            'operator': 'Shell/Kinder Morgan'
        }
    }
    
    # Alert thresholds
    ALERT_THRESHOLDS = {
        'storage_high_percentile': 80,
        'storage_low_percentile': 20,
        'lng_utilization_high': 90,
        'lng_utilization_low': 60,
        'basis_zscore_threshold': 2.0
    }