import json
from math import pow
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# Elo rating functions
def expected_score(rating_a, rating_b):
    return 1 / (1 + pow(10, (rating_b - rating_a) / 400))

def update_elo(rating_a, rating_b, actual_score_a, k=32):
    expected_a = expected_score(rating_a, rating_b)
    new_rating_a = rating_a + k * (actual_score_a - expected_a)
    new_rating_b = rating_b + k * ((1 - actual_score_a) - (1 - expected_a))
    return new_rating_a, new_rating_b

# Function to clean team names by removing sponsor prefixes
def clean_team_name(team_name):
    prefixes = ["GAÜ ", "DND L. ", "Miracle ", "China Bazaar ", "Tremeşeli H. "]
    suffixes = [" TSK", " GSK", " SK", " DSK", " YSK", " GBSK", " ŞHSK", " İYSK", " KKSK"]
    cleaned = team_name
    for prefix in prefixes:
        cleaned = cleaned.replace(prefix, "")
    for suffix in suffixes:
        cleaned = cleaned.replace(suffix, "")
    return cleaned.strip()

# Function to process matches and track Elo history
def calculate_elo_ratings(data):
    elo_ratings = {}
    elo_history = {}
    
    for season_data in data:
        season = season_data["season"]
        weeks = season_data["weeks"]
        for week, matches in weeks.items():
            timestamp = f"{season} - {week}"
            for match in matches:
                if "home_score" not in match or "away_score" not in match:
                    continue
                
                home_team = clean_team_name(match["home_team"])
                away_team = clean_team_name(match["away_team"])
                home_score = match["home_score"]
                away_score = match["away_score"]
                
                if home_team not in elo_ratings:
                    elo_ratings[home_team] = 1500
                    elo_history[home_team] = [(timestamp, 1500)]
                if away_team not in elo_ratings:
                    elo_ratings[away_team] = 1500
                    elo_history[away_team] = [(timestamp, 1500)]
                
                actual_score = 1 if home_score > away_score else 0.5 if home_score == away_score else 0
                new_home_elo, new_away_elo = update_elo(
                    elo_ratings[home_team], elo_ratings[away_team], actual_score
                )
                
                elo_ratings[home_team] = new_home_elo
                elo_ratings[away_team] = new_away_elo
                elo_history[home_team].append((timestamp, new_home_elo))
                elo_history[away_team].append((timestamp, new_away_elo))
    
    return elo_ratings, elo_history

# Function to create Plotly figure
def create_plot(elo_history, selected_team="All Teams"):
    fig = go.Figure()
    
    for team, history in elo_history.items():
        timestamps, ratings = zip(*history)
        visible = True if selected_team == "All Teams" or selected_team == team else False
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=ratings,
            mode='lines+markers',
            name=team,
            hovertemplate='%{x}<br>Elo: %{y:.0f}<extra></extra>',
            visible=visible
        ))
    
    fig.update_layout(
        title="Elo Rating Progression Over Time",
        xaxis_title="Season - Week",
        yaxis_title="Elo Rating",
        hovermode="x unified",
        template="plotly_white",
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5),
        annotations=[
            dict(
                text="Click legend to toggle. Double-click to isolate. Use dropdown to filter.",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0,
                y=1.05
            )
        ]
    )
    
    return fig

# Streamlit app
def main():
    st.title("Kuzey Kıbrıs Football Elo Ratings")
    
    # Load JSON data
    try:
        with open("combined_data.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except FileNotFoundError:
        st.error("Error: 'combined_data.json' file not found. Please ensure it exists in the same directory.")
        return
    except json.JSONDecodeError:
        st.error("Error: Invalid JSON format in 'combined_data.json'. Please check the file.")
        return
    
    # Calculate Elo ratings and history
    with st.spinner("Calculating Elo ratings..."):
        final_ratings, elo_history = calculate_elo_ratings(json_data)
    
    # Display final ratings
    st.subheader("Final Elo Ratings (as of March 11, 2025)")
    ratings_df = pd.DataFrame(
        sorted(final_ratings.items(), key=lambda x: x[1], reverse=True),
        columns=["Team", "Elo Rating"]
    )
    ratings_df["Elo Rating"] = ratings_df["Elo Rating"].round(0).astype(int)
    st.dataframe(ratings_df, height=300, use_container_width=True)
    
    # Team selection dropdown
    st.subheader("Elo Rating Progression")
    team_options = ["All Teams"] + sorted(elo_history.keys())
    selected_team = st.selectbox("Select a team to filter:", team_options)
    
    # Generate and display plot
    fig = create_plot(elo_history, selected_team)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()