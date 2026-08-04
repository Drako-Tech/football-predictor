        with m_col3:
            # Insert expandable predictions tab inside the match column space
            with st.expander("📊 Sofascore Model Predictions"):
                # Compile any raw fixtures stats from your data engine to supply the LLM
                xg_fixture = f.get('xgfixture', {})
                stats = f.get('statistics', [])
                
                # Context packet injected into your prompt
                context_data = f"Match: {home_name} vs {away_name}. Sportmonks context stats: xG={xg_fixture}, historical_stats={stats}"
                
                # --- LLM API CALL EXAMPLE (Using OpenAI or similar client library) ---
                # NOTE: You will need to import your chosen LLM SDK (e.g., openai) at the top of your file
                @st.cache_data(ttl=600)
                def get_llm_sofascore_predictions(match_context):
                    try:
                        # Construct your API payload to your LLM provider here
                        # Ensure you pass the System Prompt Template defined above
                        # response = client.chat.completions.create(model="gpt-4o", messages=[...])
                        # return json.loads(response.choices[0].message.content)
                        pass 
                    except Exception:
                        return None
                
                # For demonstration, assume 'sofascore_payload' is the parsed Python dictionary returned by the LLM
                sofascore_payload = get_llm_sofascore_predictions(context_data)
                
                if sofascore_payload:
                    # 1. Main Markets
                    main_m = sofascore_payload.get("main_markets", {})
                    render_flashscore_prediction_bar("Full-Time Result (1X2)", main_m.get("full_time_result", {}))
                    render_flashscore_prediction_bar("Double Chance", main_m.get("double_chance", {}))
                    
                    # 2. Goals Markets
                    goals_m = sofascore_payload.get("goals_markets", {})
                    render_flashscore_prediction_bar("Both Teams to Score (BTTS)", goals_m.get("both_teams_to_score", {}))
                    render_flashscore_prediction_bar("Over/Under Goals Breakdown", goals_m.get("over_under_total_goals", {}))
                    
                    # 3. Extras
                    corners_cards = sofascore_payload.get("corner_and_cards", {})
                    render_flashscore_prediction_bar("Total Corners Over/Under 9.5", corners_cards.get("total_corners_over_9_5", {}))
                    
                else:
                    # Fallback to display the baseline Sportmonks predictions if the LLM fails or is disconnected
                    predictions = f.get('predictions', [])
                    if predictions:
                        for pred in predictions[:2]:
                            m_name = pred.get('market', {}).get('name', "Probability Result Model")
                            render_flashscore_prediction_bar(m_name, pred.get('predictions', {}))
                    else:
                        st.caption("Model parameters synchronizing with the official pre-match data grids.")
