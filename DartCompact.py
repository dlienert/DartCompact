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
    require_double_out = st.checkbox("Require double to win (Double Out Rule)", value=True)

    for i in range(num_players):
        name = st.text_input(f"Name of Player {i+1}", key=f"name_{i}")
        player_names.append(name)

    avatars = {}
    options = ["confused", "funny", "dizzy", "sad", "angry", "handsome"]
    for name in player_names:
        avatar_choice = st.radio(f"Choose avatar for {name}", options=options, horizontal=True, key=f"avatar_choice_{name}")
        avatar_url = f"https://api.dicebear.com/7.x/adventurer/svg?seed={avatar_choice}_{name}"
        st.image(avatar_url, width=100)
        avatars[name] = avatar_url
    st.session_state.avatars = avatars

    if st.button("Start Game"):
        if all(name.strip() != "" for name in player_names):
            st.session_state.players = player_names
            st.session_state.scores = {name: 301 for name in player_names}
            st.session_state.turn = 0
            st.session_state.game_started = True
            st.session_state.require_double_out = require_double_out
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
        st.image(st.session_state.avatars[current_player], width=100, caption=f"{current_player}'s Avatar")
        st.subheader(f"{current_player}'s turn – Current Score: {st.session_state.scores[current_player]}")

        base_score = st.selectbox("Base Score", [i for i in range(1, 21)] + [25, 50], key="base_score")
        multiplier = st.radio("Multiplier", ["Single", "Double", "Triple"], horizontal=True, key="multiplier")

        if st.button("Confirm Throw"):
            if base_score in [25, 50] and multiplier in ["Double", "Triple"]:
                st.info("Double or Triple is not allowed on 25 or 50. Defaulting to Single.")
                multiplier = "Single"

            if multiplier == "Single":
                points = base_score
            elif multiplier == "Double":
                points = base_score * 2
            else:
                points = base_score * 3

            new_score = st.session_state.scores[current_player] - points
            if new_score < 0:
                st.info("Overshoot! Score remains the same.")
            else:
                st.session_state.scores[current_player] = new_score
                if new_score == 0:
                    if st.session_state.require_double_out and multiplier != "Double":
                        st.info("You need to finish on a Double to win!")
                    else:
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
