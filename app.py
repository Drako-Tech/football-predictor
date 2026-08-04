import streamlit as st
import pandas as pd
import requests

# Set your API Key
API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

# Caches data for 1 hour (3600 seconds) so your app doesn't burn through API limits
@st.cache_data(ttl=3600)
def get_live_match_data():
    # FIXED: Changed URL to api.football-data.org
    url = "https://football-data.org"
    headers = { "X-Auth-Token": API_KEY }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raises an error for bad response codes
        data = response.json()
        
        extracted_matches = []
        for match in data.get('matches', []):
            match_info = {
                "HomeTeam": match['homeTeam']['name'],
                "AwayTeam": match['awayTeam']['name'],
                "HomeGoalsLast5": 10,  # Placeholder: Replace with your calculation logic
                "AwayGoalsLast5": 5    # Placeholder: Replace with your calculation logic
            }
            extracted_matches.append(match_info)
            
        return pd.DataFrame(extracted_matches)
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching live data: {e}")
        # Returns an empty DataFrame with your expected columns as a fallback
        return pd.DataFrame(columns=["HomeTeam", "AwayTeam", "HomeGoalsLast5", "AwayGoalsLast5"])

# Replace your st.file_uploader logic with this automated call
df = get_live_match_data()

# Display your preview section exactly like your original screenshot
st.subheader("Extracted Data Preview")
if not df.empty:
    st.dataframe(df)
else:
    st.info("No active or upcoming matches found at the moment.")
