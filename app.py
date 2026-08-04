import math
import numpy as np
import pandas as pd
import streamlit as st
import requests
import io

st.set_page_config(layout="wide", page_title="Global Live Football Analytics Hub")
st.title("⚽ Global Live Multi-League Analytics & Value Hub")

# Global Fixed API Key Pipeline
ODDS_API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

def poisson_prob(lmbda, k):
    if lmbda <= 0: return 0.0
    return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

# --- 10-League Configuration System Mapping Matrix ---
LEAGUES_CONFIG = {
    "Premier League (England)": {"code": "E0", "odds_code": "soccer_epl"},
    "English Championship (England)": {"code": "E1", "odds_code": "soccer_efl_championship"},
    "La Liga (Spain)": {"code": "SP1", "odds_code": "soccer_spain_la_liga"},
    "Serie A (Italy)": {"code": "I1", "odds_code": "soccer_italy_serie_a"},
    "Bundesliga (Germany)": {"code": "D1", "odds_code": "soccer_germany_bundesliga"},
    "Ligue 1 (France)": {"code": "F1", "odds_code": "soccer_france_ligue_one"},
    "Primeira Liga (Portugal)": {"code": "P1", "odds_code": "soccer_portugal_primeira_liga"},
    "Belgian Pro League (Belgium)": {"code": "B1", "odds_code": "soccer_belgium_first_division_a"},
    "Brasileirão (Brazil)": {"code": "MOCK_BR", "odds_code": "soccer_brazil_campeonato"},
    "MLS (USA/Canada)": {"code": "MOCK_MLS", "odds_code": "soccer_usa_mls"}
}

# --- Automated Live Market Odds Fetcher ---
def fetch_live_market_odds(api_key, league_odds_code):
    if not api_key or "MOCK" in league_odds_code:
        return {}
    try:
        url = f"https://the-odds-api.com{league_odds_code}/odds/?apiKey={api_key}&regions=uk&markets=h2h&oddsFormat=decimal"
        response = requests.get(url, timeout=5).json()
        odds_dict = {}
        for match in response:
            home = match.get('home_team')
            away = match.get('away_team')
            bookmakers = match.get('bookmakers', [])
            if bookmakers:
                # Use first active bookmaker parameters
                markets = bookmakers[0].get('markets', [])
                if markets:
                    outcomes = markets[0].get('outcomes', [])
                    h_odds, d_odds, a_odds = 1.85, 3.40, 4.20
                    for outcome in outcomes:
                        if outcome['name'] == home: h_odds = float(outcome['price'])
                        elif outcome['name'] == 'Draw': d_odds = float(outcome['price'])
                        elif outcome['name'] == away: a_odds = float(outcome['price'])
                    odds_dict[f"{home} vs {away}"] = (h_odds, d_odds, a_odds)
        return odds_dict
    except Exception:
        return {}

# --- Dynamic Automated Live League Table Engine ---
def calculate_league_table(df, predict_home=None, predict_away=None, ph_goals=0, pa_goals=0):
    working_df = df.copy()
    if predict_home and predict_away:
        new_row = pd.DataFrame([{
            'HomeTeam': predict_home, 'AwayTeam': predict_away,
            'FTHG': int(ph_goals), 'FTAG': int(pa_goals),
            'FTR': 'H' if ph_goals > pa_goals else ('A' if pa_goals > ph_goals else 'D')
        }])
        working_df = pd.concat([working_df, new_row], ignore_index=True)

    h_group = working_df.groupby('HomeTeam')
    home_stats = pd.DataFrame({
        'Played_Home': h_group['FTHG'].count(),
        'W_h': h_group.apply(lambda x: (x['FTR'] == 'H').sum()),
        'D_h': h_group.apply(lambda x: (x['FTR'] == 'D').sum()),
        'L_h': h_group.apply(lambda x: ((x['FTR'] == 'A') | (x['FTR'] == 'L')).sum()),
        'GF_h': h_group['FTHG'].sum(),
        'GA_h': h_group['FTAG'].sum()
    })

    a_group = working_df.groupby('AwayTeam')
    away_stats = pd.DataFrame({
        'Played_Away': a_group['FTAG'].count(),
        'W_a': a_group.apply(lambda x: (x['FTR'] == 'A').sum()),
        'D_a': a_group.apply(lambda x: (x['FTR'] == 'D').sum()),
        'L_a': a_group.apply(lambda x: ((x['FTR'] == 'H') | (x['FTR'] == 'L')).sum()),
        'GF_a': a_group['FTAG'].sum(),
        'GA_a': a_group['FTHG'].sum()
    })

    table = home_stats.join(away_stats, how='outer').fillna(0).astype(int)
    table['Played'] = table['Played_Home'] + table['Played_Away']
    table['Won'] = table['W_h'] + table['W_a']
    table['Drawn'] = table['D_h'] + table['D_a']
    table['Lost'] = table['L_h'] + table['L_a']
    table['GF'] = table['GF_h'] + table['GF_a']
    table['GA'] = table['GA_h'] + table['GA_a']
    table['GD'] = table['GF'] - table['GA']
    table['Points'] = (table['Won'] * 3) + table['Drawn']
    table.index.name = 'Team'
    table = table.reset_index()

    def extract_form_string(team):
        t_matches = working_df[(working_df['HomeTeam'] == team) | (working_df['AwayTeam'] == team)].tail(5)
        form_list = []
        for _, r in t_matches.iterrows():
            if r['HomeTeam'] == team:
                res = 'W' if r['FTR'] == 'H' else ('D' if r['FTR'] == 'D' else 'L')
            else:
                res = 'W' if r['FTR'] == 'A' else ('D' if r['FTR'] == 'D' else 'L')
            form_list.append(res)
        return " - ".join(form_list)

    table['Form (Last 5)'] = table['Team'].apply(extract_form_string)
    table = table.sort_values(by=['Points', 'GD', 'GF', 'Team'], ascending=[False, False, False, True]).reset_index(drop=True)
    table.index += 1
    return table[['Team', 'Played', 'Won', 'Drawn', 'Lost', 'GF', 'GA', 'GD', 'Points', 'Form (Last 5)']]

# --- Local Standby Backup Sandbox Generator for Americas Leagues ---
def generate_mock_league_data(league_name):
    if "Brazil" in league_name:
        teams = ['Flamego', 'Palmeiras', 'Botafogo', 'Fluminense', 'Gremio', 'Sao Paulo', 'Santos', 'Corinthians']
    else:
        teams = ['LA Galaxy', 'Inter Miami', 'LAFC', 'Columbus Crew', 'NY Red Bulls', 'FC Cincinnati', 'Seattle Sounders', 'Atlanta United']
    data = []
    for i in range(len(teams)):
        for j in range(len(teams)):
            if i != j:
                data.append({'HomeTeam': teams[i], 'AwayTeam': teams[j], 'FTHG': 2, 'FTAG': 1, 'FTR': 'H', 'HS': 12, 'AS': 8, 'HST': 5, 'AST': 3})
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def load_league_data_safely(league_name, config):
    if "MOCK" in config["code"]:
        return generate_mock_league_data(league_name), "Local Automated Simulation Layer"
        
    headers = {"User-Agent": "Mozilla/5.0"}
    # 25/26 season evaluation targets
    url = f"https://football-data.co.uk{config['code']}.csv"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200 and "HomeTeam" in response.text:
            csv_data = io.StringIO(response.text)
            return pd.read_csv(csv_data), f"Live Cloud Stream via Football-Data ({config['code']})"
    except Exception:
        pass
        
    # Archive 24/25 safety loop fallback
    url_fallback = f"https://football-data.co.uk{config['code']}.csv"
    try:
        response = requests.get(url_fallback, headers=headers, timeout=10)
        if response.status_code == 200 and "HomeTeam" in response.text:
            csv_data = io.StringIO(response.text)
            return pd.read_csv(csv_data), f"Archive Cloud Stream via Football-Data ({config['code']})"
    except Exception:
        pass

    # Generic failsafe wrapper array mapping
    teams = ["Team Alpha", "Team Beta", "Team Gamma", "Team Delta"]
    d = []
    for i in range(4):
        for j in range(4):
            if i != j: d.append({'HomeTeam': teams[i], 'AwayTeam': teams[j], 'FTHG': 1, 'FTAG': 1, 'FTR': 'D'})
    return pd.DataFrame(d), "Generic System Failsafe Layer"


# --- DYNAMIC TARGET LEAGUE UI CHOOSER SELECTION ---
selected_league_label = st.selectbox("🌐 Select Target Football Tournament", list(LEAGUES_CONFIG.keys()))
active_config = LEAGUES_CONFIG[selected_league_label]

# --- CONTROLLER PIPELINE ROUTING ---
df = None
try:
    with st.spinner(f"🔄 Establishing secure connection and downloading stats for {selected_league_label}..."):
        df, source_label = load_league_data_safely(selected_league_label, active_config)
        live_odds_book = fetch_live_market_odds(ODDS_API_KEY, active_config["odds_code"])
    st.success(f"🟢 Synchronized: Using {source_label}")
except Exception as e:
    df, source_label = generate_mock_league_data(selected_league_label), "Emergency Failsafe Offline Layer"
    live_odds_book = {}
    st.error(f"Data stream communication break: {e}")

if df is not None and not df.empty:
    teams_list = sorted(df['HomeTeam'].dropna().unique().tolist())
    tab1, tab2 = st.tabs(["🎯 Match Forecast Simulation Engine", "📊 Live Standings & Form Matrix Dashboard"])
    
    with tab1:
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            selected_home = st.selectbox("Select Home Team", teams_list, index=0)
        with col_sel2:
            selected_away = st.selectbox("Select Away Team", teams_list, index=min(1, len(teams_list)-1))
        
        avg_h_sc = float(df['FTHG'].mean()) if not df.empty else 1.5
        avg_a_sc = float(df['FTAG'].mean()) if not df.empty else 1.2
        
        home_at_home = df[df['HomeTeam'] == selected_home]
        away_at_away = df[df['AwayTeam'] == selected_away]
        
        h_sc = float(home_at_home['FTHG'].mean()) if not home_at_home.empty else 1.5
        h_co = float(home_at_home['FTAG'].mean()) if not home_at_home.empty else 1.0
        a_sc = float(away_at_away['FTAG'].mean()) if not away_at_away.empty else 1.0
        a_co = float(away_at_away['FTHG'].mean()) if not away_at_away.empty else 1.5
        
        st.sidebar.header("🛠️ Situational Modifiers Engine")
        home_xg_mod = st.sidebar.slider(f"{selected_home} xG Multiplier", 0.5, 2.0, 1.0, 0.05)
        away_xg_mod = st.sidebar.slider(f"{selected_away} xG Multiplier", 0.5, 2.0, 1.0, 0.05)
