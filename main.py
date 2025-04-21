from gui import start_game_with_gui, ask_for_names
from game_logic import start_game

def start_app():
    def on_names_collected(names):
        players = start_game(names)  # Call to start_game with collected names
        print(f"Jeu démarré avec les joueurs : {players}")  # For debug
        # Start the game or perform other actions

    ask_for_names(num_players=2, on_start=on_names_collected)  # adapt as needed

if __name__ == "__main__":
    start_game_with_gui()  # Starts the game's UI directly
