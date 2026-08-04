import streamlit as st
import pandas as pd
import requests
import urllib3
from datetime import datetime

# Suppress insecure request warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Page Layout Configurations
st.set_page_config(page_title="European Football Match Predictor", page_icon="⚽", layout="wide")

# API Configuration
API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

# Expanded Competitions mapping for every major league across Europe
COMPETITIONS = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 English Premier League": "PL",
    "🇪🇸 Spanish La Liga": "PD",
    "🇩🇪 German Bundesliga": "BL1",
    "🇮🇹 Italian Serie A": "SA",
    "🇫🇷 French Ligue 1": "FL1",
    "🇳🇱 Dutch Eredivisie": "DED",
    "🇵🇹 Portuguese Primeira Liga": "PPL",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 English Championship": "ELC",
    "🇪🇺 UEFA Champions League": "CL",
    "🇪🇺 UEFA Europa League": "ELI",
    "🇪🇺 UEFA European Championship": "EC"
}

@st.cache_data(ttl=1800) # Reduced cache to 30 mins for live updates
def get_prediction_dashboard(competition_code):
    # Base endpoint targeting the selected European competition matches
    url = f"https://football-data.org{competition_code}/matches"
    headers = { 
        "X-Auth-Token": API_KEY,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        
        if response.status_code == 403:
            st.error("🔑 API Tier Restriction: This competition might require a paid football-data.org plan.")
            return pd.DataFrame()
        elif response.status_code != 200:
            st.error(f"❌ API Connection Error: Received status code {response.status_code}")
            return pd.DataFrame()
            
        data = response.json()
        matches = data.get('matches', [])
        
        if not matches:
            return pd.DataFrame()
        
        # 1. Map out historical scores across the competition to find form trends
        team_historical_goals = {}
        
        # Parse through finished fixtures to log goal statistics
        for m in matches:
            if m.get('status') == 'FINISHED':
                home = m['homeTeam']['name']
                away = m['awayTeam']['name']
                
                score_data = m.get('score', {}).get('fullTime', {})
                h_goals = score_data.get('home')
                a_goals = score_data.get('away')
                
                if h_goals is not None and a_goals is not None:
                    team_historical_goals.setdefault(home, []).append(h_goals)
                    team_historical_goals.setdefault(away, []).append(a_goals)

        # Helper function tracking average and sum metrics over last 5 iterations
        def get_last_5_goals(team_name):
            history = team_historical_goals.get(team_name, [])
            return sum(history[-5:]) if history else 0

        # 2. Compile metrics and generate predictive values for incomplete schedules
        prediction_rows = []
        for m in matches:
            status = m.get('status', '')
            # Capturing all variations of live or upcoming schedules
            if status in ['SCHEDULED', 'TIMED', 'LIVE', 'IN_PLAY', 'PAUSED']:
                home_team = m['homeTeam']['name']
                away_team = m['awayTeam']['name']
                
                # Format Match Dates elegantly
                utc_date_str = m.get('utcDate', '')
                try:
                    date_obj = datetime.strptime(utc_date_str, "%Y-%m-%dT%H:%M:%SZ")
                    formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    formatted_date = utc_date_str
                
                home_form = get_last_5_goals(home_team)
                away_form = get_last_5_goals(away_team)
                
                # 3. Dynamic Calculation Algorithm
                total_goals = home_form + away_form
                goal_diff = abs(home_form - away_form)
                
                if total_goals > 0:
                    confidence = min(50 + int((goal_diff / total_goals) * 50), 95)
                else:
                    confidence = 50 
                
                if home_form > away_form:
                    pred_outcome = "Home Win"
                    edge = f"🔵 {home_team} Form Edge"
                elif away_form > home_form:
                    pred_outcome = "Away Win"
                    edge = f"🟢 {away_team} Form Edge"
                else:
                    pred_outcome = "Draw"
                    edge = "⚪ Form Evenly Matched"
                    confidence = 50

                prediction_rows.append({
                    "Match Date": formatted_date,
                    "Home Team": home_team,
                    "Away Team": away_team,
                    "Home Goals (Last 5)": home_form,
                    "Away Goals (Last 5)": away_form,
                    "Form Advantage": edge,
                    "Predicted Outcome": pred_outcome,
                    "Confidence Rating": f"{confidence}%",
                    "Status": "LIVE" if status in ['LIVE', 'IN_PLAY', 'PAUSED'] else "SCHEDULED"
                })
                
        return pd.DataFrame(prediction_rows)
        
    except Exception as e:
        st.error(f"⚠️ Exception occurred during runtime handling: {e}")
        return pd.DataFrame()

# ==========================================
# STREAMLIT USER INTERFACE LAYOUT
# ==========================================

st.title("🇪🇺 Pan-European Football Match Predictor")
st.markdown("Select your target European competition in the sidebar to review live fixtures and mathematical outcome trends.")

# Sidebar Filters
st.sidebar.header("🌍 League & Filter Panels")

# Dropdown showcasing the newly added European leagues
selected_league_label = st.sidebar.selectbox("Choose Competition League:", list(COMPETITIONS.keys()))
selected_league_code = COMPETITIONS[selected_league_label]

with st.spinner(f"Aggregating database matrix profiles..."):
    df_predictions = get_prediction_dashboard(selected_league_code)

if not df_predictions.empty:
    st.sidebar.subheader("Fine-tune Selection Filters")
    
    # Status Toggles
    status_filter = st.sidebar.multiselect(
        "Match Schedule Window:", 
        options=df_predictions["Status"].unique(), 
        default=df_predictions["Status"].unique()
    )
    
    # Name Search Engine Filters
    team_search = st.sidebar.text_input("🔍 Filter by target team string name:").strip()
    
    # Processing filters live
    filtered_df = df_predictions[df_predictions["Status"].isin(status_filter)]
    if team_search:
        filtered_df = filtered_df[
            filtered_df["Home Team"].str.contains(team_search, case=False) | 
            filtered_df["Away Team"].str.contains(team_search, case=False)
        ]

    # Render Visual Performance Layout Panels
    st.subheader(f"🔮 Predictions for {selected_league_label}")
    
    c1, c2 = st.columns(2)
    c1.metric("Matches Listed in View", len(filtered_df))
    c2.metric("Active Ongoing Games", len(filtered_df[filtered_df["Status"] == "LIVE"]))

    if not filtered_df.empty:
        display_cols = [
            "Match Date", "Home Team", "Away Team", 
            "Home Goals (Last 5)", "Away Goals (Last 5)", 
            "Form Advantage", "Predicted Outcome", "Confidence Rating"
        ]
        
        st.dataframe(
            filtered_df[display_cols].set_index("Match Date"), 
            use_container_width=True
        )
    else:
        st.warning("No matches fit your exact sidebar filter choices.")
else:
    st.info("No live or upcoming fixtures available in this gameweek slate.")
