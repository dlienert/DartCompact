import streamlit as st
import pandas as pd

st.set_page_config(page_title="DartCompact 🎯", layout="centered")

st.title("🎯 DartCompact")
st.write("Welcome to the compact dart game for multiple players!")

# Initialize players
if "players" not in st.session_state:
    st.session_state.players = []
    st.session_state.scores = {}
    st.session_state.winner = None
    st.session_state.game_started = False

if not st.session_state.game_started:
    num_players = st.number_input("Number of players", min_value=1, max_value=8, step=1)
    player_names = []

    for i in range(num_players):
        name = st.text_input(f"Name of Player {i+1}", key=f"name_{i}")
        player_names.append(name)

    if st.button("Start Game"):
        if all(name.strip() != "" for name in player_names):
            st.session_state.players = player_names
            st.session_state.scores = {name: 301 for name in player_names}
            st.session_state.turn = 0
            st.session_state.game_started = True
        else:
            st.warning("Please fill in all player names.")

else:
    if st.session_state.winner:
        st.success(f"🏆 {st.session_state.winner} has won the game!")
        
        # Show final stats
        st.write("## Game Statistics")
        
        if "throws" not in st.session_state:
            st.session_state.throws = {name: [] for name in st.session_state.players}
        
        stats_data = {
            "Players": [],
            "Average Points": [],
            "Max Points": []
        }
        
        for player, throws in st.session_state.throws.items():
            stats_data["Players"].append(player)
            stats_data["Average Points"].append(sum(throws)/len(throws) if throws else 0)
            stats_data["Max Points"].append(max(throws) if throws else 0)
        
        stats_df = pd.DataFrame(stats_data).set_index("Players")
        
        st.write("### Average Points per Throw")
        st.bar_chart(stats_df["Average Points"])
        
        st.write("### Max Points in a Single Throw")
        st.bar_chart(stats_df["Max Points"])
    else:
        current_player = st.session_state.players[st.session_state.turn]
        st.subheader(f"{current_player}'s turn – Current Score: {st.session_state.scores[current_player]}")

        points = st.number_input("Enter points", min_value=0, max_value=180, step=1, key="throw_points")

        if st.button("Confirm Throw"):
            new_score = st.session_state.scores[current_player] - points
            if new_score < 0:
                st.info("Overshoot! Score remains the same.")
            else:
                st.session_state.scores[current_player] = new_score
                if new_score == 0:
                    st.session_state.winner = current_player
                # Record the throw
                if "throws" not in st.session_state:
                    st.session_state.throws = {name: [] for name in st.session_state.players}
                st.session_state.throws[current_player].append(points)
            st.session_state.turn = (st.session_state.turn + 1) % len(st.session_state.players)

    

# Restart option
if st.button("Restart"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
