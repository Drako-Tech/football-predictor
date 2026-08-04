import math
import numpy as np
import pandas as pd
import streamlit as st
import requests

st.set_page_config(layout="wide", page_title="Live Elite Football Hub")
st.title("⚽ Live Automated Football Analytics & Value Hub")

# 🔴 API Key integrated natively into the source code pipeline
ODDS_API_KEY = "6c79e2eacf0174c706c7b1cd8a0fb802"

def poisson_prob(lmbda, k):
    if lmbda <= 0: return 0.0
    return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)

# --- Automated Live Market Odds Fetcher ---
def fetch_live_market_odds(api_key):
    if not api_key:
        return {}
    try:
        url = f"https://the-odds-api.com{api_key}&regions=uk&markets=h2h&oddsFormat=decimal"
        response = requests.get(url, timeout=10).json()
        odds_dict = {}
        for match in response:
            home = match.get('home_team')
            away = match.get('away_team')
            bookmakers = match.get('bookmakers', [])
            if bookmakers:
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
        'P_h': h_group['FTHG'].count(),
        'W_h': h_group.apply(lambda x: (x['FTR'] == 'H').sum()),
        'D_h': h_group.apply(lambda x: (x['FTR'] == 'D').sum()),
        'L_h': h_group.apply(lambda x: (x['FTR'] == 'L').sum() if 'L' in x['FTR'].values else (x['FTR'] == 'A').sum()),
        'GF_h': h_group['FTHG'].sum(),
        'GA_h': h_group['FTAG'].sum()
    })

    a_group = working_df.groupby('AwayTeam')
    away_stats = pd.DataFrame({
        'P_a': a_group['FTAG'].count(),
        'W_a': a_group.apply(lambda x: (x['FTR'] == 'A').sum()),
        'D_a': a_group.apply(lambda x: (x['FTR'] == 'D').sum()),
        'L_a': a_group.apply(lambda x: (x['FTR'] == 'A').sum() if 'A' in x['FTR'].values else (x['FTR'] == 'H').sum()),
        'GF_a': a_group['FTAG'].sum(),
        'GA_a': a_group['FTHG'].sum()
    })

    table = home_stats.join(away_stats, how='outer').fillna(0).astype(int)
    table['Played'] = table['P_h'] + table['P_a']
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

@st.cache_data(ttl=3600)
def load_safely_from_web():
    try:
        current_season_url = "https://football-data.co.uk"
        test_df = pd.read_csv(current_season_url, nrows=5)
        if not test_df.empty and "HomeTeam" in test_df.columns:
            return pd.read_csv(current_season_url), "2025/2026 Live Football Dataset"
    except Exception:
        pass
    fallback_url = "https://football-data.co.uk"
    return pd.read_csv(fallback_url), "2024/2025 Season Archive Backup"

try:
    with st.spinner("🔄 Synchronizing global analytics channels safely over the cloud..."):
        df, source_label = load_safely_from_web()
        live_odds_book = fetch_live_market_odds(ODDS_API_KEY)
    st.success(f"🟢 Cloud Data Sync Active: Using {source_label}")
    
    required_cols = ["HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "HS", "AS", "HST", "AST"]
    if all(col in df.columns for col in required_cols):
        teams_list = sorted(df['HomeTeam'].dropna().unique().tolist())
        
        tab1, tab2 = st.tabs(["🎯 Match Forecast Simulation Engine", "📊 Live Standings & Form Matrix Dashboard"])
        
        with tab1:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                selected_home = st.selectbox("Select Home Team", teams_list, index=0)
            with col_sel2:
                selected_away = st.selectbox("Select Away Team", teams_list, index=min(1, len(teams_list)-1))
            
            avg_h_sc = float(df['FTHG'].mean())
            avg_a_sc = float(df['FTAG'].mean())
            home_at_home = df[df['HomeTeam'] == selected_home]
            away_at_away = df[df['AwayTeam'] == selected_away]
            
            h_sc = float(home_at_home['FTHG'].mean()) if not home_at_home.empty else 1.5
            h_co = float(home_at_home['FTAG'].mean()) if not home_at_home.empty else 1.0
            a_sc = float(away_at_away['FTAG'].mean()) if not away_at_away.empty else 1.0
            a_co = float(away_at_away['FTHG'].mean()) if not away_at_away.empty else 1.5
            
            st.sidebar.header("🛠️ Situational Modifiers Engine")
            home_xg_mod = st.sidebar.slider(f"{selected_home} xG Multiplier", 0.5, 2.0, 1.0, 0.05)
            away_xg_mod = st.sidebar.slider(f"{selected_away} xG Multiplier", 0.5, 2.0, 1.0, 0.05)
            home_injuries = st.sidebar.selectbox(f"{selected_home} Key Absences", ["No Key Absences", "Minor Squad Absences", "Severe Absences"])
            away_injuries = st.sidebar.selectbox(f"{selected_away} Key Absences", ["No Key Absences", "Minor Squad Absences", "Severe Absences"])
            
            injury_map = {"No Key Absences": 1.0, "Minor Squad Absences": 0.92, "Severe Absences": 0.80}
            home_modifier = home_xg_mod * injury_map[home_injuries]
            away_modifier = away_xg_mod * injury_map[away_injuries]
            
            home_exp_goals = max(0.1, (h_sc / avg_h_sc) * (a_co / avg_a_sc) * avg_h_sc * home_modifier)
            away_exp_goals = max(0.1, (a_sc / avg_a_sc) * (h_co / avg_h_sc) * avg_a_sc * away_modifier)
            
            if st.button("Run Simulation Engine", type="primary"):
                max_goals = 6
                h_p = np.array([poisson_prob(home_exp_goals, i) for i in range(max_goals)])
                a_p = np.array([poisson_prob(away_exp_goals, j) for j in range(max_goals)])
                grid = np.outer(h_p, a_p)
                
                home_win_p = float(np.sum(np.tril(grid, -1))) * 100
                draw_p = float(np.sum(np.diag(grid))) * 100
                away_win_p = float(np.sum(np.triu(grid, 1))) * 100
                
                st.success(f"🎯 Expected Projected Goals: {selected_home} {home_exp_goals:.2f} vs {selected_away} {away_exp_goals:.2f}")
                
                outcomes_df = pd.DataFrame({
                    "Match Outcome": [f"Home Win ({selected_home})", "Draw Match", f"Away Win ({selected_away})"],
                    "Probability (%)": [f"{home_win_p:.1f}%", f"{draw_p:.1f}%", f"{away_win_p:.1f}%"]
                })
                st.table(outcomes_df)
                
                max_idx = np.unravel_index(np.argmax(grid), grid.shape)
                st.info(f"✨ **Most Likely Exact Scoreline**: {selected_home} {max_idx} - {max_idx} ({grid[max_idx]*100:.1f}% probability)")
                
                under_2_5_mask = np.fromfunction(lambda i, j: (i + j) < 2.5, (max_goals, max_goals))
                under_2_5_prob = float(np.sum(grid[under_2_5_mask]))
                over_2_5_prob = (1.0 - under_2_5_prob) * 100
                btts_no_prob = float(np.sum(grid[:, 0]) + np.sum(grid[0, :]) - grid)
                btts_yes_prob = (1.0 - btts_no_prob) * 100
                
                st.subheader("🎲 Embedded Derivative Value Betting Parameters")
                b1, b2 = st.columns(2)
                b1.metric("Over 2.5 Total Goals Probability", f"{over_2_5_prob:.1f}%")
                b2.metric("Both Teams to Score (BTTS Yes)", f"{btts_yes_prob:.1f}%")
                
                st.subheader("🔢 Poisson Scoreline Distribution Matrix")
                matrix_df = pd.DataFrame(grid * 100, columns=[f"Away {g}" for g in range(max_goals)], index=[f"Home {g}" for g in range(max_goals)])
                st.dataframe(matrix_df, use_container_width=True)
                
                # --- INTEGRATED REAL-TIME VALUE BET TRACKER ---
