import os

def save_results(players, winner, filename="resultat.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write("Darts results\n")
        for p in players:
            f.write(f"{p['name']}: {p['score']} pts\n")
            f.write(f"Historic: {p['history']}\n")
        f.write(f"Winner: {winner}\n" + "-"*30 + "\n")

import os

def get_player_stats(player_name, filename="resultat.txt"):
    victories, total = 0, 0

    if not os.path.exists(filename):
        return {'victories': 0, 'total': 0, 'win_percentage': 0}

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_players = []
    for line in lines:
        line = line.strip()

        # New game
        if line.startswith("Résultats du jeu"):
            current_players = []

        # Detecting a player
        elif line.endswith("points") or line.endswith("pts"):
            player_line = line.split(":")[0]
            current_players.append(player_line)

        # End of the game - verification of the winner
        elif line.startswith("Winner:"):
            winner = line.split(":")[1].strip()
            if player_name in current_players:
                total += 1
                if winner == player_name:
                    victories += 1

    win_pct = round((victories / total) * 100, 2) if total else 0
    return {'victories': victories, 'total': total, 'win_percentage': win_pct}
