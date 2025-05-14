import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend for Streamlit # Helps with stability of the app
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
import requests

st.set_page_config(page_title="DartCompact 🎯", layout="centered")

# === Logic of the game ===
def create_players(players_names):
    return [{"name": name, "score": 301, "history": [], "victories": 0} for name in players_names]

def process_turn(player, throws):
    total_score = sum(throws)
    new_score = player['score'] - total_score

    # Initialize ML data if not present
    if 'ml_data' not in st.session_state:
        st.session_state.ml_data = pd.DataFrame(columns=['player', 'avg_throw', 'total_throws', 'current_score', 'max_throw', 'won'])
    
    # Add throws to history
    player['history'].append(throws)

    if new_score < 0:
        message = "Bust! You overpassed your score."
        new_score = player['score']  # Score stays the same if the player busts
        game_over = False
    else:
        message = f"Remaining score: {new_score} points"
        game_over = new_score == 0  # Player wins if score == 0

    player['score'] = new_score
    return game_over, new_score, message

# Multi-player dart game using Streamlit for name input, avatars, and score tracking
st.title("🎯 DartCompact")
st.write("Welcome to the compact dart game for multiple players!")

# Initialize session state variables only once
if "players" not in st.session_state:
    st.session_state.players = []  # Player names
    st.session_state.scores = {}  # Player scores
    st.session_state.winner = None  # Game winner
    st.session_state.game_started = False  # Game status
    st.session_state.game_count = 0  # Initialize game counter
    st.session_state.ml_data = pd.DataFrame(columns=['player', 'avg_throw', 'total_throws', 'current_score', 'max_throw', 'won'])
    
# Game setup UI
if not st.session_state.game_started:
    num_players = st.number_input("Number of players", min_value=1, max_value=8, step=1)
    require_double_out = st.checkbox("Require double to win", value=True)
    starting_score = st.selectbox("Select starting score", [101, 301, 501], index=1)

    player_names = []
    avatars = {}
    options = ["Kim", "Alexis", "Robyn", "Billie", "Lou", "Charlie"]

    # Input for player names
    for i in range(num_players):
        name = st.text_input(f"Name of Player {i+1}", key=f"name_{i}")
        player_names.append(name)

    # Select avatars
    for i, name in enumerate(player_names):
        avatar_choice = st.radio(f"Choose avatar for Player {i+1}", options=options, horizontal=True, key=f"avatar_choice_{i}")
        avatar_url = f"https://api.dicebear.com/7.x/adventurer/svg?seed={avatar_choice}_default"
        st.image(avatar_url, width=100)
        avatars[name] = avatar_url
    st.session_state.avatars = avatars

    # Start game button
    if st.button("Start Game"):
        if all(name.strip() != "" for name in player_names):
            st.session_state.players = player_names
            st.session_state.scores = {name: starting_score for name in player_names}
            st.session_state.throws = {name: [] for name in player_names}
            st.session_state.turn = 0
            st.session_state.game_started = True
            st.session_state.require_double_out = require_double_out
            
            # Increment game counter
            st.session_state.game_count += 1
            st.success(f"Starting game #{st.session_state.game_count}")
            
            # Try to train the ML model if we have enough data
            if st.session_state.game_count >= 2:
                try:
                    df = st.session_state.ml_data
                    if len(df) >= 10 and len(set(df['won'])) > 1:
                        X = df[['avg_throw', 'total_throws', 'current_score', 'max_throw']].apply(pd.to_numeric, errors='coerce')
                        y = df['won'].astype(int)
                        model = LogisticRegression(solver='liblinear')
                        model.fit(X, y)
                        st.session_state.ml_model = model
                        st.success("ML model trained successfully!")
                except Exception as e:
                    st.error(f"Error training ML model: {e}")
                
            st.rerun()
        else:
            st.warning("Please fill in all player names.")

else:
    # Initialize throw tracking if needed
    if "has_thrown" not in st.session_state:
        st.session_state.has_thrown = False
    if "throw_count" not in st.session_state:
        st.session_state.throw_count = 0

    # Get current player data
    player_name = st.session_state.players[st.session_state.turn]
    player_throws = st.session_state.throws[player_name]
    current_score = st.session_state.scores[player_name]
    
    # Track player performance for ML only if they've made throws
    if player_throws:
        player_data = {
            'player': player_name,
            'avg_throw': sum(player_throws) / len(player_throws),
            'total_throws': len(player_throws),
            'current_score': current_score,
            'max_throw': max(player_throws),
            'won': 0  # Will be updated to 1 if player wins
        }
        # Add to ML dataset
        st.session_state.ml_data = pd.concat([st.session_state.ml_data, pd.DataFrame([player_data])], ignore_index=True)

    # Game over logic
    if st.session_state.winner:
        st.success(f"🏆 {st.session_state.winner} has won the game!")
        
        # Process winner data only once
        if 'winner_processed' not in st.session_state:
            st.session_state.winner_processed = True
            
            # Train ML model with updated win data
            try:
                df = st.session_state.ml_data
                if len(df) >= 10 and len(set(df['won'])) > 1:
                    X = df[['avg_throw', 'total_throws', 'current_score', 'max_throw']].apply(pd.to_numeric, errors='coerce')
                    y = df['won'].astype(int)
                    model = LogisticRegression(solver='liblinear')
                    model.fit(X, y)
                    st.session_state.ml_model = model
                    st.success("ML model trained successfully!")
            except Exception as e:
                st.error(f"Error training ML model: {e}")

        # Create final ranking sorted by remaining score
        winner = st.session_state.winner
        others = [p for p in st.session_state.players if p != winner]
        others_sorted = sorted(others, key=lambda p: st.session_state.scores[p])
        ranking = [winner] + others_sorted

        # Display podium
        st.markdown("## 🏅 Final Standings")
        podium_cols = st.columns([1, 1, 1])
        podium_order = [0, 1, 2]  # Show 1st, 2nd, 3rd left to right

        for idx, pos in enumerate(podium_order):
            if pos < len(ranking):  # Check if there are enough players
                player = ranking[pos]
                with podium_cols[idx]:
                    medal = "🥇 **1st Place**" if pos == 0 else "🥈 **2nd Place**" if pos == 1 else "🥉 **3rd Place**"
                    st.markdown(medal)
                    st.image(st.session_state.avatars[player], width=100)
                    st.markdown(f"### {player}")
        
        # Game statistics
        st.write("## 📊 Game Statistics")
        stats_data = {"Players": [], "Average Points": [], "Max Points": []}

        for player, throws in st.session_state.throws.items():
            if throws:  # Only add stats if player has made throws
                stats_data["Players"].append(player)
                stats_data["Average Points"].append(sum(throws)/len(throws))
                stats_data["Max Points"].append(max(throws))

        # Only create stats if there's data
        if stats_data["Players"]:
            stats_df = pd.DataFrame(stats_data).set_index("Players")
            st.write("### Average Points per Throw")
            st.bar_chart(stats_df["Average Points"])
            st.write("### Max Points in a Single Throw")
            st.bar_chart(stats_df["Max Points"])
        
        # Display ML insights if model exists and enough data
        if 'ml_model' in st.session_state and len(st.session_state.ml_data) > 5:
            st.markdown("## 🧠 ML Model Insights")
            
            # Get all player data
            all_players = list(set(st.session_state.ml_data['player'].values))
            
            # Group player stats
            player_stats = st.session_state.ml_data.groupby('player').agg({
                'won': 'sum', 'avg_throw': 'mean', 'total_throws': 'sum', 'max_throw': 'max'
            }).reset_index()
            
            # Player performance only (remove the columns layout)
            st.write("### Player Performance")
            
            # Get win counts from player_stats
            win_counts = {row['player']: row['won'] for _, row in player_stats.iterrows()}
            
            # Track player participation in games
            if 'player_games' not in st.session_state:
                st.session_state.player_games = {player: 0 for player in all_players}
            
            # Use game count for win rate calculation
            games_played = {player: max(1, st.session_state.game_count) for player in all_players}
            
            # Create display dataframe
            display_data = []
            for player in all_players:
                if player in player_stats['player'].values:  # Check if player has stats
                    avg_score = player_stats[player_stats['player'] == player]['avg_throw'].values[0]
                    max_score = player_stats[player_stats['player'] == player]['max_throw'].values[0]
                    wins = win_counts.get(player, 0)
                    
                    # Calculate win rate
                    win_rate = (wins / games_played[player]) * 100
                    
                    display_data.append({
                        'player': player,
                        'Wins': wins,
                        'Win Rate %': win_rate,
                        'Avg Score': round(avg_score, 1),
                        'Best Throw': int(max_score),
                    })
            
            # Display player stats
            if display_data:
                display_df = pd.DataFrame(display_data).set_index('player')
                st.info("Win rate calculated based on total completed games")
                st.dataframe(display_df)
            else:
                st.write("No player statistics available yet.")
        
        # Pro player comparison
        st.write("## 🧠 Compare Yourself to a Pro")
        pro_player = "Michael van Gerwen"
        pro_competitor_id = "sr:competitor:26280"
        API_KEY = "0j9Nj7DIbdznIAKdz6LPFnHWmYChwGUQgboXO76n"
        
        # Pro player stats (with fallback values)
        pro_avg = 98.5
        pro_max = 180
        
        try:
            url = f"https://api.sportradar.com/darts/trial/v2/en/competitors/{pro_competitor_id}/profile.json?api_key={API_KEY}"
            response = requests.get(url, timeout=5)  # Add timeout
            if response.status_code == 200:
                data = response.json()
                stats = data.get("statistics", {})
                pro_avg = stats.get("average_3_dart_score", pro_avg)
                pro_max = stats.get("best_3_dart_score", pro_max)
        except Exception as e:
            st.warning(f"Could not fetch pro data: {str(e)}. Using default values.")
 
        # Compare each player to pro
        for player, throws in st.session_state.throws.items():
            if throws:  # Only show comparison if player has made throws
                user_avg = sum(throws)/len(throws)
                user_max = max(throws)
 
                st.markdown(f"### {player} vs {pro_player}")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="🎯 Your Avg", value=round(user_avg, 1))
                    st.metric(label="🔥 Your Max Throw", value=user_max)
                with col2:
                    st.metric(label="🏆 Pro Avg", value=round(pro_avg, 1))
                    st.metric(label="🚀 Pro Max Throw", value=pro_max)
 
                # Visual comparison (protect against division by zero)
                if pro_avg > 0:
                    percent_of_pro = min(user_avg / pro_avg, 1.0)
                    st.progress(percent_of_pro)
                    st.caption(f"You're at {percent_of_pro*100:.1f}% of professional level")
    
    # Active game interface
    else:
        current_player = st.session_state.players[st.session_state.turn]
        st.image(st.session_state.avatars[current_player], width=100, caption=f"{current_player}'s Avatar")
        st.subheader(f"{current_player}'s turn – Current Score: {st.session_state.scores[current_player]}")

        # Track last turn to reset state properly
        if "last_turn" not in st.session_state:
            st.session_state.last_turn = -1

        # Reset state if turn changed
        if st.session_state.turn != st.session_state.last_turn:
            st.session_state.pop(f"base_score_{current_player}", None)
            st.session_state.pop(f"multiplier_{current_player}", None)
            st.session_state.last_turn = st.session_state.turn
            st.session_state.has_thrown = False
            st.session_state.throw_count = 0

        # Throw input form
        with st.form(key=f"{current_player}_throw_form_{st.session_state.throw_count}", clear_on_submit=True):
            base_score = st.selectbox(
                "Base Score",
                [0] + [i for i in range(1, 21)] + [25, 50],
                key=f"base_score_{current_player}_{st.session_state.throw_count}"
            )
            multiplier = st.radio(
                "Multiplier",
                ["Single", "Double", "Triple"],
                horizontal=True,
                key=f"multiplier_{current_player}_{st.session_state.throw_count}"
            )
            submitted = st.form_submit_button("Confirm Throw")

        # Process throw if submitted
        if submitted and not st.session_state.has_thrown:
            # Validate score rules
            if base_score in [25, 50] and multiplier in ["Double", "Triple"]:
                st.info("Double or Triple is not allowed on 25 or 50. Using Single.")
                multiplier = "Single"

            # Calculate points
            points = base_score * (1 if multiplier == "Single" else 2 if multiplier == "Double" else 3)

            # Update score and handle game logic
            current_score = st.session_state.scores[current_player]
            new_score = current_score - points

            if new_score < 0:
                st.info("Overshoot! Score remains the same.")
                st.session_state.throws[current_player].append(0)  # Record zero for overshoot
                st.session_state.throw_count += 1
                if st.session_state.throw_count >= 3:
                    st.session_state.has_thrown = True
            elif new_score == 0:
                if st.session_state.require_double_out and multiplier != "Double":
                    st.info("You need to finish on a Double to win!")
                    st.session_state.throws[current_player].append(0)  # Record zero for invalid finish
                    st.session_state.throw_count += 1
                    if st.session_state.throw_count >= 3:
                        st.session_state.has_thrown = True
                else:
                    # Player wins
                    st.session_state.scores[current_player] = 0
                    st.session_state.winner = current_player
                    st.session_state.throws[current_player].append(points)
                    
                    # Update winner in ML data
                    winner_entries = st.session_state.ml_data[st.session_state.ml_data['player'] == current_player]
                    if not winner_entries.empty:
                        last_entry_idx = winner_entries.index[-1]
                        st.session_state.ml_data.at[last_entry_idx, 'won'] = 1
                    
                    st.session_state.has_thrown = True
                    st.rerun()  # Show win immediately
            else:
                # Normal score update
                st.session_state.scores[current_player] = new_score
                st.session_state.throws[current_player].append(points)
                st.session_state.throw_count += 1
                if st.session_state.throw_count >= 3:
                    st.session_state.has_thrown = True
            
            # Refresh UI if needed
            if not st.session_state.has_thrown:
                st.rerun()

        # Next turn button
        if st.session_state.has_thrown:
            if st.button("Next Turn"):
                st.session_state.turn = (st.session_state.turn + 1) % len(st.session_state.players)
                st.session_state.has_thrown = False
                st.session_state.throw_count = 0
                current_player = st.session_state.players[st.session_state.turn]
                st.session_state.pop(f"base_score_{current_player}", None)
                st.session_state.pop(f"multiplier_{current_player}", None)
                st.rerun()

# Restart game button
if st.button("Restart Game"):
    # Save important data before reset
    saved_ml_data = st.session_state.ml_data.copy() if 'ml_data' in st.session_state else pd.DataFrame(
        columns=['player', 'avg_throw', 'total_throws', 'current_score', 'max_throw', 'won'])
    saved_game_count = st.session_state.game_count if 'game_count' in st.session_state else 0
    saved_ml_model = st.session_state.ml_model if 'ml_model' in st.session_state else None
    
    # Clear all session state keys except those needed for ML
    keys_to_keep = ['ml_data', 'game_count', 'ml_model']
    keys_to_clear = [k for k in st.session_state.keys() if k not in keys_to_keep]
    
    for key in keys_to_clear:
        del st.session_state[key]
    
    # Restore ML data
    st.session_state.ml_data = saved_ml_data
    st.session_state.game_count = saved_game_count
    if saved_ml_model is not None:
        st.session_state.ml_model = saved_ml_model
        
    st.success(f"Game reset! You've played {saved_game_count} games so far.")
    st.rerun()
