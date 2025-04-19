from gui import start_game_with_gui, ask_for_names
from game_logic import start_game

def start_app():
    def on_names_collected(names):
        players = start_game(names)  # Appel à start_game avec les noms collectés
        print(f"Jeu démarré avec les joueurs : {players}")  # Pour debug
        # Lancer la partie ou effectuer d'autres actions

    ask_for_names(num_players=2, on_start=on_names_collected)  # adapt as needed

if __name__ == "__main__":
    start_game_with_gui()  # Démarre directement l'UI du jeu
