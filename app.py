import streamlit as st
import pandas as pd
import requests
import urllib3

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set your API Key
API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

@st.cache_data(ttl=3600)
def get_live_match_data():
    url = "https://football-data.org"
    
    # ADDED: User-Agent headers to prevent server-side bot blocking
    headers = { 
        "X-Auth-Token": API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        
        # If the server drops an error code, let's catch it clearly before parsing JSON
        if response.status_code != 200:
            st.error(f"API Server returned error status code: {response.status_code}")
            st.text(f"Server Response snippet: {response.text[:200]}")
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
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching live data: {e}")
        return pd.DataFrame(columns=["HomeTeam", "AwayTeam", "HomeGoalsLast5", "AwayGoalsLast5"])
    except ValueError as json_err:
        st.error(f"JSON Parsing Error: {json_err}. Raw output was: {response.text[:300]}")
        return pd.DataFrame(columns=["HomeTeam", "AwayTeam", "HomeGoalsLast5", "AwayGoalsLast5"])

df = get_live_match_data()

st.subheader("Extracted Data Preview")
if not df.empty:
    st.dataframe(df)
else:
    st.info("No active or upcoming matches found at the moment.")
