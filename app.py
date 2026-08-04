import streamlit as st
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

def get_live_match_data():
    url = "https://football-data.org"
    
    headers = { 
        "X-Auth-Token": API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        
        # DIAGNOSTIC SCREEN: Force show whatever your system is actually reading
        st.info("🛠️ Network Diagnostic Mode Active")
        st.text(f"HTTP Status Received: {response.status_code}")
        st.text("First 500 characters of server response:")
        st.code(response.text[:500]) # This outputs the hidden text blocking you
        
        # Attempt standard execution block
        if response.status_code == 200:
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
            
        return pd.DataFrame(columns=["HomeTeam", "AwayTeam", "HomeGoalsLast5", "AwayGoalsLast5"])
        
    except Exception as e:
        st.error(f"Network Connection Issue: {e}")
        return pd.DataFrame(columns=["HomeTeam", "AwayTeam", "HomeGoalsLast5", "AwayGoalsLast5"])

df = get_live_match_data()
st.subheader("Extracted Data Preview")
