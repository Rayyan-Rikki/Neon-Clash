from flask import Flask, render_template, jsonify, request
import random

app = Flask(__name__)

# Store the game state
game_state = {
    'board': ['' for _ in range(9)],
    'current_player': 'X',
    'game_over': False,
    'mode': 'player',  # 'player' or 'bot'
    'bot_difficulty': 'easy',  # 'easy', 'medium', or 'hard'
    'coins': 0,
    'current_skin': 'default'  # 'default' or 'fire'
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/play/<int:position>', methods=['POST'])
def play(position):
    if game_state['game_over'] or position < 0 or position > 8 or game_state['board'][position] != '':
        return jsonify({'error': 'Invalid move'}), 400
    
    # Make the move for current player
    game_state['board'][position] = game_state['current_player']
    
    # Check for winner
    winner = check_winner()
    if winner or is_board_full():
        game_state['game_over'] = True
        # Add coins if player (X) wins against bot
        if winner == 'X' and game_state['mode'] == 'bot':
            coins_to_add = {
                'easy': 5,
                'medium': 10,
                'hard': 15
            }.get(game_state['bot_difficulty'], 0)
            game_state['coins'] += coins_to_add
            
        return jsonify({
            'board': game_state['board'],
            'winner': winner if winner else 'draw',
            'game_over': True,
            'coins': game_state['coins']
        })

    # If it's player mode or no winner yet, switch players
    if game_state['mode'] == 'player':
        game_state['current_player'] = 'O' if game_state['current_player'] == 'X' else 'X'
        return jsonify({
            'board': game_state['board'],
            'current_player': game_state['current_player']
        })
    
    # Bot mode logic (only if no winner yet)
    elif game_state['mode'] == 'bot':
        bot_position = make_bot_move()
        if bot_position is not None:
            game_state['board'][bot_position] = 'O'
            
            # Check if bot won
            winner = check_winner()
            if winner or is_board_full():
                game_state['game_over'] = True
                return jsonify({
                    'board': game_state['board'],
                    'winner': winner if winner else 'draw',
                    'game_over': True
                })
    
    return jsonify({
        'board': game_state['board'],
        'current_player': game_state['current_player']
    })

@app.route('/set_mode/<mode>', methods=['POST'])
def set_mode(mode):
    if mode in ['player', 'bot']:
        game_state['mode'] = mode
        reset_game()
        return jsonify({'message': f'Mode set to {mode}'})
    return jsonify({'error': 'Invalid mode'}), 400

@app.route('/reset', methods=['POST'])
def reset():
    reset_game()
    return jsonify({'message': 'Game reset'})

@app.route('/set_difficulty/<difficulty>', methods=['POST'])
def set_difficulty(difficulty):
    if difficulty in ['easy', 'medium', 'hard']:
        game_state['bot_difficulty'] = difficulty
        return jsonify({'message': f'Difficulty set to {difficulty}'})
    return jsonify({'error': 'Invalid difficulty'}), 400

@app.route('/add_coins/<difficulty>', methods=['POST'])
def add_coins(difficulty):
    coins_to_add = {
        'easy': 5,
        'medium': 10,
        'hard': 15
    }.get(difficulty, 0)
    game_state['coins'] += coins_to_add
    return jsonify({'coins': game_state['coins']})

@app.route('/get_coins', methods=['GET'])
def get_coins():
    return jsonify({'coins': game_state['coins']})

@app.route('/buy_skin/<skin>')
def buy_skin(skin):
    skin_prices = {
        'fire': 50,
        'ice': 30
    }
    
    if skin in skin_prices and game_state['coins'] >= skin_prices[skin]:
        game_state['coins'] -= skin_prices[skin]
        game_state['current_skin'] = skin
        return jsonify({
            'success': True, 
            'coins': game_state['coins']
        })
    elif skin == 'default':
        game_state['current_skin'] = skin
        return jsonify({
            'success': True, 
            'coins': game_state['coins']
        })
    return jsonify({
        'success': False, 
        'message': 'Not enough coins'
    })

def reset_game():
    game_state['board'] = ['' for _ in range(9)]
    game_state['current_player'] = 'X'
    game_state['game_over'] = False

def check_winner():
    # All possible winning combinations
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]
    
    for combo in winning_combinations:
        if (game_state['board'][combo[0]] != '' and
            game_state['board'][combo[0]] == game_state['board'][combo[1]] == game_state['board'][combo[2]]):
            return game_state['board'][combo[0]]  # Returns 'X' or 'O'
    return None

def is_board_full():
    return '' not in game_state['board']

def make_bot_move():
    difficulty = game_state['bot_difficulty']
    
    if difficulty == 'easy':
        return make_easy_move()
    elif difficulty == 'medium':
        return make_medium_move()
    else:  # hard
        return make_hard_move()

def make_easy_move():
    # Simply make a random move
    empty_cells = [i for i, cell in enumerate(game_state['board']) if cell == '']
    if empty_cells:
        return random.choice(empty_cells)
    return None

def make_medium_move():
    # 50% chance to make a smart move, 50% chance to make a random move
    if random.random() < 0.5:
        return make_easy_move()
    return make_hard_move()

def make_hard_move():
    # Try to win
    bot_move = find_winning_move('O')
    if bot_move is not None:
        return bot_move
    
    # Block player from winning
    block_move = find_winning_move('X')
    if block_move is not None:
        return block_move
    
    # Take center if available
    if game_state['board'][4] == '':
        return 4
    
    # Take corners
    corners = [0, 2, 6, 8]
    random.shuffle(corners)
    for corner in corners:
        if game_state['board'][corner] == '':
            return corner
    
    # Take any available edge
    edges = [1, 3, 5, 7]
    random.shuffle(edges)
    for edge in edges:
        if game_state['board'][edge] == '':
            return edge
    
    return None

def find_winning_move(player):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    
    for combo in winning_combinations:
        if (game_state['board'][combo[0]] == game_state['board'][combo[1]] == player and 
            game_state['board'][combo[2]] == ''):
            return combo[2]
        if (game_state['board'][combo[0]] == game_state['board'][combo[2]] == player and 
            game_state['board'][combo[1]] == ''):
            return combo[1]
        if (game_state['board'][combo[1]] == game_state['board'][combo[2]] == player and 
            game_state['board'][combo[0]] == ''):
            return combo[0]
    return None

if __name__ == '__main__':
    app.run(debug=True) 