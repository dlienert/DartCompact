import streamlit as st
import pandas as pd

# Multi-player dart game using Streamlit for name input, avatars, and score tracking.

st.set_page_config(page_title="DartCompact 🎯", layout="centered")

st.title("🎯 DartCompact")
st.write("Welcome to the compact dart game for multiple players!")

# Initialize players and game state
if "players" not in st.session_state:
    st.session_state.players = []  # Player names
    st.session_state.scores = {}  # Player scores
    st.session_state.winner = None  # Game winner
    st.session_state.game_started = False  # Game status

# Game setup UI
if not st.session_state.game_started:
    num_players = st.number_input("Number of players", min_value=1, max_value=8, step=1)  # Player count
    require_double_out = st.checkbox("Require double to win", value=True)  # Double Out Rule
    starting_score = st.selectbox("Select starting score", [101, 301, 501], index=1)  # Starting score

    player_names = []  # Player names list
    avatars = {}  # Player avatars dictionary
    options = ["Kim", "Alexis", "Robyn", "Billie", "Lou", "Charlie"]  # Avatar options

    # Input for player names and avatars
    for i in range(num_players):
        name = st.text_input(f"Name of Player {i+1}", key=f"name_{i}")
        player_names.append(name)

    for i, name in enumerate(player_names):
        avatar_choice = st.radio(f"Choose avatar for Player {i+1}", options=options, horizontal=True, key=f"avatar_choice_{i}")
        avatar_url = f"https://api.dicebear.com/7.x/adventurer/svg?seed={avatar_choice}_default"
        st.image(avatar_url, width=100)  # Display avatar
        avatars[name] = avatar_url  # Map name to avatar URL
    st.session_state.avatars = avatars  # Store avatars

    # Start game logic
    if st.button("Start Game"):
        if all(name.strip() != "" for name in player_names):  # Check names
            st.session_state.players = player_names  # Store names
            st.session_state.scores = {name: starting_score for name in player_names}  # Initialize scores
            st.session_state.throws = {name: [] for name in player_names}  # Track throws
            st.session_state.turn = 0  # Initialize turn
            st.session_state.game_started = True  # Mark game started
            st.session_state.require_double_out = require_double_out  # Store rule preference
        else:
            st.warning("Please fill in all player names.")  # Warning for missing names

else:
    # Initialize throw tracking
    if "has_thrown" not in st.session_state:
        st.session_state.has_thrown = False

    # Game over logic
    if st.session_state.winner:
        st.success(f"🏆 {st.session_state.winner} has won the game!")
        
        # Show final stats
        st.write("## Game Statistics")
        stats_data = {"Players": [], "Average Points": [], "Max Points": []}  # Stats data
        
        # Calculate statistics
        for player, throws in st.session_state.throws.items():
            stats_data["Players"].append(player)
            stats_data["Average Points"].append(sum(throws)/len(throws) if throws else 0)  # Average points
            stats_data["Max Points"].append(max(throws) if throws else 0)  # Max points
        
        stats_df = pd.DataFrame(stats_data).set_index("Players")
        st.write("### Average Points per Throw")
        st.bar_chart(stats_df["Average Points"])  # Average points chart
        st.write("### Max Points in a Single Throw")
        st.bar_chart(stats_df["Max Points"])  # Max points chart
    else:
        current_player = st.session_state.players[st.session_state.turn]  # Current player
        st.image(st.session_state.avatars[current_player], width=100, caption=f"{current_player}'s Avatar")
        st.subheader(f"{current_player}'s turn – Current Score: {st.session_state.scores[current_player]}")

        # Track last turn
        if "last_turn" not in st.session_state:
            st.session_state.last_turn = -1

        # Reset state if turn changed
        if st.session_state.turn != st.session_state.last_turn:
            st.session_state.pop(f"base_score_{current_player}", None)
            st.session_state.pop(f"multiplier_{current_player}", None)
            st.session_state.last_turn = st.session_state.turn
            st.session_state.has_thrown = False

        # Throw confirmation logic
        if not st.session_state.has_thrown:
            base_score_key = f"base_score_{current_player}"
            multiplier_key = f"multiplier_{current_player}"
            base_score = st.selectbox("Base Score", [i for i in range(1, 21)] + [25, 50], key=base_score_key)  # Base score input
            multiplier = st.radio("Multiplier", ["Single", "Double", "Triple"], horizontal=True, key=multiplier_key)  # Multiplier input

            # Confirm throw button
            if st.button("Confirm Throw"):
                # Validate score rules
                if base_score in [25, 50] and multiplier in ["Double", "Triple"]:
                    st.info("Double or Triple is not allowed on 25 or 50. Defaulting to Single.")
                    multiplier = "Single"

                # Calculate points
                points = base_score if multiplier == "Single" else base_score * 2 if multiplier == "Double" else base_score * 3

                # Update score and check for overshoot
                new_score = st.session_state.scores[current_player] - points
                if new_score < 0:
                    st.info("Overshoot! Score remains the same.")
                else:
                    st.session_state.scores[current_player] = new_score  # Update score
                    # Check for winning condition
                    if new_score == 0:
                        if st.session_state.require_double_out and multiplier != "Double":
                            st.info("You need to finish on a Double to win!")  # Validate win condition
                        else:
                            st.session_state.winner = current_player  # Declare winner
                    st.session_state.throws[current_player].append(points)  # Track points
                    st.session_state.has_thrown = True  # Mark thrown
        # Turn switching logic
        if st.session_state.has_thrown:
            if st.button("Next Turn"):
                st.session_state.turn = (st.session_state.turn + 1) % len(st.session_state.players)  # Next player
                st.session_state.has_thrown = False  # Reset throw status
                current_player = st.session_state.players[st.session_state.turn]
                st.session_state.pop(f"base_score_{current_player}", None)  # Clear selections
                st.session_state.pop(f"multiplier_{current_player}", None)
                st.rerun()  # Refresh UI

# Restart behavior
if st.button("Restart"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]  # Clear session state to restart the game
