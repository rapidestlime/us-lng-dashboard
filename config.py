import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    EIA_API_KEY = os.getenv('EIA_API_KEY')
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')
    
    # Data refresh intervals (in minutes)
    LNG_DATA_REFRESH = 60  # 1 hour
    STORAGE_DATA_REFRESH = 1440  # 24 hours (storage updates weekly)
    NEWS_REFRESH = 15  # 315 minutes
    
    # EIA Series IDs
    EIA_SERIES = {
        # LNG Exports (Monthly, BCF)
        'lng_total': 'NG.NLNG_US_M.M',
        'lng_sabine_pass': 'NG.NLNG_SAB_M.M',
        'lng_corpus_christi': 'NG.NLNG_COR_M.M',
        'lng_cameron': 'NG.NLNG_CAM_M.M',
        'lng_freeport': 'NG.NLNG_FRE_M.M',
        'lng_cove_point': 'NG.NLNG_COV_M.M',
        'lng_elba_island': 'NG.NLNG_ELB_M.M',
        
        # Storage (Weekly, BCF)
        'storage_total': 'NG.NW2_EPG0_SWO_R48_BCF.W',
        'storage_east': 'NG.NW2_EPG0_SWO_R1Z_BCF.W',
        'storage_west': 'NG.NW2_EPG0_SWO_R2Z_BCF.W',
        'storage_producing': 'NG.NW2_EPG0_SWO_R3Z_BCF.W',
        
        # Production (Monthly, BCF)
        'production_total': 'NG.N9070US2_M.M',
        'production_associated': 'NG.N9070US1_M.M',
        'production_dry': 'NG.N9070US3_M.M',
        
        # Consumption (Monthly, BCF)
        'consumption_power': 'NG.N3035US2_M.M',
        'consumption_industrial': 'NG.N3025US2_M.M',
        'consumption_residential': 'NG.N3010US2_M.M'
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