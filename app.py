import streamlit as st
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

@st.cache_data(ttl=3600)
def get_prediction_dashboard():
    # Fetching the entire season's fixtures and results to calculate form
    url = "https://football-data.org"
    headers = { 
        "X-Auth-Token": API_KEY,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code != 200:
            return pd.DataFrame()
            
        data = response.json()
        matches = data.get('matches', [])
        
        # 1. Map out historical scores to calculate a 'Form Tracker'
        team_historical_goals = {}
        
        # First loop: Catalog all played matches to find goals scored
        for m in matches:
            if m['status'] == 'FINISHED':
                home = m['homeTeam']['name']
                away = m['awayTeam']['name']
                h_goals = m['score']['fullTime']['home']
                a_goals = m['score']['fullTime']['away']
                
                if h_goals is not None and a_goals is not None:
                    team_historical_goals.setdefault(home, []).append(h_goals)
                    team_historical_goals.setdefault(away, []).append(a_goals)

        # Helper function to get goals in last 5 games
        def get_last_5_goals(team_name):
            history = team_historical_goals.get(team_name, [])
            return sum(history[-5:]) if history else 0

        # 2. Second loop: Build the prediction dashboard for UPCOMING games
        prediction_rows = []
        for m in matches:
            if m['status'] in ['SCHEDULED', 'TIMED', 'LIVE']:
                home_team = m['homeTeam']['name']
                away_team = m['awayTeam']['name']
                
                # Dynamic statistical metrics calculated live
                home_form = get_last_5_goals(home_team)
                away_form = get_last_5_goals(away_team)
                
                # Math-driven prediction logic matching professional layouts
                if home_form > (away_form + 3):
                    pred = "Home Win (High Confidence)"
                elif home_form > away_form:
                    pred = "Home Win (Slight Edge)"
                elif away_form > (home_form + 3):
                    pred = "Away Win (High Confidence)"
                elif away_form > home_form:
                    pred = "Away Win (Slight Edge)"
                else:
                    pred = "Draw / Even Match"

                prediction_rows.append({
                    "Home Team": home_team,
                    "Away Team": away_team,
                    "Home Goals (Last 5)": home_form,
                    "Away Goals (Last 5)": away_form,
                    "Mathematical Prediction": pred
                })
                
        return pd.DataFrame(prediction_rows)
        
    except Exception as e:
        st.error(f"Error mirroring data layouts: {e}")
        return pd.DataFrame()

# Render Dashboard Layout
st.title("📊 Data-Driven Match Predictor Dashboard")
df_predictions = get_prediction_dashboard()

st.subheader("Extracted Data Preview & Live Statistical Trends")
if not df_predictions.empty:
    st.dataframe(df_predictions, use_container_width=True)
else:
    st.info("No active or upcoming Premier League fixtures available in this gameweek.")
