import pandas as pd
import streamlit as st

st.title("Football Match Predictor")
st.write("Upload your match data CSV to generate simple form-based predictions.")

# File uploader for extracted data
uploaded_file = st.file_uploader("Choose a CSV file", type="and", accept_multiple_files=False)

# Fallback sample data if no file uploaded
if uploaded_file is not None:
  df = pd.read_csv(uploaded_file)
else:
  st.info("Using sample data. Upload your custom CSV to override.")
  data = {
      "HomeTeam": ["Arsenal", "Chelsea", "Liverpool", "Man City"],
      "AwayTeam": ["Everton", "Fulham", "Wolves", "Burnley"],
      "HomeGoalsLast5": [10, 7, 12, 13],
      "AwayGoalsLast5": [5, 6, 4, 3],
  }
  df = pd.DataFrame(data)

st.subheader("Extracted Data Preview")
st.dataframe(df)


# Simple prediction logic based on recent goals
def predict_match(row):
  diff = row["HomeGoalsLast5"] - row["AwayGoalsLast5"]
  if diff > 3:
    return "Home Win (High Confidence)"
  elif diff > 0:
    return "Home Win (Slight Edge)"
  elif diff == 0:
    return "Draw Expected"
  else:
    return "Away Win"


if not df.empty and "HomeGoalsLast5" in df.columns and "AwayGoalsLast5" in df.columns:
  df["Prediction"] = df.apply(predict_match, axis=1)
  st.subheader("Generated Predictions")
  st.dataframe(df[["HomeTeam", "AwayTeam", "Prediction"]])
