def start_game():
    print("🎯 Welcome on DartCompact!")
if __name__ == "__main__":
    start_game()

def throw_dart(current_score, throw_points):
    if current_score - throw_points < 0:
        print("Overshoot! Score stays the same.")
        return current_score
    return current_score - throw_points

# Starting score for both players
player1_score = 301
player2_score = 301

# Define the number of player with their name
num_players = int(input("Number of players: "))
players = []
for i in range(num_players):
    name = input(f"Enter name for player {i + 1}: ")
    players.append({"name": name, "score": 301})

#Game loop 
winner = None
while not winner:
    for player in players:
        print(f"\n{player['name']}'s turn. Current score: {player['score']}")
        try:
            points = int(input("Enter points scored: "))
        except ValueError:
            print("Invalid input. Try again.")
            continue
        player['score'] = throw_dart(player['score'], points)
        print(f"{player['name']}'s new score: {player['score']}")
        if player['score'] == 0:
            winner = player['name']
            print(f"\n🏆 {winner} wins the game!")
            break

# Save scores
with open(filename, "w") as file:
    file.write("Darts Game Results:\n")
    for player in players:
        file.write(f"{player['name']}: {player['score']}\n")
    file.write(f"Winner: {winner}\n")
    file.write("-" * 30 + "\n")

print(f"\n✅ Scores saved to '{filename}'")
