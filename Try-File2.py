# Import required libraries
import matplotlib  # Library for creating data visualizations and charts
matplotlib.use('Agg')  # Force matplotlib to use non-interactive 'Agg' backend - necessary for Streamlit to avoid conflicts with its rendering system
import matplotlib.pyplot as plt  # Import the pyplot module specifically, which provides MATLAB-like plotting interface for creating charts
import streamlit as st  # Import Streamlit, the web app framework that turns data scripts into shareable web apps
import pandas as pd  # Import pandas for data manipulation - provides DataFrame objects that make data analysis easier
import numpy as np  # Import numpy for numerical operations - needed for array manipulations and mathematical functions
from sklearn.linear_model import LogisticRegression  # Import LogisticRegression for win/loss prediction - chosen because it works well for binary classification
import requests  # Import requests library to make HTTP calls to external APIs (used for fetching pro player data)

# Configure the Streamlit page settings - must be called before any other Streamlit function
st.set_page_config(
    page_title='DartCompact 🎯',  # Set browser tab title with dart emoji for branding
    layout='centered'  # Use centered layout (vs 'wide') for better readability on various devices
)

# Game logic functions - These functions handle the core dart game mechanics

def create_players(players_names):
    """Create a list of player dictionaries with initial values"""
    # Using list comprehension for efficiency - creates a dictionary for each player in a single line
    # Dictionary structure with multiple properties enables easy tracking of various player attributes
    # - name: Player's display name (string)
    # - score: Starting score (301 is standard for casual darts)
    # - history: Empty list that will store throw history for analysis
    # - victories: Counter for total wins (for potential future feature)
    return [{'name': name, 'score': 301, 'history': [], 'victories': 0} for name in players_names]

def process_turn(player, throws):
    """Process a player's turn and update their score based on throws"""
    # Calculate total points for this turn by summing all throw values
    total_score = sum(throws)  # Using sum() is more concise than manual addition in a loop
    
    # Calculate new score by subtracting current turn's points from player's current score
    # Dart scoring is subtractive - players start with a score and decrease to zero
    new_score = player['score'] - total_score
    
    # Make sure ML data structure exists in session state
    # This check prevents errors if the function is called before ML structure initialization
    if 'ml_data' not in st.session_state:
        # Create empty DataFrame with specific columns for ML training data
        # Column structure designed to capture relevant features for win prediction
        st.session_state.ml_data = pd.DataFrame(columns=[
            'player',        # Player name (string) - for grouping and identification
            'avg_throw',     # Average throw score (float) - key predictor of skill
            'total_throws',  # Total number of throws (int) - measures experience in this game
            'current_score', # Remaining score (int) - proximity to winning
            'max_throw',     # Best throw (int) - indicator of peak performance
            'won'            # Whether player won (binary) - target variable for ML
        ])
    
    # Record this turn's throws in player history for later analysis
    # Append to the list rather than overwriting to maintain complete game history
    player['history'].append(throws)
    
    # Handle different scoring scenarios according to dart rules
    if new_score < 0:
        # BUST case: Player went below zero (overshoot scenario)
        message = 'Bust! You overpassed your score.'  # Informative message for player
        new_score = player['score']  # Score stays the same if the player busts - standard dart rule
        game_over = False  # Game continues after a bust
    else:
        # Normal scoring case or potential win
        message = f'Remaining score: {new_score} points'  # Feedback on remaining points
        game_over = new_score == 0  # Game is over only when score is exactly zero - standard dart rule
    
    # Update player's score in the player object
    # Must be done after all checks to avoid premature score updates
    player['score'] = new_score
    
    # Return multiple values as a tuple for flexibility in the calling code
    # - game_over: Boolean flag to indicate if player has won
    # - new_score: Updated score for display and further game logic
    # - message: Feedback text to show the player
    return game_over, new_score, message

# Multi-player dart game using Streamlit for name input, avatars, and score tracking
# Each section of the app is clearly separated for maintenance and readability

# App title and welcome message
st.title('🎯 DartCompact')  # Use an emoji in the title for visual appeal and quick recognition
st.write('Welcome to the compact dart game for multiple players!')  # Brief welcome message explains app purpose

# Session state initialisation
# Streamlit's session_state persists variables between reruns - essential for game state management

# Initialize session state variables only once (when the app first loads)
# This conditional check prevents resetting variables on page reloads, which would lose game state
if 'players' not in st.session_state:
    # All key game state variables are initialized here to avoid "key not found" errors later
    st.session_state.players = []  # List to store player names - empty until game setup
    st.session_state.scores = {}   # Dictionary mapping player names to scores - empty until game setup
    st.session_state.winner = None  # Will store winner's name when someone wins - None indicates no winner yet
    st.session_state.game_started = False  # Flag to control UI flow - False shows setup screen, True shows game UI
    st.session_state.game_count = 0  # Counter for total completed games - used for statistics and ML training
    
    # DataFrame to store player performance data for ML training
    # Using pandas DataFrame for ML data offers flexible data manipulation capabilities
    # Empty DataFrame with predefined columns ensures consistent data structure
    st.session_state.ml_data = pd.DataFrame(columns=[
        'player',        # Player identification 
        'avg_throw',     # Average points per throw - measures consistency
        'total_throws',  # Number of throws made - measures game progress
        'current_score', # Remaining score - measures proximity to winning
        'max_throw',     # Maximum points scored in a single throw - measures skill ceiling
        'won'            # Binary outcome (0/1) - target variable for ML model
    ])

# Game setup UI
# This section is only shown when no game is in progress (game_started = False)
# Contains all the inputs needed to configure and start a new game
    
# Show setup UI when no game is in progress
if not st.session_state.game_started:
    # Input for selecting number of players (1-8)
    # number_input provides integer selection with increment buttons
    # min_value=1 ensures at least one player, max_value=8 prevents overcrowding
    num_players = st.number_input('Number of players', min_value=1, max_value=8, step=1)
    
    # Toggle for requiring a double to win (standard darts rule)
    # checkbox provides a simple boolean toggle with default=False
    # This implements the standard "double-out" rule in darts where players must hit a double to win
    require_double_out = st.checkbox('Require double to win', value=False)
    
    # Select starting score (standard options in darts)
    # selectbox provides a dropdown with predefined options
    # 301 is selected by default (index=1) as it's the most common format for casual games
    starting_score = st.selectbox('Select starting score', [101, 301, 501], index=1)

    # Initialize arrays for player data collection
    player_names = []  # Will hold the names entered by user - separate from session state until game starts
    avatars = {}  # Will map player names to their avatar URLs - for visual player identification
    
    # Available avatar options (using Dicebear API)
    # Limited options make selection simpler and ensure consistency
    options = ['Kim', 'Alexis', 'Robyn', 'Billie', 'Lou', 'Charlie']

    # Create text inputs for each player's name
    # Loop generates the right number of input fields based on num_players selection
    for i in range(num_players):
        # text_input creates a single-line text field for name entry
        # Unique key prevents conflicts when multiple inputs exist
        name = st.text_input(f'Name of Player {i+1}', key=f'name_{i}')
        player_names.append(name)  # Add to temporary list until game starts

    # Let each player select an avatar
    # Separate loop from name entry to ensure all names are collected first
    for i, name in enumerate(player_names):
        # radio creates a set of mutually exclusive options with horizontal layout
        # Each player gets their own set of options with a unique key
        avatar_choice = st.radio(f'Choose avatar for Player {i+1}', options=options, horizontal=True, key=f'avatar_choice_{i}')
        
        # Generate avatar URL using dicebear API
        # This free API generates consistent avatars based on the seed value
        # Using _default suffix ensures consistent style across avatars
        avatar_url = f'https://api.dicebear.com/7.x/adventurer/svg?seed={avatar_choice}_default'
        
        # Display avatar preview so players can see their selection
        # width=100 keeps the avatar reasonably sized on the page
        st.image(avatar_url, width=100)
        
        # Store avatar URL in dictionary, mapped to player name
        # This creates {name: url} pairs for easy retrieval during gameplay
        avatars[name] = avatar_url
        
    # Save all avatars to session state for use throughout the game
    # Doing this here ensures all avatars are set before the game starts
    st.session_state.avatars = avatars

    # Game start button and logic 
    # Button that triggers game initialization when clicked
    if st.button('Start Game'):
        # Validate that all players have names
        # This prevents starting a game with unnamed players, which would cause issues
        if all(name.strip() != '' for name in player_names):
            # Store finalized player data in session state
            st.session_state.players = player_names  # List of player names in turn order
            st.session_state.scores = {name: starting_score for name in player_names}  # Initial scores dictionary
            st.session_state.throws = {name: [] for name in player_names}  # Empty throw history for each player
            st.session_state.turn = 0  # First player's turn (index 0)
            st.session_state.game_started = True  # Flag game as started to switch to game UI
            st.session_state.require_double_out = require_double_out  # Store double-out rule setting
            
            # Update game counter for statistics tracking
            # Increment rather than set to ensure accurate count across multiple games
            st.session_state.game_count += 1
            st.success(f'Starting game #{st.session_state.game_count}')  # Success message with game number
            
            # ML model training
            # Only train model if we have at least 2 games of data
            # This ensures enough data points for meaningful patterns
            if st.session_state.game_count >= 2:
                try:
                    # Get all collected ML data from previous games
                    df = st.session_state.ml_data
                    
                    # Only train if we have enough data and examples of both outcomes
                    # Need at least 10 data points for minimal statistical significance
                    # Need both positive and negative cases (won=0, won=1) for classification
                    if len(df) >= 10 and len(set(df['won'])) > 1:
                        # Prepare features (X) and target (y)
                        # Apply pd.to_numeric to ensure all features are properly converted to numbers
                        # errors='coerce' handles any non-numeric values by converting them to NaN
                        X = df[['avg_throw', 'total_throws', 'current_score', 'max_throw']].apply(pd.to_numeric, errors='coerce')
                        
                        # Convert target to integer type (0 or 1) for binary classification
                        y = df['won'].astype(int)
                        
                        # Create and train logistic regression model
                        # LogisticRegression is used because:
                        # 1. It works well for binary classification (win/lose)
                        # 2. It can provide probability estimates
                        # 3. It's relatively simple and interpretable
                        # solver='liblinear' is good for small datasets
                        model = LogisticRegression(solver='liblinear')
                        model.fit(X, y)  # Train model with features and target
                        
                        # Store trained model in session state for later use
                        st.session_state.ml_model = model
                        st.success('ML model trained successfully!')  # Success message
                except Exception as e:
                    # Catch and display any errors during training
                    # This prevents crashes if something goes wrong with the ML process
                    st.error(f'Error training ML model: {e}')
                
            # Refresh UI to show game interface
            # rerun() is more reliable than update() for complete UI refresh
            st.rerun()
        else:
            # Show warning if any player name is empty
            # This prevents starting a game with unnamed players
            st.warning('Please fill in all player names')

else:
    # Game play ui
    
    # Initialize throw tracking variables if needed
    if 'has_thrown' not in st.session_state:
        st.session_state.has_thrown = False  # Tracks if current player completed their throws
    if 'throw_count' not in st.session_state:
        st.session_state.throw_count = 0  # Counts how many throws current player has made (max 3)

    # Get current player's data for this turn
    player_name = st.session_state.players[st.session_state.turn]  # Get name of current player
    player_throws = st.session_state.throws[player_name]  # Get throw history for this player
    current_score = st.session_state.scores[player_name]  # Get current score for this player
    
    # ML data collection
    
    # Only track ML data after player has made at least one throw (to avoid empty data)
    if player_throws:
        # Create data point with player's current performance metrics
        player_data = {
            'player': player_name,  # Player name
            'avg_throw': sum(player_throws) / len(player_throws),  # Average points per throw
            'total_throws': len(player_throws),  # Total number of throws made
            'current_score': current_score,  # Current remaining score
            'max_throw': max(player_throws),  # Highest scoring throw
            'won': 0  # Initially marked as not won (will be updated to 1 if they win)
        }
        # Add to ML dataset for training
        st.session_state.ml_data = pd.concat([st.session_state.ml_data, pd.DataFrame([player_data])], ignore_index=True)

    # Game over screen
    
    # Check if we have a winner and display end-game UI
    if st.session_state.winner:
        # Show winner announcement
        st.success(f'🏆 {st.session_state.winner} has won the game!')
        
        # Process winner data only once to avoid duplicating entries
        if 'winner_processed' not in st.session_state:
            st.session_state.winner_processed = True  # Flag to prevent re-processing
            
            # ML model update with winner data
            try:
                df = st.session_state.ml_data
                # Need sufficient data and both win/loss examples to train
                if len(df) >= 10 and len(set(df['won'])) > 1:
                    # Prepare features and target
                    X = df[['avg_throw', 'total_throws', 'current_score', 'max_throw']].apply(pd.to_numeric, errors='coerce')
                    y = df['won'].astype(int)
                    # Create and train model
                    model = LogisticRegression(solver='liblinear')
                    model.fit(X, y)
                    # Store model in session state
                    st.session_state.ml_model = model
                    st.success('ML model trained successfully!')
            except Exception as e:
                st.error(f'Error training ML model: {e}')

        # Final standings 
        
        # Create player ranking for final standings
        winner = st.session_state.winner  # Get winner's name
        others = [p for p in st.session_state.players if p != winner]  # All other players
        # Sort other players by score (lower score is better)
        others_sorted = sorted(others, key=lambda p: st.session_state.scores[p])
        # Final ranking with winner first, then others sorted by score
        ranking = [winner] + others_sorted

        # Display podium with medals
        st.markdown('## 🏅 Final Standings')
        podium_cols = st.columns([1, 1, 1])  # Create 3 columns for podium display
        podium_order = [0, 1, 2]  # Positions for 1st, 2nd, 3rd place

        # Display each player on the podium
        for idx, pos in enumerate(podium_order):
            if pos < len(ranking):  # Only process if we have enough players
                player = ranking[pos]
                with podium_cols[idx]:
                    # Show appropriate medal based on position
                    medal = '🥇 **1st Place**' if pos == 0 else '🥈 **2nd Place**' if pos == 1 else '🥉 **3rd Place**'
                    st.markdown(medal)
                    # Display player avatar and name
                    st.image(st.session_state.avatars[player], width=100)
                    st.markdown(f'### {player}')
        
        # Game statistics

        # Show game statistics for all players
        st.write('## 📊 Game Statistics')
        stats_data = {'Players': [], 'Average Points': [], 'Max Points': []}

        # Collect statistics from each player's throws
        for player, throws in st.session_state.throws.items():
            if throws:  # Only include players who made throws
                stats_data['Players'].append(player)
                stats_data['Average Points'].append(sum(throws)/len(throws))
                stats_data['Max Points'].append(max(throws))

        # Create visualizations if we have data
        if stats_data['Players']:
            # Convert to DataFrame for charting
            stats_df = pd.DataFrame(stats_data).set_index('Players')
            # Show average points chart
            st.write('### Average Points per Throw')
            st.bar_chart(stats_df["Average Points"])
            # Show max points chart
            st.write('### Max Points in a Single Throw')
            st.bar_chart(stats_df['Max Points'])
        
        # ML model insights
        
        # Display ML insights if model exists and we have enough data
        if 'ml_model' in st.session_state and len(st.session_state.ml_data) > 5:
            st.markdown("## 🧠 ML Model Insights")
            
            # Get list of all unique players from ML data
            all_players = list(set(st.session_state.ml_data['player'].values))
            
            # Aggregate player statistics by grouping ML data
            player_stats = st.session_state.ml_data.groupby('player').agg({
                'won': 'sum',  # Count total wins
                'avg_throw': 'mean',  # Average score per throw
                'total_throws': 'sum',  # Total throws made
                'max_throw': 'max'  # Maximum throw score
            }).reset_index()
            
            # Player performance stats
            
            st.write('### Player performance')
            
            # Extract win counts for each player
            win_counts = {row['player']: row['won'] for _, row in player_stats.iterrows()}
            
            # Initialize tracking for games played per player
            if 'player_games' not in st.session_state:
                st.session_state.player_games = {player: 0 for player in all_players}
            
            # Calculate games played for win rate calculation
            # Use total game count as each player is assumed to have played all games
            games_played = {player: max(1, st.session_state.game_count) for player in all_players}
            
            # Create data for player statistics table
            display_data = []
            for player in all_players:
                # Only include players with statistics
                if player in player_stats['player'].values:
                    # Get player's average score, max score, and win count
                    avg_score = player_stats[player_stats['player'] == player]['avg_throw'].values[0]
                    max_score = player_stats[player_stats['player'] == player]['max_throw'].values[0]
                    wins = win_counts.get(player, 0)
                    
                    # Calculate win percentage 
                    win_rate = (wins / games_played[player]) * 100
                    
                    # Add player stats to display data
                    display_data.append({
                        'player': player,
                        'Wins': wins,  # Number of games won
                        'Win Rate %': win_rate,  # Percentage of games won
                        'Avg Score': round(avg_score, 1),  # Average score per throw (rounded)
                        'Best Throw': int(max_score),  # Highest scoring throw
                    })
            
            # Display player statistics table if data exists
            if display_data:
                # Convert to DataFrame for display
                display_df = pd.DataFrame(display_data).set_index('player')
                # Explain win rate calculation
                st.info('Win rate calculated based on total completed games')
                # Show player statistics table
                st.dataframe(display_df)
            else:
                st.write('No player statistics available yet.')
        
        # Pro player comparison
        
        st.write('## Compare yourself to a Pro')
        # Pro player details
        pro_player = 'Michael van Gerwen'  # Famous professional dart player
        pro_competitor_id = 'sr:competitor:26280'  # API ID for this player
        API_KEY = "0j9Nj7DIbdznIAKdz6LPFnHWmYChwGUQgboXO76n"  # Sportradar API key
        
        # Default pro player statistics (used if API fails)
        pro_avg = 98.5  # Pro average score per throw
        pro_max = 180   # Pro maximum score (perfect throw)
        
        # Try to fetch real pro data from API
        try:
            # Build API request URL
            url = f'https://api.sportradar.com/darts/trial/v2/en/competitors/{pro_competitor_id}/profile.json?api_key={API_KEY}'
            # Make API request with timeout
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                # Parse JSON response
                data = response.json()
                # Extract statistics
                stats = data.get('statistics', {})
                # Get average and max scores (use defaults if not found)
                pro_avg = stats.get('average_3_dart_score', pro_avg)
                pro_max = stats.get('best_3_dart_score', pro_max)
        except Exception as e:
            # Log error but continue with default values
            st.warning(f'Could not fetch pro data: {str(e)}. Using default values.')
 
        # Compare each player to the pro
        for player, throws in st.session_state.throws.items():
            if throws:  # Only show for players who made throws
                # Calculate player's average and max scores
                user_avg = sum(throws)/len(throws)
                user_max = max(throws)
 
                # Display comparison UI
                st.markdown(f'### {player} vs {pro_player}')
                col1, col2 = st.columns(2)  # Create two columns for side-by-side comparison
                # Show player's stats in left column
                with col1:
                    st.metric(label='🎯 Your Avg', value=round(user_avg, 1))
                    st.metric(label='🔥 Your Max Throw', value=user_max)
                # Show pro's stats in right column
                with col2:
                    st.metric(label='🏆 Pro Avg', value=round(pro_avg, 1))
                    st.metric(label='🚀 Pro Max Throw', value=pro_max)
 
                # Visual comparison with progress bar
                if pro_avg > 0:  # Avoid division by zero
                    # Calculate how close player is to pro level (capped at 100%)
                    percent_of_pro = min(user_avg / pro_avg, 1.0)
                    # Display progress bar showing comparison
                    st.progress(percent_of_pro)
                    # Show percentage text
                    st.caption(f"You're at {percent_of_pro*100:.1f}% of professional level")
    
    # Active game ui 
    
    # Show game interface for current player when game is in progress (no winner yet)
    else:
        # Get current player information
        current_player = st.session_state.players[st.session_state.turn]
        # Display player avatar and current score
        st.image(st.session_state.avatars[current_player], width=100, caption=f"{current_player}'s Avatar")
        st.subheader(f"{current_player}'s turn – Current Score: {st.session_state.scores[current_player]}")

        # Track player turns to reset state when player changes
        if 'last_turn' not in st.session_state:
            st.session_state.last_turn = -1  # Initialize to invalid turn number

        # Reset player state when turn changes to a new player
        if st.session_state.turn != st.session_state.last_turn:
            # Clear previous throw selection values
            st.session_state.pop(f'base_score_{current_player}', None)
            st.session_state.pop(f'multiplier_{current_player}', None)
            # Update turn tracker
            st.session_state.last_turn = st.session_state.turn
            # Reset throw state for new player
            st.session_state.has_thrown = False
            st.session_state.throw_count = 0

        # Throw input form
        
        # Form for player to input their throw details
        with st.form(key=f'{current_player}_throw_form_{st.session_state.throw_count}', clear_on_submit=True):
            # Base score selection (dart board numbers)
            base_score = st.selectbox(
                'Base Score',
                [0] + [i for i in range(1, 21)] + [25, 50],  # 0-20, plus 25 (outer bull) and 50 (bullseye)
                key=f'base_score_{current_player}_{st.session_state.throw_count}'
            )
            # Multiplier selection (single, double, triple)
            multiplier = st.radio(
                'Multiplier',
                ['Single', 'Double', 'Triple'],
                horizontal=True,
                key=f'multiplier_{current_player}_{st.session_state.throw_count}'
            )
            # Submit button
            submitted = st.form_submit_button('Confirm Throw')

        # Throw processing 

        # Process the throw if form was submitted and turn is not complete
        if submitted and not st.session_state.has_thrown:
            # Validate dart rules: 25 and 50 can only be hit as singles (no double/triple bulls)
            if base_score in [25, 50] and multiplier in ['Double', 'Triple']:
                st.info('Double or Triple is not allowed on 25 or 50. Using Single.')
                multiplier = 'Single'

            # Calculate points based on base score and multiplier
            points = base_score * (1 if multiplier == 'Single' else 2 if multiplier == 'Double' else 3)

            # Update score and handle game logic
            current_score = st.session_state.scores[current_player]
            new_score = current_score - points  # Subtract points from current score

            # Score scenarios 

            # Handle bust (score below 0)
            if new_score < 0:
                st.info('Overshoot! Your score remains the same')
                st.session_state.throws[current_player].append(0)  # Record zero for overshoot
                st.session_state.throw_count += 1
                if st.session_state.throw_count >= 3:  # Check if turn is complete (3 throws)
                    st.session_state.has_thrown = True
            # Handle exact zero (potential win)
            elif new_score == 0:
                # Check double-out rule if enabled
                if st.session_state.require_double_out and multiplier != 'Double':
                    st.info('You need to finish on a Double to win!')
                    st.session_state.throws[current_player].append(0)  # Record zero for invalid finish
                    st.session_state.throw_count += 1
                    if st.session_state.throw_count >= 3:  # Check if turn is complete
                        st.session_state.has_thrown = True
                else:
                    # Player wins!
                    st.session_state.scores[current_player] = 0
                    st.session_state.winner = current_player  # Set winner
                    st.session_state.throws[current_player].append(points)  # Record winning throw
                    
                    # Update ML data to mark this player as the winner
                    winner_entries = st.session_state.ml_data[st.session_state.ml_data['player'] == current_player]
                    if not winner_entries.empty:
                        # Find most recent entry for this player and mark as win
                        last_entry_idx = winner_entries.index[-1]
                        st.session_state.ml_data.at[last_entry_idx, 'won'] = 1
                    
                    st.session_state.has_thrown = True
                    st.rerun()  # Refresh UI to show win screen
            # Handle normal score update
            else:
                # Update player's score with new value
                st.session_state.scores[current_player] = new_score
                # Record this throw in player's history
                st.session_state.throws[current_player].append(points)
                # Increment throw counter
                st.session_state.throw_count += 1
                # Check if player has completed their 3 throws
                if st.session_state.throw_count >= 3:
                    st.session_state.has_thrown = True
            
            # Refresh UI if needed (for showing next throw input)
            if not st.session_state.has_thrown:
                st.rerun()

        # Next turn button 
        
        # Show next turn button when current player has completed their throws
        if st.session_state.has_thrown:
            if st.button('Next turn'):
                # Move to next player (cycle back to first player after last)
                st.session_state.turn = (st.session_state.turn + 1) % len(st.session_state.players)
                # Reset throw state for next player
                st.session_state.has_thrown = False
                st.session_state.throw_count = 0
                # Get the next player
                current_player = st.session_state.players[st.session_state.turn]
                # Clear previous throw selections
                st.session_state.pop(f'base_score_{current_player}', None)
                st.session_state.pop(f'multiplier_{current_player}', None)
                # Refresh UI for next player
                st.rerun()

# Restart game button

# Button to restart the game while preserving ML data
if st.button('Restart Game'):
    # Save important data before clearing session state
    saved_ml_data = st.session_state.ml_data.copy() if 'ml_data' in st.session_state else pd.DataFrame(
        columns=['player', 'avg_throw', 'total_throws', 'current_score', 'max_throw', 'won'])
    saved_game_count = st.session_state.game_count if 'game_count' in st.session_state else 0
    saved_ml_model = st.session_state.ml_model if 'ml_model' in st.session_state else None
    
    # Identify keys to preserve (related to ML)
    keys_to_keep = ['ml_data', 'game_count', 'ml_model']
    # Identify keys to clear (everything else)
    keys_to_clear = [k for k in st.session_state.keys() if k not in keys_to_keep]
    
    # Clear session state except for ML-related data
    for key in keys_to_clear:
        del st.session_state[key]
    
    # Restore saved ML data
    st.session_state.ml_data = saved_ml_data
    st.session_state.game_count = saved_game_count
    if saved_ml_model is not None:
        st.session_state.ml_model = saved_ml_model
        
    # Show success message with game count
    st.success(f"Game reset! You've played {saved_game_count} games so far.")
    # Refresh UI to show setup screen
    st.rerun()
