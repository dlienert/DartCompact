import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend for Streamlit
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

# main.py start


if __name__ == "__main__":
    pass  # GUI code removed for Streamlit compatibility

# main.py end

# game_logic.py start



# === Logic of the game ===
def create_players(players_names):
    return [{"name": name, "score": 301, "history": [], "victories": 0} for name in players_names]

def process_turn(player, throws):
    total_score = sum(throws)
    new_score = player['score'] - total_score

    # ML process (Initialising ML data)
    if 'ml_data' not in st.session_state:
        st.session_state.ml_data = pd.DataFrame(columns=['player', 'avg_throw', 'total_throws', 'current_score', 'max_throw', 'won'])
    
    # ✅ Add throws in historic 
    player['history'].append(throws)

    if new_score < 0:
        message = "Bust! You overpassed your score."
        new_score = player['score']  #Score stays the same if Bust
        game_over = False
    else:
        message = f"Remaining score: {new_score} points"
        game_over = new_score == 0  #Player wins if score == 0

    player['score'] = new_score
    return game_over, new_score, message


def handle_win(players, winner_name):
    save_results(players, winner_name)

def start_game(players_names):
    return create_players(players_names)

# game_logic.py end

#dart_compact.py start


# Multi-player dart game using Streamlit for name input, avatars, and score tracking.

st.set_page_config(page_title="DartCompact 🎯", layout="centered")

st.title("🎯 DartCompact")
st.write("Welcome to the compact dart game for multiple players!!!")

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
            st.rerun()  # ChatGPT fix: replaces deprecated experimental_rerun()
        else:
            st.warning("Please fill in all player names.")  # Warning for missing names

else:
    # Initialize throw tracking
    if "has_thrown" not in st.session_state:
        st.session_state.has_thrown = False

    #ML process (Data added after each run)
    player = st.session_state.players[st.session_state.current_player]
    # Just after updating player[‘score’] and player[‘history’].
    player_data = {
        'player': player['name'],
        'avg_throw': sum(player['history']) / len(player['history']) if player['history'] else 0,
        'total_throws': len(player['history']),
        'current_score': player['score'],
        'max_throw': max(player['history']) if player['history'] else 0,
        'won': 1 if player['score'] == 0 else 0
    }
    st.session_state.ml_data = pd.concat([st.session_state.ml_data, pd.DataFrame([player_data])], ignore_index=True)

    #ML process (Prediction display)
    if 'ml_model' in st.session_state:
        player = st.session_state.players[st.session_state.current_player]
        x_pred = pd.DataFrame([{
            'avg_throw': sum(player['history']) / len(player['history']) if player['history'] else 0,
            'total_throws': len(player['history']),
            'current_score': player['score'],
            'max_throw': max(player['history']) if player['history'] else 0,
        }])
        proba = st.session_state.ml_model.predict_proba(x_pred)[0][1]
        st.markdown(f"### 🤖 Chance estimée de victoire : **{proba*100:.1f}%**")

    # Game over logic
    if st.session_state.winner:
        st.success(f"🏆 {st.session_state.winner} has won the game!")

        #ML Process (Training the model at the end of the game)
        from sklearn.linear_model import LogisticRegression

        df = st.session_state.ml_data
        if df['won'].sum() >= 2:  # We train the model only if we have to completed games 
            X = df[['avg_throw', 'total_throws', 'current_score', 'max_throw']]
            y = df['won']
            model = LogisticRegression()
            model.fit(X, y)
            st.session_state.ml_model = model
        
        # Create final ranking sorted by remaining score
        winner = st.session_state.winner
        others = [p for p in st.session_state.players if p != winner]
        others_sorted = sorted(others, key=lambda p: st.session_state.scores[p])
        ranking = [winner] + others_sorted

        st.markdown("## 🏅 Final Standings")
        # Podium-style layout
        podium_cols = st.columns([1, 1, 1])
        podium_order = [0, 1, 2]  #show 1st, 2nd, 3rd left to right

        for idx, pos in enumerate(podium_order):
            if pos < len(ranking):
                player = ranking[pos]
                with podium_cols[idx]:
                    if pos == 0:
                        st.markdown("🥇 **1st Place**")
                    elif pos == 1:
                        st.markdown("🥈 **2nd Place**")
                    elif pos == 2:
                        st.markdown("🥉 **3rd Place**")
                    st.image(st.session_state.avatars[player], width=100)
                    st.markdown(f"### {player}")

        # Statistics below podium
        st.write("## 📊 Game Statistics")
        stats_data = {"Players": [], "Average Points": [], "Max Points": []}

        for player, throws in st.session_state.throws.items():
            stats_data["Players"].append(player)
            stats_data["Average Points"].append(sum(throws)/len(throws) if throws else 0)
            stats_data["Max Points"].append(max(throws) if throws else 0)

        stats_df = pd.DataFrame(stats_data).set_index("Players")
        st.write("### Average Points per Throw")
        st.bar_chart(stats_df["Average Points"])
        st.write("### Max Points in a Single Throw")
        st.bar_chart(stats_df["Max Points"])
        # Comparison to professional players
        st.write("## 🧠 Compare Yourself to a Pro")
 
        import requests
        
        # Real pro player data via Sportradar API (trial plan uses competitor endpoint)
        pro_player = "Michael van Gerwen"
        pro_competitor_id = "sr:competitor:26280"  # MvG's competitor ID
        API_KEY = "0j9Nj7DIbdznIAKdz6LPFnHWmYChwGUQgboXO76n"
        
        try:
            url = f"https://api.sportradar.com/darts/trial/v2/en/competitors/{pro_competitor_id}/profile.json?api_key={API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Attempt to extract actual stats if available in response
                stats = data.get("statistics", {})
                pro_avg = stats.get("average_3_dart_score", 98.5)
                pro_max = stats.get("best_3_dart_score", 180)
            else:
                st.warning("Couldn't fetch pro data, using defaults.")
        except Exception as e:
            st.error("API call failed.")
 
        for player, throws in st.session_state.throws.items():
            user_avg = sum(throws)/len(throws) if throws else 0
            user_max = max(throws) if throws else 0
 
            st.markdown(f"### {player} vs {pro_player}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="🎯 Your Avg", value=round(user_avg, 1))
                st.metric(label="🔥 Your Max Throw", value=user_max)
            with col2:
                st.metric(label="🏆 Pro Avg", value=pro_avg)
                st.metric(label="🚀 Pro Max Throw", value=pro_max)
 
            # Visual comparison bar
            percent_of_pro = min(user_avg / pro_avg, 1.0)
            st.progress(percent_of_pro)
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
            if "throw_count" not in st.session_state:
                st.session_state.throw_count = 0

        # Throw confirmation logic
        with st.form(key=f"{current_player}_throw_form_{st.session_state.throw_count}", clear_on_submit=True):
            base_score = st.selectbox(
                "Base Score",
                [i for i in range(1, 21)] + [25, 50],
                key=f"base_score_{current_player}_{st.session_state.throw_count}"
            )
            multiplier = st.radio(
                "Multiplier",
                ["Single", "Double", "Triple"],
                horizontal=True,
                key=f"multiplier_{current_player}_{st.session_state.throw_count}"
            )
            submitted = st.form_submit_button("Confirm Throw")

        if submitted and not st.session_state.has_thrown:
            # Validate score rules
            if base_score in [25, 50] and multiplier in ["Double", "Triple"]:
                st.info("Double or Triple is not allowed on 25 or 50. Defaulting to Single.")
                multiplier = "Single"

            # Calculate points
            points = base_score
            if multiplier == "Double":
                points *= 2
            elif multiplier == "Triple":
                points *= 3

            # Update score and handle overshoot or win
            current_score = st.session_state.scores[current_player]
            new_score = current_score - points

            if new_score < 0:
                st.info("Overshoot! Score remains the same.")
            elif new_score == 0:
                if st.session_state.require_double_out and multiplier != "Double":
                    st.info("You need to finish on a Double to win!")
                else:
                    st.session_state.scores[current_player] = 0
                    st.session_state.winner = current_player
                    st.session_state.throws[current_player].append(points)
                    st.session_state.has_thrown = True
                    st.stop()
            else:
                st.session_state.scores[current_player] = new_score
                st.session_state.throws[current_player].append(points)
                st.session_state.throw_count += 1
                if st.session_state.throw_count >= 3:
                    st.session_state.has_thrown = True
                    st.stop()
            st.rerun()  # ChatGPT fix to update score display immediately after confirming a throw

        # Turn switching logic
        if st.session_state.has_thrown:
            if st.button("Next Turn"):
                st.session_state.turn = (st.session_state.turn + 1) % len(st.session_state.players)  # Next player
                st.session_state.has_thrown = False  # Reset throw status
                st.session_state.throw_count = 0
                current_player = st.session_state.players[st.session_state.turn]
                st.session_state.pop(f"base_score_{current_player}", None)  # Clear selections
                st.session_state.pop(f"multiplier_{current_player}", None)
                st.rerun()  # Refresh UI

# Restart behavior
if st.button("Restart"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]  # Clear session state to restart the game
    st.rerun()  # ChatGPT fix: immediately refresh UI after restart

# dart_compact.py end
