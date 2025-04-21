# game_logic.py

from utils import save_results

# === Logic of the game ===
def create_players(players_names):
    return [{"name": name, "score": 301, "history": [], "victories": 0} for name in players_names]

def process_turn(player, throws):
    total_score = sum(throws)
    new_score = player['score'] - total_score

    # ✅ Add throws in historic 
    player['history'].append(throws)

    if new_score < 0:
        message = "Bust! You overpassed your score."
        new_score = player['score']  #Score stays the same if Bust
        game_over = False
    else:
        message = f"Score restant : {new_score} points"
        game_over = new_score == 0  #Player wins if score == 0

    player['score'] = new_score
    return game_over, new_score, message


def handle_win(players, winner_name):
    save_results(players, winner_name)

def start_game(players_names):
    return create_players(players_names)
