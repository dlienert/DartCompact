import os

def save_results(players, winner, filename="resultat.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write("Résultats du jeu de fléchettes\n")
        for p in players:
            f.write(f"{p['name']}: {p['score']} pts\n")
            f.write(f"Historique: {p['history']}\n")
        f.write(f"Gagnant: {winner}\n" + "-"*30 + "\n")

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

        # Nouvelle partie
        if line.startswith("Résultats du jeu"):
            current_players = []

        # Détecter un joueur
        elif line.endswith("points") or line.endswith("pts"):
            player_line = line.split(":")[0]
            current_players.append(player_line)

        # Fin de la partie - vérification du gagnant
        elif line.startswith("Gagnant:"):
            winner = line.split(":")[1].strip()
            if player_name in current_players:
                total += 1
                if winner == player_name:
                    victories += 1

    win_pct = round((victories / total) * 100, 2) if total else 0
    return {'victories': victories, 'total': total, 'win_percentage': win_pct}
