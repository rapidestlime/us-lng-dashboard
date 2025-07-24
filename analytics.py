import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional
from config import Config
import numpy as np
from scipy import stats


logger = logging.getLogger(__name__)

class NaturalGasAnalytics:
    def __init__(self):
        self.facilities = Config.LNG_FACILITIES
        
    def calculate_storage_percentiles(self, storage_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate storage percentiles vs historical data"""
        if storage_df.empty:
            return pd.DataFrame()
            
        # Add temporal features
        storage_df = storage_df.copy()
        storage_df['period'] = pd.to_datetime(storage_df['period'])
        storage_df['week'] = storage_df['period'].dt.isocalendar().week
        storage_df['year'] = storage_df['period'].dt.year
        storage_df['month'] = storage_df['period'].dt.month
        
        print(storage_df['year'].unique())
        
        current_year = datetime.now().year
        historical_years = list(range(current_year - 5, current_year))
        
        results = []
        for _, row in storage_df.iterrows():
            week = row['week']
            current_value = row['value']
            
            # Get historical data for same week
            historical_data = storage_df[
                (storage_df['week'] == week) & 
                (storage_df['year'].isin(historical_years))
            ]['value'].dropna()
            
            if len(historical_data) >= 3:  # Need minimum data points
                percentile = stats.percentileofscore(historical_data, current_value)
                z_score = (current_value - historical_data.mean()) / historical_data.std()
                
                results.append({
                    'period': row['period'],
                    'current_storage': current_value,
                    'percentile': percentile,
                    'z_score': z_score,
                    'historical_min': historical_data.min(),
                    'historical_max': historical_data.max(),
                    'historical_mean': historical_data.mean(),
                    'historical_std': historical_data.std(),
                    'week': week
                })
        
        return pd.DataFrame(results)
    
    def calculate_lng_utilization(self, lng_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate LNG facility utilization rates"""
        utilization_data = []
        
        for facility_name, facility_info in self.facilities.items():
            # Map facility name to data key
            data_key = f"lng_{facility_name.lower().replace(' ', '_')}"
            
            if data_key in lng_data and not lng_data[data_key].empty:
                df = lng_data[data_key].copy()
                capacity = facility_info['current_capacity']
                
                # Convert monthly BCF to daily Bcf/d (approximate)
                df['daily_exports'] = (df['value'] / 30.44) / 1000  # Convert MMcf/month to Bcf/d
                df['utilization_rate'] = (df['daily_exports'] / capacity) * 100
                df['facility'] = facility_name
                df['capacity_bcfd'] = capacity
                df['operator'] = facility_info['operator']
                df['location'] = facility_info['location']
                df['future_capacity'] = facility_info['future_capacity']
                
                utilization_data.append(df)
        
        if utilization_data:
            combined_df = pd.concat(utilization_data, ignore_index=True)
            return combined_df.sort_values(['facility', 'period'])
        
        return pd.DataFrame()
    
    def detect_storage_anomalies(self, percentile_df: pd.DataFrame) -> Dict[str, list]:
        """Detect storage level anomalies"""
        anomalies = {
            'high_storage': [],
            'low_storage': [],
            'rapid_changes': []
        }
        
        if percentile_df.empty:
            return anomalies
            
        latest = percentile_df.iloc[-1]
        
        # High/low storage alerts
        if latest['percentile'] > Config.ALERT_THRESHOLDS['storage_high_percentile']:
            anomalies['high_storage'].append({
                'date': latest['period'],
                'percentile': latest['percentile'],
                'storage': latest['current_storage'],
                'message': f"Storage at {latest['percentile']:.0f}th percentile - potential bearish pressure"
            })
        
        if latest['percentile'] < Config.ALERT_THRESHOLDS['storage_low_percentile']:
            anomalies['low_storage'].append({
                'date': latest['period'],
                'percentile': latest['percentile'],
                'storage': latest['current_storage'],
                'message': f"Storage at {latest['percentile']:.0f}th percentile - potential bullish pressure"
            })
        
        # Rapid change detection (week-over-week)
        if len(percentile_df) >= 2:
            prev_week = percentile_df.iloc[-2]
            storage_change = latest['current_storage'] - prev_week['current_storage']
            
            if abs(storage_change) > 100:  # More than 100 BCF change
                anomalies['rapid_changes'].append({
                    'date': latest['period'],
                    'change': storage_change,
                    'message': f"Large storage change: {storage_change:+.0f} BCF week-over-week"
                })
        
        return anomalies
    
    def calculate_lng_export_growth(self, lng_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate LNG export growth trends"""
        if 'lng_total' not in lng_data:
            return pd.DataFrame()
            
        df = lng_data['lng_total'].copy()
        
        # Calculate year-over-year growth
        df['year'] = df['period'].dt.year
        df['month'] = df['period'].dt.month
        
        # Merge with previous year data
        df_prev = df.copy()
        df_prev['year'] = df_prev['year'] + 1
        df_prev = df_prev[['year', 'month', 'value']].rename(columns={'value': 'prev_year_value'})
        
        df = df.merge(df_prev, on=['year', 'month'], how='left')
        df['yoy_growth'] = ((df['value'] - df['prev_year_value']) / df['prev_year_value']) * 100
        
        # Calculate monthly growth
        df['mom_growth'] = df['value'].pct_change() * 100
        
        # Calculate rolling averages
        df['ma_3m'] = df['value'].rolling(window=3).mean()
        df['ma_12m'] = df['value'].rolling(window=12).mean()
        
        return df