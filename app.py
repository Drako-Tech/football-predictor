import streamlit as st
import pandas as pd
import requests

# Note: Keep your API tokens private in production using st.secrets!
API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

LEAGUE_MAP = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 8,
    "🇪🇸 La Liga": 501,
    "🇩🇪 Bundesliga": 82,
    "🇮🇹 Serie A": 384,
    "🇫🇷 Ligue 1": 301
}

# --- REUSABLE PROGRESS BAR LAYOUT ENGINE ---
def render_prediction_bar(card_title, description, home_val, draw_val, away_val):
    """
    Renders an encapsulated dashboard card with exact matching header string titles,
    informational description tags, and proportional multi-colored ratio progress tracking bars.
    """
    with st.container(border=True):
        st.markdown(f"<h4 style='text-align: center; font-weight: bold;'>{card_title}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #4A4A4A; font-size: 14px; margin-bottom: 20px;'>{description}</p>", unsafe_allow_html=True)
        
        # Guard calculation sizes against total math zeros
        w_home = max(home_val, 1.0)
        w_draw = max(draw_val, 1.0)
        w_away = max(away_val, 1.0)
        
        # Build the exact multi-colored segmented horizontal loading line track
        bar_col1, bar_col2, bar_col3 = st.columns([w_home, w_draw, w_away], gap="small")
        
        with bar_col1:
            st.markdown("<div style='background-color: #FF2E63; height: 14px; border-radius: 4px 0px 0px 4px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-weight: 700; font-size: 13px; margin-top: 4px;'>{home_val:.2f}%</p>", unsafe_allow_html=True)
            
        with bar_col2:
            st.markdown("<div style='background-color: #CCD1D9; height: 14px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-weight: 700; font-size: 13px; margin-top: 4px;'>{draw_val:.2f}%</p>", unsafe_allow_html=True)
            
        with bar_col3:
            st.markdown("<div style='background-color: #081430; height: 14px; border-radius: 0px 4px 4px 0px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-weight: 700; font-size: 13px; margin-top: 4px;'>{away_val:.2f}%</p>", unsafe_allow_html=True)


# --- DATA FETCHING ENGINE (ALL COMPONENT INCLUDES INTEGRATED) ---
@st.cache_data(ttl=3600)
def get_master_football_payload(league_id):
    """
    Fetches scheduled upcoming fixtures with comprehensive analytics nodes
    including predictions, advanced stats, standings context, and xG feeds.
    """
    url = "https://api.sportmonks.com/v3/football/fixtures"
    
    # Combined includes string pulling every chosen Sportmonks category feature node
    params = {
        "api_token": API_KEY,
        "include": "predictions;participants;league;venue;xgfixture;standings;statistics",
        "filters": f"leagueIds:{league_id};fixtureStatuses:SCHEDULED" 
    }
    
    try:
        response = requests.get(url, params=params, timeout=12)
        if response.status_code != 200:
            return []
        return response.json().get('data', [])
    except Exception:
        return []


# --- APP RENDER INTERFACE ---
st.set_page_config(page_title="Pro Football Predictor Hub", layout="wide")
st.title("📊 Data-Driven Match Predictor Dashboard")
st.caption("Comprehensive Live Analytical Dashboard Powered by Sportmonks")

# League Selector Panel
selected_league = st.selectbox("Choose a competition to scan:", options=list(LEAGUE_MAP.keys()))
fixtures_list = get_master_football_payload(LEAGUE_MAP[selected_league])

if fixtures_list:
    st.subheader(f"Upcoming Analytical Breakdown: {selected_league}")
    
    for f in fixtures_list:
        # 1. Parse Participants & Profiles
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
        
        # 2. Extract Prediction Markets Map Matrix
        markets = {
            237: {"home": 0.0, "draw": 0.0, "away": 0.0},  # Fulltime Result
            231: {"home": 0.0, "draw": 0.0, "away": 0.0},  # Team to Score First
            232: {"home": 0.0, "draw": 0.0, "away": 0.0}   # First Half Winner
        }
        for pred in f.get('predictions', []):
            tid = pred.get('type_id')
            if tid in markets:
                p_data = pred.get('predictions', {})
                markets[tid]["home"] = p_data.get('home', 0.0)
                markets[tid]["draw"] = p_data.get('draw', 0.0) or p_data.get('none', 0.0)
                markets[tid]["away"] = p_data.get('away', 0.0)
                
        # 3. Extract Expected Goals Data Points (xG Component)
        xg_data = f.get('xgfixture', [])
        home_xg, away_xg = 0.0, 0.0
        for xg_node in xg_data:
            if xg_node.get('location') == 'home':
                home_xg = xg_node.get('data', {}).get('value', 0.0)
            elif xg_node.get('location') == 'away':
                away_xg = xg_node.get('data', {}).get('value', 0.0)

        # RENDER MATCH PANEL MODULE CONTAINER
        with st.container(border=True):
            hdr_col1, hdr_col2, hdr_col3 = st.columns([2, 3, 2])
            with hdr_col1:
                if home_logo: st.image(home_logo, width=45)
                st.subheader(home_name)
            with hdr_col2:
                st.markdown("<p style='text-align: center; font-size: 18px; font-weight: bold; margin-top:10px;'>VS</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: #7F8C8D;'>🏟️ {f.get('venue', {}).get('name', 'Unknown Stadium')}</p>", unsafe_allow_html=True)
            with hdr_col3:
                if away_logo: st.image(away_logo, width=45)
                st.subheader(away_name)
                
            st.divider()
            
            # --- NESTED SYSTEM COMPONENTS VIEW TABS ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🔮 Outcome Predictions", 
                "📈 Expected Goals (xG)", 
                "📊 Team Statistics", 
                "🏆 Standings Context",
                "⏱️ Match Metadata"
            ])
            
            # Tab 1: Proportional Slider Visualizations
            with tab1:
                render_prediction_bar(
                    "Fulltime Result Probability",
                    "The probability of each possible match outcome (home win, draw, away win) at the end of full-time.",
                    markets[237]["home"], markets[237]["draw"], markets[237]["away"]
                )
                render_prediction_bar(
                    "Team To Score First Probability",
                    "The probability of which team will score the first goal in the match.",
                    markets[231]["home"], markets[231]["draw"], markets[231]["away"]
                )
                render_prediction_bar(
                    "First Half Winner Probability",
                    "The probability that a specific team will be leading at the end of the first half.",
                    markets[232]["home"], markets[232]["draw"], markets[232]["away"]
                )
                
            # Tab 2: Expected Goals Insights (xG)
            with tab2:
                st.markdown("#### Pre-Match Expected Offensive Efficiency")
                metric_col1, metric_col2 = st.columns(2)
                metric_col1.metric(label=f"{home_name} Projected xG", value=f"{home_xg:.2f}")
                metric_col2.metric(label=f"{away_name} Projected xG", value=f"{away_xg:.2f}")
                st.caption("Expected Goals (xG) quantifies the cumulative statistical probability of finishing generated scoring chances.")

            # Tab 3: Detailed Match/Season Statistics Component
            with tab3:
                st.markdown("#### Core Head-to-Head & Season Tracking Metrics")
                stats_list = f.get('statistics', [])
                if stats_list:
                    # Construct clean comparative DataFrames
                    stat_rows = []
                    for stat in stats_list:
                        stat_rows.append({
                            "Metric Type": stat.get('type', {}).get('name', 'General Metric'),
                            "Location": stat.get('location', 'Unknown'),
                            "Value": stat.get('data', {}).get('value', 0)
                        })
                    st.dataframe(pd.DataFrame(stat_rows), use_container_width=True)
                else:
                    st.info("Detailed tactical tracking matrix will synchronize closer to kick-off.")

            # Tab 4: Standings Context Component
            with tab4:
                st.markdown("#### Current Competition Ranking Context")
                standings_raw = f.get('standings', [])
                if standings_raw:
                    st.dataframe(pd.DataFrame(standings_raw), use_container_width=True)
                else:
                    st.info("League standing records table details are currently loading or adjusting.")

            # Tab 5: Match Metadata (Schedules & Venues)
            with tab5:
                st.markdown("#### Fixture Schedule & Venue Breakdown")
                meta_col1, meta_col2 = st.columns(2)
                meta_col1.markdown(f"**Kick-off Time (UTC):** `{f.get('starting_at', 'TBD')}`")
                meta_col2.markdown(f"**Fixture Status:** `{f.get('state', {}).get('name', 'Scheduled')}`")
