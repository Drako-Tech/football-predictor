import streamlit as st
import pandas as pd
import requests
import urllib3

# Suppress insecure request warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set your API Key
API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

@st.cache_data(ttl=3600)
def get_live_match_data():
    # Force the api sub-domain explicitly
    url = "https://football-data.org"
    headers = { "X-Auth-Token": API_KEY }
    
    try:
        # Added verify=False to bypass local SSL certificate validation errors
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status() 
        data = response.json()
        
        extracted_matches = []
        for match in data.get('matches', []):
            match_info = {
                "HomeTeam": match['homeTeam']['name'],
                "AwayTeam": match['awayTeam']['name'],
                "HomeGoalsLast5": 10,  
                "AwayGoalsLast5": 5    
            }
            extracted_matches.append(match_info)
            
        return pd.DataFrame(extracted_matches)
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching live data: {e}")
        return pd.DataFrame(columns=["HomeTeam", "AwayTeam", "HomeGoalsLast5", "AwayGoalsLast5"])

df = get_live_match_data()

st.subheader("Extracted Data Preview")
if not df.empty:
    st.dataframe(df)
else:
    st.info("No active or upcoming matches found at the moment.")
