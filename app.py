import streamlit as st
import pandas as pd
import requests

# Note: Keep your API tokens private in production using st.secrets!
API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

# 1. Define a structured dictionary mapping user-friendly names to Sportmonks IDs
LEAGUE_MAP = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 8,
    "🇪🇸 La Liga": 501,
    "🇩🇪 Bundesliga": 82,
    "🇮🇹 Serie A": 384,
    "🇫🇷 Ligue 1": 301
}

@st.cache_data(ttl=3600)
def get_sportmonks_predictions(league_id):
    """
    Fetches upcoming fixtures and pre-calculated model predictions filtered
    by a specific league ID in a single data request.
    """
    url = "https://api.sportmonks.com/v3/football/fixtures"
    
    params = {
        "api_token": API_KEY,
        "include": "predictions;participants",
        # Pass the league ID and filter for scheduled upcoming fixtures
        "filters": f"leagueIds:{league_id};fixtureStatuses:SCHEDULED" 
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            st.error(f"Sportmonks API Error: Received status code {response.status_code}")
            return pd.DataFrame()
            
        json_data = response.json()
        fixtures = json_data.get('data', [])
        
        prediction_rows = []
        
        for f in fixtures:
            # Extract team names from the participants list
            participants = f.get('participants', [])
            home_team = "Unknown Home"
            away_team = "Unknown Away"
            
            for p in participants:
                meta = p.get('meta', {})
                if meta.get('location') == 'home':
                    home_team = p.get('name')
                elif meta.get('location') == 'away':
                    away_team = p.get('name')
            
            # Extract 1X2 Full-Time market probabilities (type_id 237)
            predictions_list = f.get('predictions', [])
            home_prob, draw_prob, away_prob = 0.0, 0.0, 0.0
            
            for pred in predictions_list:
                if pred.get('type_id') == 237:
                    developer_predictions = pred.get('predictions', {})
                    home_prob = developer_predictions.get('home', 0.0)
                    draw_prob = developer_predictions.get('draw', 0.0)
                    away_prob = developer_predictions.get('away', 0.0)
                    break
            
            # Formulate the deterministic layout prediction message
            if home_prob > away_prob and home_prob > draw_prob:
                verdict = f"🟢 Home Win ({home_prob:.1f}%)"
            elif away_prob > home_prob and away_prob > draw_prob:
                verdict = f"🔵 Away Win ({away_prob:.1f}%)"
            elif draw_prob > 0.0:
                verdict = f"🟡 Draw ({draw_prob:.1f}%)"
            else:
                verdict = "Data Sync Pending"
                
            prediction_rows.append({
                "Home Team": home_team,
                "Away Team": away_team,
                "Home Win Prob %": home_prob,
                "Draw Prob %": draw_prob,
                "Away Win Prob %": away_prob,
                "Model Verdict": verdict
            })
            
        return pd.DataFrame(prediction_rows)
        
    except Exception as e:
        st.error(f"Failed to fetch data stream: {e}")
        return pd.DataFrame()

# --- Render Streamlit Dashboard Layout ---
st.set_page_config(page_title="Football Predictor Hub", layout="wide")
st.title("📊 Data-Driven Match Predictor Dashboard")
st.caption("Powered by Sportmonks Real-Time Analytics Pipeline")

# 2. Add an elegant selector panel in the UI
st.subheader("Filter Predictions by League")
selected_league_name = st.selectbox(
    "Choose a competition to scan:", 
    options=list(LEAGUE_MAP.keys()), 
    index=0
)

# 3. Dynamic payload fetching based on the chosen key
target_id = LEAGUE_MAP[selected_league_name]
df_predictions = get_sportmonks_predictions(target_id)

st.subheader(f"Extracted Data Preview & Statistical Trends: {selected_league_name}")

if not df_predictions.empty:
    st.dataframe(
        df_predictions, 
        use_container_width=True,
        column_config={
            "Home Win Prob %": st.column_config.ProgressColumn("Home Win Probability", format="%.1f%%", min_value=0, max_value=100),
            "Away Win Prob %": st.column_config.ProgressColumn("Away Win Probability", format="%.1f%%", min_value=0, max_value=100),
            "Draw Prob %": st.column_config.ProgressColumn("Draw Probability", format="%.1f%%", min_value=0, max_value=100),
        }
    )
else:
    st.info(f"No scheduled upcoming matches found for {selected_league_name} in this current window segment.")
