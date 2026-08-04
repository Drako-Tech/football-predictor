# --- Automated Live Market Odds Fetcher ---
def fetch_live_market_odds(api_key, league_odds_code):
    if not api_key or "MOCK" in league_odds_code:
        return {}
    try:
        # FIXED: Added the required /v4/sports/ path segment
        url = f"https://the-odds-api.com{league_odds_code}/odds/?apiKey={api_key}&regions=uk&markets=h2h&oddsFormat=decimal"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Check for HTTP errors
        
        data = response.json()
        odds_dict = {}
        for match in data:
            home = match.get('home_team')
            # ... rest of your logic parsing out bookmakers ...
            
        return odds_dict
    except Exception as e:
        # Good practice to log the error to console when debugging local fallback issues
        print(f"API Fetch Error: {e}") 
        return {}
