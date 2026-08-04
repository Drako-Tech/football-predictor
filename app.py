import streamlit as st
import pandas as pd
import requests

# Note: Keep your API tokens private in production using st.secrets!
API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

# 1. Complete Master League Mapping Matrix including Elite European Tournaments
LEAGUE_MAP = {
    "🏆 UEFA Champions League": 2,
    "🇪🇺 UEFA Europa League": 5,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 8,
    "🇪🇸 La Liga": 501,
    "🇩🇪 Bundesliga": 82,
    "🇮🇹 Serie A": 384,
    "🇫🇷 Ligue 1": 301,
    "🇩🇰 Danish Superliga (FREE Sandbox Test)": 271,
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premiership (FREE Sandbox Test)": 501
}

# --- REUSABLE ADAPTIVE MULTI-SEGMENT PROGRESS BAR ---
def render_dynamic_market_bar(market_title, outcomes_dict):
    """
    Dynamically maps out 1, 2, or 3-segment color progress sliders depending 
    on the structural nature of the betting market (e.g., 1X2 vs Over/Under vs Home/Away).
    """
    with st.container(border=True):
        st.markdown(f"<h5 style='font-weight: bold; margin-bottom: 2px;'>🎯 {market_title}</h5>", unsafe_allow_html=True)
        
        # Sort or identify contents dynamically
        items = list(outcomes_dict.items())
        count = len(items)
        
        if count == 0:
            st.caption("No outcome probability tracking variables available.")
            return

        # Assign unique styling identifiers for the container panels
        colors = ["#FF2E63", "#CCD1D9", "#081430", "#4A90E2", "#50E3C2"]
        
        # Generate relative width column layout blocks based on probability weights
        widths = [max(float(val), 1.0) for label, val in items]
        cols = st.columns(widths, gap="small")
        
        for idx, col in enumerate(cols):
            label, val = items[idx]
            color = colors[idx % len(colors)]
            
            # Formulate asymmetric corner border radius tags based on layout block array placement
            b_radius = "4px 0px 0px 4px" if idx == 0 else ("0px 4px 4px 0px" if idx == count-1 else "0px")
            if count == 1: b_radius = "4px"
            
            with col:
                st.markdown(f"<div style='background-color: {color}; height: 12px; border-radius: {b_radius};'></div>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-size: 11px; margin-top: 2px; font-weight:600;'>{label.upper()}<br><span style='font-size:13px; font-weight:700;'>{val:.2f}%</span></p>", unsafe_allow_html=True)


# --- DATA PIPELINE INGESTION NODE ---
@st.cache_data(ttl=3600)
def get_master_football_payload(league_id):
    """
    Fetches scheduled upcoming fixtures with comprehensive analytics layers
    including predictions, advanced stats, standings context, and xG data streams.
    """
    url = "https://sportmonks.com"
    
    params = {
        "api_token": API_KEY,
        "include": "predictions.market;participants;league;venue;xgfixture;standings;statistics",
        "filters": f"leagueIds:{league_id};fixtureStatuses:SCHEDULED" 
    }
    
    try:
        response = requests.get(url, params=params, timeout=12)
        if response.status_code == 401:
            st.error("🔑 **Invalid API Token!** The current key is unauthorized. Swap the token inside your local script.")
            return []
        if response.status_code != 200:
            return []
        return response.json().get('data', [])
    except Exception as e:
        st.error(f"Network Connection Exception: {e}")
        return []


# --- APP INTERFACE RENDER ENGINE ---
st.set_page_config(page_title="Ultimate Football Predictor Pro", layout="wide")
st.title("⚽ Ultimate Football Predictor & Market Analytics Hub")
st.caption("Flawless Real-Time Multi-Market Intelligence Engine Powered by Sportmonks")

# Elegant Sidebar Configuration Framework
st.sidebar.header("🏆 League Selection Hub")
selected_league_name = st.sidebar.selectbox("Choose Competition:", options=list(LEAGUE_MAP.keys()))
target_id = LEAGUE_MAP[selected_league_name]

# Global Loading Action Call
fixtures_list = get_master_football_payload(target_id)

if fixtures_list:
    st.subheader(f"Upcoming Match Schedules: {selected_league_name}")
    
    for f in fixtures_list:
        # 1. Process and Align Team Profiles & Logos
        participants = f.get('participants', [])
        home_name, away_name = "Home Team", "Away Team"
        home_logo, away_logo = "", ""
        
        for p in participants:
            if p.get('meta', {}).get('location') == 'home':
                home_name = p.get('name')
                home_logo = p.get('image_path', '')
            else:
                away_name = p.get('name')
                away_logo = p.get('image_path', '')
                
        # 2. Extract Pre-Match Expected Goals (xG Data Feed)
        xg_data = f.get('xgfixture', [])
        home_xg, away_xg = 0.0, 0.0
        for xg_node in xg_data:
            if xg_node.get('location') == 'home':
                home_xg = xg_node.get('data', {}).get('value', 0.0)
            elif xg_node.get('location') == 'away':
                away_xg = xg_node.get('data', {}).get('value', 0.0)

        # MAIN FIXTURE DISPLAY WRAPPER CONTAINER
        with st.container(border=True):
            hdr_col1, hdr_col2, hdr_col3 = st.columns([2, 3, 2])
            with hdr_col1:
                st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                if home_logo: st.image(home_logo, width=55)
                st.subheader(home_name)
                st.markdown("</div>", unsafe_allow_html=True)
            with hdr_col2:
                st.markdown("<p style='text-align: center; font-size: 22px; font-weight: 800; color:#FF2E63; margin-top:15px;'>VS</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-weight:600; color: #7F8C8D;'>🏟️ {f.get('venue', {}).get('name', 'Unknown Venue')}</p>", unsafe_allow_html=True)
            with hdr_col3:
                st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
                if away_logo: st.image(away_logo, width=55)
                st.subheader(away_name)
                st.markdown("</div>", unsafe_allow_html=True)
                
            st.divider()
            
            # --- TABBED LAYOUT DASHBOARD NAVIGATION VIEWS ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🔮 All Market Predictions", 
                "📈 Expected Goals (xG)", 
                "📊 Performance Statistics", 
                "🏆 Standings Table",
                "⏱️ Match Metadata"
            ])
            
            # TAB 1: ALL PLAN MARKETS PRODUCER PANEL
            with tab1:
                predictions_list = f.get('predictions', [])
                if predictions_list:
                    st.markdown("#### Dynamic Mathematical Model Market Projections")
                    for pred in predictions_list:
                        # Fetch human-readable market strings directly from nested meta includes
                        market_meta = pred.get('market', {})
                        market_name = market_meta.get('name', f"Market Type Code {pred.get('type_id')}")
                        
                        # Extract the inner percentage allocation mappings
                        outcomes_probability_map = pred.get('predictions', {})
                        
                        # Pass cleanly to our custom multi-size progress row engine
                        render_dynamic_market_bar(market_name, outcomes_probability_map)
                else:
                    st.info("No prediction market odds profiles have registered for this fixture selection yet.")
                    
            # TAB 2: EXPECTED GOALS INSIGHTS (xG)
            with tab2:
                st.markdown("#### Offensive Efficiency Projections")
                metric_col1, metric_col2 = st.columns(2)
                metric_col1.metric(label=f"{home_name} Expected xG Value", value=f"{home_xg:.2f}")
                metric_col2.metric(label=f"{away_name} Expected xG Value", value=f"{away_xg:.2f}")
                st.caption("xG values measure the statistical high-quality threat of shot opportunities generated by each team profile.")

            # TAB 3: TEAM PERFORMANCE STATS
            with tab3:
                st.markdown("#### Aggregate Head-to-Head Structural Season Metrics")
                stats_list = f.get('statistics', [])
                if stats_list:
                    stat_rows = []
                    for stat in stats_list:
                        stat_rows.append({
                            "Tracking Category": stat.get('type', {}).get('name', 'General Metric'),
                            "Location Scope": stat.get('location', 'Global'),
                            "Recorded Value": stat.get('data', {}).get('value', 0)
                        })
                    st.dataframe(pd.DataFrame(stat_rows), use_container_width=True, hide_index=True)
                else:
                    st.info("Tactical data matrix details will refresh closer to live match execution.")

            # TAB 4: LEAGUE STANDINGS 
            with tab4:
                st.markdown("#### Group / Competition Ranking Matrix")
                standings_raw = f.get('standings', [])
                if standings_raw:
                    st.dataframe(pd.DataFrame(standings_raw), use_container_width=True, hide_index=True)
                else:
                    st.info("League standing contextual tables are updating in the background.")

            # TAB 5: MATCH TIMESTAMPS
            with tab5:
                st.markdown("#### Scheduling Timeline Details")
                meta_col1, meta_col2 = st.columns(2)
                meta_col1.markdown(f"**Kick-off Window (UTC):** `{f.get('starting_at', 'To Be Decided')}`")
