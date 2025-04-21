from utils import get_player_stats
from tkinter import messagebox
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from game_logic import start_game, process_turn, handle_win
from tkinter import simpledialog
from utils import save_results

current_player_index = 0  # To follow the order of laps
root = None  # Main screen

def start_turns_gui(players):
    global current_player_index
    current_player_index = 0
    ask_for_throws(players)

def ask_for_throws(players):
    global current_player_index

    player = players[current_player_index]
    window = tk.Toplevel()
    window.title(f"{player['name']} - Throw your darts")
    window.attributes('-fullscreen', True)
    window.bind("<Escape>", lambda e: pause_menu(window))

    bg_color = "#1e1e2f"
    fg_color = "#ecf0f1"
    accent_color = "#f1c40f"
    window.configure(bg=bg_color)

    content = tk.Frame(window, bg=bg_color)
    content.pack(expand=True)

    tk.Label(content, text=f"🎯 {player['name']}, enter your 3 throws", font=("Segoe UI", 24, "bold"), bg=bg_color, fg=accent_color).pack(pady=20)

    entries = []
    for i in range(3):
        entry = tk.Entry(content, font=("Segoe UI", 16), width=5, bg="#2c3e50", fg=fg_color, insertbackground=fg_color)
        entry.pack(pady=5)
        entries.append(entry)

    score_label = tk.Label(content, text=f"Remaining score : {player['score']}", font=("Segoe UI", 16), bg=bg_color, fg=accent_color)
    score_label.pack(pady=10)

    def submit_throws():
        try:
            throws = [int(e.get()) for e in entries]
            if any(v < 0 or v > 180 for v in throws):
                raise ValueError
            game_over, score, message = process_turn(player, throws)
            print(f"{player['name']} -> {throws} | {message} | Remaining score : {score}")
            score_label.config(text=f"Score restant : {score}")  # Updating the remaining score 

            if game_over:
                winner = player["name"]
                handle_win(players, winner)
                show_results_gui(players, winner)
            else:
                # Next turn
                global current_player_index
                current_player_index = (current_player_index + 1) % len(players)
                ask_for_throws(players)

        except ValueError:
            tk.Label(content, text="Enter valid numbers.", font=("Segoe UI", 12), fg="#e74c3c", bg=bg_color).pack(pady=5)

    tk.Button(content, text="Confirm", font=("Segoe UI", 16), bg=accent_color, fg=bg_color, command=submit_throws).pack(pady=20)

def start_game_with_gui():
    global root
    root = tk.Tk()
    root.title("DartCompact - Beginning of the game")
    root.attributes('-fullscreen', True)
    root.bind("<Escape>", lambda e: pause_menu(root))  # Use root here

    bg_color = "#1e1e2f"
    fg_color = "#ecf0f1"
    accent_color = "#f1c40f"
    root.configure(bg=bg_color)  # ✅ Use root here

    content_frame = tk.Frame(root, bg=bg_color)
    content_frame.pack(expand=True)

    tk.Label(content_frame, text="Welcome in DartCompact!", font=("Segoe UI", 26, "bold"), bg=bg_color, fg=accent_color).pack(pady=30)
    tk.Label(content_frame, text="How many players will participate ?", font=("Segoe UI", 18), bg=bg_color, fg=fg_color).pack(pady=10)

    num_players_entry = tk.Entry(content_frame, font=("Segoe UI", 16), bg="#2c3e50", fg=fg_color, insertbackground=fg_color)
    num_players_entry.pack(pady=10)

    def submit_num_players():
        try:
            num_players = int(num_players_entry.get())
            if num_players <= 0:
                raise ValueError
        except ValueError:
            tk.Label(content_frame, text="Enter valid numbers", font=("Segoe UI", 12), fg="#e74c3c", bg=bg_color).pack(pady=5)
            return
        root.destroy()  # ✅ Close the main window 
        ask_for_names(num_players)

    tk.Button(content_frame, text="Begin", font=("Segoe UI", 14), bg=accent_color, fg=bg_color, activebackground="#f39c12", command=submit_num_players).pack(pady=20)

    root.mainloop()



def pause_menu(parent):
    global root
    if messagebox.askyesno("Break", "Do you want to leave the game ?"):
        parent.destroy()
        if root:
            root.destroy()


def ask_for_names(num_players):
    window = tk.Toplevel()
    window.title("Entering names")
    window.attributes('-fullscreen', True)
    window.bind("<Escape>", lambda e: pause_menu(window))

    bg_color = "#1e1e2f"
    fg_color = "#ecf0f1"
    accent_color = "#f1c40f"
    window.configure(bg=bg_color)

    content_frame = tk.Frame(window, bg=bg_color)
    content_frame.pack(expand=True)

    tk.Label(content_frame, text="Enter the name of the players :", font=("Segoe UI", 20, "bold"), bg=bg_color, fg=fg_color).pack(pady=20)

    name_entries = []

    def submit_names():
        names = [entry.get() for entry in name_entries]
        if all(names):  # Check that all names are filled in
            window.destroy()  # Closes the name entry window
            players = start_game(names)  # Create players with names
            start_turns_gui(players)  # Start the game rounds
        else:
            tk.Label(content_frame, text="Veuillez remplir tous les noms.", font=("Segoe UI", 12), fg="#e74c3c", bg=bg_color).pack(pady=5)

    # Creating text fields for player names
    for i in range(num_players):
        tk.Label(content_frame, text=f"Nom du joueur {i+1}:", font=("Segoe UI", 14), bg=bg_color, fg=fg_color).pack(pady=5)
        entry = tk.Entry(content_frame, font=("Segoe UI", 14), bg="#2c3e50", fg=fg_color, insertbackground=fg_color)
        entry.pack(pady=5)
        name_entries.append(entry)

    tk.Button(content_frame, text="Start the game", font=("Segoe UI", 14), bg=accent_color, fg=bg_color, activebackground="#f39c12", command=submit_names).pack(pady=20)


def show_results_gui(players, winner):
    window = tk.Toplevel()
    window.title("Results of the Game")
    window.attributes('-fullscreen', True)
    window.bind("<Escape>", lambda e: pause_menu(window))

    bg_color = "#1e1e2f"
    fg_color = "#ecf0f1"
    accent_color = "#2ecc71"
    window.configure(bg=bg_color)

    content_frame = tk.Frame(window, bg=bg_color)
    content_frame.pack(expand=True)

    tk.Label(content_frame, text="🎯 Results of the Game 🎯", font=("Segoe UI", 26, "bold"), bg=bg_color, fg=accent_color).pack(pady=20)

    sorted_players = sorted(players, key=lambda x: x['score'])
    for player in sorted_players:
        tk.Label(content_frame, text=f"{player['name']} : {player['score']} points", font=("Segoe UI", 16), bg=bg_color, fg=fg_color).pack()
        tk.Label(content_frame, text=f"Historic : {player['history']}", font=("Segoe UI", 12, "italic"), bg=bg_color, fg=fg_color).pack()
        tk.Button(content_frame, text="Show my statistics", font=("Segoe UI", 14), bg="#3498db", fg=bg_color, activebackground="#2980b9", command=lambda p=player: show_player_stats(p)).pack(pady=10)

    tk.Label(content_frame, text=f"\nWinner : {winner}", font=("Segoe UI", 20, "bold"), bg=bg_color, fg=accent_color).pack(pady=20)

    tk.Button(content_frame, text="Play again", font=("Segoe UI", 14), bg="#3498db", fg=bg_color, activebackground="#2980b9", command=lambda: [window.destroy(), start_game_with_gui()]).pack(pady=10)

def show_player_stats(player):
    stats = get_player_stats(player['name'])

    stats_window = tk.Toplevel()
    stats_window.title(f"Statistics of {player['name']}")
    stats_window.geometry("600x400")
    stats_window.configure(bg="#1e1e2f")

    tk.Label(stats_window, text=f"📊 Statistics of {player['name']}", font=("Segoe UI", 20, "bold"), fg="#f1c40f", bg="#1e1e2f").pack(pady=20)

    if stats:
        for key, value in stats.items():
            tk.Label(stats_window, text=f"{key} : {value}", font=("Segoe UI", 14), fg="#ecf0f1", bg="#1e1e2f").pack(pady=5)
    else:
        tk.Label(stats_window, text="No available statistics.", font=("Segoe UI", 14), fg="#e74c3c", bg="#1e1e2f").pack(pady=10)

    tk.Button(stats_window, text="Close", font=("Segoe UI", 12), bg="#e74c3c", fg="#ecf0f1", command=stats_window.destroy).pack(pady=20)
