import math
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("⚽ Elite Football Predictive Analytics Dashboard")


def poisson_prob(lmbda, k):
  if lmbda <= 0:
    return 0.0
  return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)


st.subheader("Step 1: Upload Your Extracted Data")
uploaded_file = st.file_uploader(
    "Drag and drop your Football-Data.co.uk CSV file here", type=["csv"]
)

if uploaded_file is not None:
  try:
    df = pd.read_csv(uploaded_file)
    st.success("Data engine loaded successfully!")
    teams_list = sorted(df["HomeTeam"].dropna().unique().tolist())

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
      selected_home = st.selectbox("Select Home Team", teams_list, index=0)
    with col_sel2:
      selected_away = st.selectbox(
          "Select Away Team", teams_list, index=min(1, len(teams_list) - 1)
      )

    # 1. Base Statistics & Global League Averages
    avg_h_sc = float(df["FTHG"].mean())
    avg_a_sc = float(df["FTAG"].mean())

    home_at_home = df[df["HomeTeam"] == selected_home]
    away_at_away = df[df["AwayTeam"] == selected_away]

    h_sc = (
        float(home_at_home["FTHG"].mean()) if not home_at_home.empty else 1.5
    )
    h_co = (
        float(home_at_home["FTAG"].mean()) if not home_at_home.empty else 1.0
    )
    a_sc = float(away_at_away["FTAG"].mean()) if not away_at_away.empty else 1.0
    a_co = float(away_at_away["FTHG"].mean()) if not away_at_away.empty else 1.5

    # 2. Advanced Extracted Metrics (Form & Shots)
    home_all = df[(df["HomeTeam"] == selected_home) | (df["AwayTeam"] == selected_home)]
    away_all = df[(df["HomeTeam"] == selected_away) | (df["AwayTeam"] == selected_away)]

    def get_weighted_form(team, matches):
      recent = matches.tail(5).copy()
      if recent.empty:
        return 50.0
      weights = [0.1, 0.15, 0.2, 0.25, 0.3]
      pts = []
      for _, r in recent.iterrows():
        if r["HomeTeam"] == team:
          p = 3 if r["FTR"] == "H" else (1 if r["FTR"] == "D" else 0)
        else:
          p = 3 if r["FTR"] == "A" else (1 if r["FTR"] == "D" else 0)
        pts.append(p)
      while len(pts) < 5:
        pts.insert(0, 1)
      return (sum(p * w for p, w in zip(pts, weights)) / 3.0) * 100

    h_form = get_weighted_form(selected_home, home_all)
    a_form = get_weighted_form(selected_away, away_all)

    tot_h_shots = home_at_home["HS"].sum()
    tot_h_goals = home_at_home["FTHG"].sum()
    h_conv = (tot_h_goals / tot_h_shots * 100) if tot_h_shots > 0 else 10.0

    tot_a_shots = away_at_away["AS"].sum()
    tot_a_goals = away_at_away["FTAG"].sum()
    a_conv = (tot_a_goals / tot_a_shots * 100) if tot_a_shots > 0 else 10.0

    # Render Performance Row Panels
    st.subheader("📊 Extracted Advanced Metrics & Performance Dashboard")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{selected_home} Form Rating", f"{h_form:.1f}%")
    m2.metric(f"{selected_home} Shot Conversion", f"{h_conv:.1f}%")
    m3.metric(f"{selected_away} Form Rating", f"{a_form:.1f}%")
    m4.metric(f"{selected_away} Shot Conversion", f"{a_conv:.1f}%")

    # 3. Situational Sidebar Engine
    st.sidebar.header("🛠️ Situational Modifiers Engine")
    home_xg_mod = st.sidebar.slider(
        f"{selected_home} xG Multiplier", 0.5, 2.0, 1.0, 0.05
    )
    away_xg_mod = st.sidebar.slider(
        f"{selected_away} xG Multiplier", 0.5, 2.0, 1.0, 0.05
    )

    home_injuries = st.sidebar.selectbox(
        f"{selected_home} Key Absences",
        ["No Key Absences", "Minor Squad Absences", "Severe Absences"],
    )
    away_injuries = st.sidebar.selectbox(
        f"{selected_away} Key Absences",
        ["No Key Absences", "Minor Squad Absences", "Severe Absences"],
    )

    injury_map = {
        "No Key Absences": 1.0,
        "Minor Squad Absences": 0.92,
        "Severe Absences": 0.80,
    }

    home_modifier = home_xg_mod * injury_map[home_injuries]
    away_modifier = away_xg_mod * injury_map[away_injuries]

    home_exp_goals = max(
        0.1, (h_sc / avg_h_sc) * (a_co / avg_a_sc) * avg_h_sc * home_modifier
    )
    away_exp_goals = max(
        0.1, (a_sc / avg_a_sc) * (h_co / avg_h_sc) * avg_a_sc * away_modifier
    )

    # 4. Main Dashboard Output Pipeline
    st.subheader("🎯 Contextual Prediction Engine Output")
    if st.button("Run Simulation Engine", type="primary"):
      max_goals = 6
      h_p = np.array([poisson_prob(home_exp_goals, i) for i in range(max_goals)])
      a_p = np.array([poisson_prob(away_exp_goals, j) for j in range(max_goals)])
      grid = np.outer(h_p, a_p)

      home_win_p = float(np.sum(np.tril(grid, -1))) * 100
      draw_p = float(np.sum(np.diag(grid))) * 100
      away_win_p = float(np.sum(np.triu(grid, 1))) * 100

      st.success(
          f"🎯 Expected Goals: {selected_home} {home_exp_goals:.2f} vs"
          f" {selected_away} {away_exp_goals:.2f}"
      )

      outcomes_df = pd.DataFrame({
          "Match Outcome": [
              f"Home Win ({selected_home})",
              "Draw Match",
              f"Away Win ({selected_away})",
          ],
          "Probability (%)": [
              f"{home_win_p:.1f}%",
              f"{draw_p:.1f}%",
              f"{away_win_p:.1f}%",
          ],
      })
      st.table(outcomes_df)

      max_idx = np.unravel_index(np.argmax(grid), grid.shape)
      st.info(
          f"✨ **Most Likely Scoreline**: {selected_home} {max_idx} -"
          f" {max_idx} ({grid[max_idx]*100:.1f}% probability)"
      )

      st.subheader("🔢 Poisson Scoreline Distribution Grid")
      matrix_df = pd.DataFrame(
          grid * 100,
          columns=[f"{selected_away} {g}" for g in range(max_goals)],
          index=[f"{selected_home} {g}" for g in range(max_goals)],
      )
      st.dataframe(matrix_df.style.background_gradient(cmap="Blues"))

      # --- 5. Integrated Live Odds & Value Bet Tracker Engine ---
      st.subheader("🏦 Live Odds Market & Predictive Value Tracker")
      st.caption(
          "Enter bookmaker decimal odds below to evaluate pricing discrepancies"
          " against your predictive analytics engine:"
      )

      fair_home_odds = 100 / home_win_p if home_win_p > 0 else 999.0
      fair_draw_odds = 100 / draw_p if draw_p > 0 else 999.0
      fair_away_odds = 100 / away_win_p if away_win_p > 0 else 999.0

      o1, o2, o3 = st.columns(3)
      with o1:
        bookie_home = st.number_input(
            f"Market Odds: {selected_home} Win", value=1.85, step=0.05
        )
      with o2:
        bookie_draw = st.number_input(
            "Market Odds: Draw Match", value=3.40, step=0.05
        )
      with o3:
        bookie_away = st.number_input(
            f"Market Odds: {selected_away} Win", value=4.20, step=0.05
        )

      edge_home = (bookie_home / fair_home_odds) - 1.0
      edge_draw = (bookie_draw / fair_draw_odds) - 1.0
      edge_away = (bookie_away / fair_away_odds) - 1.0

      st.write("### 📊 Market Discrepancy Matrix Analysis")
      v1, v2, v3 = st.columns(3)

      if edge_home > 0:
        v1.success(
            f"🟩 **VALUE DETECTED on {selected_home}**  \n"
            f"Model Fair Odds: **{fair_home_odds:.2f}**  \n"
            f"Your Mathematical Edge: **+{edge_home*100:.1f}%**"
        )
      else:
        v1.error(
            f"❌ No Value on {selected_home}  \n"
            f"Model Fair Odds: **{fair_home_odds:.2f}**  \n"
            f"Negative Edge: **{edge_home*100:.1f}%**"
        )

      if edge_draw > 0:
        v2.success(
            f"🟩 **VALUE DETECTED on DRAW**  \n"
            f"Model Fair Odds: **{fair_draw_odds:.2f}**  \n"
            f"Your Mathematical Edge: **+{edge_draw*100:.1f}%**"
        )
      else:
        v2.error(
            f"❌ No Value on Draw  \n"
            f"Model Fair Odds: **{fair_draw_odds:.2f}**  \n"
            f"Negative Edge: **{edge_draw*100:.1f}%**"
        )

      if edge_away > 0:
        v3.success(
            f"🟩 **VALUE DETECTED on {selected_away}**  \n"
            f"Model Fair Odds: **{fair_away_odds:.2f}**  \n"
            f"Your Mathematical Edge: **+{edge_away*100:.1f}%**"
        )
      else:
        v3.error(
            f"❌ No Value on {selected_away}  \n"
            f"Model Fair Odds: **{fair_away_odds:.2f}**  \n"
            f"Negative Edge: **{edge_away*100:.1f}%**"
        )

  except Exception as e:
    st.error(f"Execution Error: {e}")
else:
  st.info(
      "💡 Drop your E0.csv file here to run the complete predictive matrix"
      " suite."
  )
