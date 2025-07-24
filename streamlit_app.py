import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, timezone
import logging
from scheduler import DataScheduler
from analytics import NaturalGasAnalytics
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global scheduler
@st.cache_resource
def get_data_scheduler():
    scheduler = DataScheduler()
    scheduler.start_background_scheduler()
    return scheduler

def create_enhanced_lng_dashboard(scheduler: DataScheduler):
    """Enhanced LNG Export Analytics Dashboard"""
    st.header("🚢 U.S. LNG Export Analytics Dashboard")
    
    # Get cached data
    lng_data = scheduler.get_cached_data('lng_data')
    if not lng_data:
        st.error("LNG data not available. Please check data pipeline.")
        return
    
    analytics = NaturalGasAnalytics()
    utilization_df = analytics.calculate_lng_utilization(lng_data)
    
    if utilization_df.empty:
        st.warning("No LNG utilization data available")
        return
    
    # Calculate key metrics
    latest_data = utilization_df.groupby('facility').last().reset_index()
    total_capacity = latest_data['capacity_bcfd'].sum()
    avg_utilization = latest_data['utilization_rate'].mean()
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total LNG Capacity", f"{total_capacity:.1f} Bcf/d")
    
    with col2:
        color = "normal"
        if avg_utilization > 85:
            color = "inverse"
        elif avg_utilization < 70:
            color = "off"
        st.metric("Average Utilization", f"{avg_utilization:.1f}%")
    
    with col3:
        if 'lng_total' in lng_data:
            latest_exports = lng_data['lng_total']['value'].iloc[-1]
            prev_exports = lng_data['lng_total']['value'].iloc[-2] if len(lng_data['lng_total']) > 1 else latest_exports
            change = latest_exports - prev_exports
            st.metric("Latest Monthly Exports", f"{latest_exports:.1f} Bcf", f"{change:+.1f} Bcf")
        else:
            st.metric("Latest Monthly Exports", "N/A")
    
    with col4:
        # Calculate approximate feedgas demand
        if 'lng_total' in lng_data:
            feedgas_demand = (latest_exports / 0.9) / 30.44  # 90% efficiency, convert to Bcf/d
            st.metric("Est. Feedgas Demand", f"{feedgas_demand:.1f} Bcf/d")
        else:
            st.metric("Est. Feedgas Demand", "N/A")
    
    # Facility utilization chart
    col1, col2 = st.columns(2)
    
    with col1:
        # Current utilization by facility
        fig_current = px.bar(
            latest_data, 
            x='facility', 
            y='utilization_rate',
            title='Current LNG Facility Utilization',
            labels={'utilization_rate': 'Utilization (%)', 'facility': 'Facility'},
            color='utilization_rate',
            color_continuous_scale='RdYlGn'
        )
        fig_current.add_hline(y=90, line_dash="dash", line_color="red", 
                             annotation_text="High Utilization")
        fig_current.update_layout(height=400)
        st.plotly_chart(fig_current, use_container_width=True)
    
    with col2:
        # Capacity vs current utilization
        fig_capacity = go.Figure()
        
        for _, row in latest_data.iterrows():
            utilized = row['capacity_bcfd'] * (row['utilization_rate'] / 100)
            unused = row['capacity_bcfd'] - utilized
            
            fig_capacity.add_trace(go.Bar(
                name=row['facility'],
                x=[row['facility']],
                y=[utilized],
                marker_color='green'
            ))
            
            fig_capacity.add_trace(go.Bar(
                name=f"{row['facility']} Unused",
                x=[row['facility']],
                y=[unused],
                marker_color='lightgray',
                showlegend=False
            ))
        
        fig_capacity.update_layout(
            title='LNG Capacity Utilization (Bcf/d)',
            barmode='stack',
            height=400,
            yaxis_title='Capacity (Bcf/d)',
            xaxis_title='Facility'
        )
        st.plotly_chart(fig_capacity, use_container_width=True)
    
    # Time series analysis
    st.subheader("📈 Export Trends Analysis")
    
    # Filter for recent data (last 24 months)
    recent_data = utilization_df[utilization_df['period'] >= (datetime.now() - timedelta(days=730))]
    
    if not recent_data.empty:
        fig_trends = px.line(
            recent_data, 
            x='period', 
            y='value', 
            color='facility',
            title='LNG Export Volumes by Facility (24-Month Trend)',
            labels={'value': 'Monthly Exports (BCF)', 'period': 'Date'}
        )
        fig_trends.update_layout(height=500)
        st.plotly_chart(fig_trends, use_container_width=True)
        
        # Utilization trends
        fig_util_trend = px.line(
            recent_data, 
            x='period', 
            y='utilization_rate', 
            color='facility',
            title='LNG Facility Utilization Trends',
            labels={'utilization_rate': 'Utilization (%)', 'period': 'Date'}
        )
        fig_util_trend.add_hline(y=85, line_dash="dash", line_color="orange", 
                                annotation_text="High Utilization Threshold")
        fig_util_trend.update_layout(height=400)
        st.plotly_chart(fig_util_trend, use_container_width=True)
    
    # Facility details table
    st.subheader("🏭 Facility Details")
    
    facility_summary = latest_data  # No need to merge, columns already present

    display_cols = [
        'facility', 'operator', 'location', 'capacity_bcfd', 
        'future_capacity', 'utilization_rate', 'daily_exports'
    ]
    
    if not facility_summary.empty:
        st.dataframe(
            facility_summary[display_cols].round(2),
            column_config={
                'facility': 'Facility',
                'operator': 'Operator',
                'location': 'Location',
                'capacity_bcfd': st.column_config.NumberColumn('Current Capacity (Bcf/d)', format='%.1f'),
                'future_capacity': st.column_config.NumberColumn('Future Capacity (Bcf/d)', format='%.1f'),
                'utilization_rate': st.column_config.NumberColumn('Utilization (%)', format='%.1f'),
                'daily_exports': st.column_config.NumberColumn('Current Exports (Bcf/d)', format='%.2f')
            },
            use_container_width=True
        )

def create_enhanced_storage_dashboard(scheduler: DataScheduler):
    """Enhanced Storage Analytics Dashboard"""
    st.header("📊 U.S. Natural Gas Storage Analytics")
    
    # Get cached data
    storage_data = scheduler.get_cached_data('storage_data')
    # st.write("DEBUG: storage_data keys:", list(storage_data.keys()) if storage_data else "No data")
    if not storage_data:
        st.error("Storage data not available. Please check data pipeline.")
        return
    
    analytics = NaturalGasAnalytics()
    
    # Process total storage data
    if 'storage_total' in storage_data:
        total_storage = storage_data['storage_total']
        # st.write("DEBUG: total_storage shape:", total_storage.shape)
        # st.write("DEBUG: total_storage columns:", total_storage.columns)
        # st.write("DEBUG: total_storage head:", total_storage.head())
        percentile_df = analytics.calculate_storage_percentiles(total_storage)
        # st.write("DEBUG: percentile_df shape:", percentile_df.shape if hasattr(percentile_df, 'shape') else "No df")
        
        if not percentile_df.empty:
            latest = percentile_df.iloc[-1]
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Storage", f"{latest['current_storage']:.0f} BCF")
            
            with col2:
                color = "normal"
                if latest['percentile'] > 80:
                    color = "inverse"
                elif latest['percentile'] < 20:
                    color = "off"
                st.metric("Storage Percentile", f"{latest['percentile']:.0f}%")
            
            with col3:
                deviation = latest['current_storage'] - latest['historical_mean']
                st.metric("vs. 5Y Average", f"{deviation:+.0f} BCF")
            
            with col4:
                # Days of supply at current withdrawal rate (simplified)
                days_supply = latest['current_storage'] / 3.5  # Assume 3.5 BCF/d avg withdrawal
                st.metric("Days of Supply", f"{days_supply:.0f} days")
            
            # Storage visualization
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Storage vs Historical Range', 'Storage Percentile Trend', 
                               'Regional Storage Distribution', 'Z-Score Analysis'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Main storage chart
            fig.add_trace(
                go.Scatter(x=percentile_df['period'], y=percentile_df['historical_max'],
                          fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=percentile_df['period'], y=percentile_df['historical_min'],
                          fill='tonexty', mode='lines', line_color='rgba(0,0,0,0)',
                          name='5Y Range', fillcolor='rgba(128,128,128,0.2)'),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=percentile_df['period'], y=percentile_df['historical_mean'],
                          mode='lines', name='5Y Average', line=dict(color='blue', dash='dash')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=percentile_df['period'], y=percentile_df['current_storage'],
                          mode='lines', name='Current', line=dict(color='red', width=3)),
                row=1, col=1
            )
            
            # Percentile trend
            fig.add_trace(
                go.Scatter(x=percentile_df['period'], y=percentile_df['percentile'],
                          mode='lines+markers', name='Percentile', line=dict(color='green')),
                row=1, col=2
            )
            fig.add_hline(y=80, line_dash="dash", line_color="red", row=1, col=2)
            fig.add_hline(y=20, line_dash="dash", line_color="red", row=1, col=2)
            
            # Regional storage (if available)
            regional_data = []
            regions = ['storage_east', 'storage_midwest', 'storage_mountain', 'storage_pacific', 'storage_southcentral']
            region_names = ['East', 'Midwest', 'Mountain', 'Pacific', 'South Central']
            
            for region, name in zip(regions, region_names):
                if region in storage_data and not storage_data[region].empty:
                    latest_regional = storage_data[region].iloc[-1]['value']
                    regional_data.append({'region': name, 'storage': latest_regional})
            
            if regional_data:
                regional_df = pd.DataFrame(regional_data)
                fig.add_trace(
                    go.Bar(x=regional_df['region'], y=regional_df['storage'],
                          name='Regional Storage', marker_color='lightblue'),
                    row=2, col=1
                )
            
            # Z-score analysis
            fig.add_trace(
                go.Scatter(x=percentile_df['period'], y=percentile_df['z_score'],
                          mode='lines+markers', name='Z-Score', line=dict(color='purple')),
                row=2, col=2
            )
            fig.add_hline(y=2, line_dash="dash", line_color="red", row=2, col=2)
            fig.add_hline(y=-2, line_dash="dash", line_color="red", row=2, col=2)
            
            fig.update_layout(height=800, title_text="Storage Analytics Dashboard")
            st.plotly_chart(fig, use_container_width=True)
            
            # Storage alerts
            anomalies = analytics.detect_storage_anomalies(percentile_df)
            
            if any(anomalies.values()):
                st.subheader("⚠️ Storage Alerts")
                
                for alert_type, alerts in anomalies.items():
                    for alert in alerts:
                        if alert_type == 'high_storage':
                            st.warning(f"🔴 {alert['message']}")
                        elif alert_type == 'low_storage':
                            st.error(f"🟡 {alert['message']}")
                        else:
                            st.info(f"📊 {alert['message']}")
            else:
                st.success("✅ No storage anomalies detected")

def main():
    st.set_page_config(
        page_title="Natural Gas Analytics Dashboard",
        page_icon="⛽",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize scheduler
    scheduler = get_data_scheduler()
    
    st.title("⛽ Natural Gas Analytics Dashboard")
    st.markdown("*Real-time analytics for natural gas trading opportunities*")
    
    # Sidebar
    st.sidebar.title("📊 Dashboard Navigation")
    
    # Data freshness indicator
    st.sidebar.subheader("📡 Data Status")
    
    data_status = {
        'LNG Data': scheduler.last_update.get('lng_data'),
        'Storage Data': scheduler.last_update.get('storage_data'),
        'News Data': scheduler.last_update.get('news_data')
    }
    
    for data_type, last_update in data_status.items():
        if last_update:
            time_diff = datetime.now() - last_update
            if time_diff.total_seconds() < 3600:  # Less than 1 hour
                st.sidebar.success(f"✅ {data_type}: Fresh ({time_diff.seconds//60}m ago)")
            else:
                st.sidebar.warning(f"⚠️ {data_type}: Stale ({time_diff.seconds//3600}h ago)")
        else:
            st.sidebar.error(f"❌ {data_type}: No data")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Select Analysis",
        ["All Dashboards", "U.S. LNG Export Analytics", "U.S. LNG Storage Analytics", "Market News"]
    )
    
    # API configuration
    with st.sidebar.expander("⚙️ Configuration"):
        st.info("API keys configured via environment variables")
        st.json({
            "EIA_API_KEY": "✅ Configured" if Config.EIA_API_KEY else "❌ Missing",
            "NEWSAPI_KEY": "✅ Configured" if Config.NEWSAPI_KEY else "❌ Missing"
        })
    
    # Display selected dashboard
    if page == "U.S. LNG Export Analytics":
        create_enhanced_lng_dashboard(scheduler)
    elif page == "U.S. LNG Storage Analytics":
        create_enhanced_storage_dashboard(scheduler)
    elif page == "Market News":
        create_news_dashboard(scheduler)
    else:  # All Dashboards
        create_enhanced_lng_dashboard(scheduler)
        st.divider()
        create_enhanced_storage_dashboard(scheduler)
        st.divider()
        create_news_dashboard(scheduler)

def create_news_dashboard(scheduler: DataScheduler):
    """Enhanced News Dashboard"""
    st.header("📰 Market News & Analysis")
    
    news_data = scheduler.get_cached_data('news_data')
    if not news_data:
        st.warning("No news data available")
        return
    
    # News sentiment analysis - not using alphavantage for now
    # sentiments = [float(article.get('overall_sentiment_score', 0)) for article in news_data]
    # avg_sentiment = np.mean(sentiments) if sentiments else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Articles", len(news_data))
    # with col2:
    #     sentiment_label = "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral"
    #     st.metric("Avg Sentiment", sentiment_label, f"{avg_sentiment:.3f}")
    with col2:
        recent_articles = [a for a in news_data if 
                  datetime.strptime(a['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc) > 
                  datetime.now(timezone.utc) - timedelta(hours=24)]
        st.metric("Last 24h", len(recent_articles))
    
    # Display articles
    for i, article in enumerate(news_data):
        with st.expander(f"📖 {article['title'][:80]}..."):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Source:** {article['source']['name']}")
                st.write(f"**Published:** {article['publishedAt']}")
                st.write(f"**Summary:** {article['description'][:200]}...")
                
                if 'url' in article:
                    st.write(f"**[Read Full Article]({article['url']})**")
            
            # with col2:
            #     if 'overall_sentiment_score' in article:
            #         sentiment_score = float(article['overall_sentiment_score'])
            #         sentiment_label = article.get('overall_sentiment_label', 'Neutral')
                    
            #         if sentiment_score > 0.1:
            #             st.success(f"📈 {sentiment_label}\n{sentiment_score:.3f}")
            #         elif sentiment_score < -0.1:
            #             st.error(f"📉 {sentiment_label}\n{sentiment_score:.3f}")
            #         else:
            #             st.info(f"➡️ {sentiment_label}\n{sentiment_score:.3f}")

if __name__ == "__main__":
    main()