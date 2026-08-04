import streamlit as st
import pandas as pd
import requests
import urllib3

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set your API Key
API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

# REMOVED CACHE LINE FOR TROUBLESHOOTING
def get_live_match_data():
    url = "https://football-data.org"
    
    headers = { 
        "X-Auth-Token": API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    try:
        # Request data forcefully from the live endpoint
        response = requests.get(url, headers=headers, verify=False)
        
        # This will catch specific API message alerts like Tier restrictions or IP bans
        if response.status_code != 200:
            st.error(f"API Server Error. Status Code: {response.status_code}")
            st.warning(f"Raw Text Response from API: {response.text}")
            return pd.DataFrame(columns=["HomeTeam", "AwayTeam", "HomeGoalsLast5", "AwayGoalsLast5"])
            
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
        
    except Exception as e:
        st.error(f"Network Connection Issue: {e}")
        return pd.DataFrame(columns=["HomeTeam", "AwayTeam", "HomeGoalsLast5", "AwayGoalsLast5"])

df = get_live_match_data()

st.subheader("Extracted Data Preview")
if not df.empty:
    st.dataframe(df)
else:
    st.info("No active or upcoming matches found at the moment.")
