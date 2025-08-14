import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Corrected Database Configuration Logic ---
# First, check for the all-in-one DATABASE_URL from the hosting provider.
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # When using DATABASE_URL from Render/Heroku, ensure it uses 'postgresql://'
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
else:
    # If DATABASE_URL is not found, THEN fall back to individual variables for local dev.
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD') 
    db_host = os.environ.get('DB_HOST', 'db')
    db_name = os.environ.get('DB_NAME', 'valorant_stats')
    db_sslmode = os.environ.get('DB_SSLMODE', 'disable')

    # Now, only check for the password if we are in this fallback block.
    if not db_password:
        raise ValueError("DB_PASSWORD environment variable not set (required for local dev).")
    
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}?sslmode={db_sslmode}"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Model (No changes needed here) ---
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    kd_ratio = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'rank': self.rank, 'kd_ratio': self.kd_ratio}

# --- Database Initialization Command (No changes needed here) ---
@app.cli.command("init-db")
def init_db_command():
    with app.app_context():
        db.create_all()
    print("Initialized the database.")

# --- API Endpoints (No changes needed here) ---

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/players', methods=['POST'])
def create_player():
    data = request.get_json()
    if not data or not all(k in data for k in ['username', 'rank', 'kd_ratio']):
        return jsonify({'error': 'Missing required fields: username, rank, kd_ratio'}), 400
    if not isinstance(data['username'], str) or not data['username'].strip():
        return jsonify({'error': 'Username must be a non-empty string'}), 400
    try:
        kd_ratio = float(data['kd_ratio'])
    except (ValueError, TypeError):
        return jsonify({'error': 'kd_ratio must be a valid number'}), 400
    new_player = Player(username=data['username'].strip(), rank=data['rank'], kd_ratio=kd_ratio)
    db.session.add(new_player)
    db.session.commit()
    return jsonify(new_player.to_dict()), 201

@app.route('/players', methods=['GET'])
def get_all_players():
    players = db.session.execute(db.select(Player)).scalars().all()
    return jsonify([player.to_dict() for player in players])

@app.route('/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    player = db.session.get(Player, player_id)
    if player is None:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify(player.to_dict())

@app.route('/players/<int:player_id>', methods=['PUT'])
def update_player(player_id):
    player = db.session.get(Player, player_id)
    if player is None:
        return jsonify({'error': 'Player not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing data'}), 400
    if 'rank' in data:
        player.rank = data['rank']
    if 'kd_ratio' in data:
        try:
            player.kd_ratio = float(data['kd_ratio'])
        except (ValueError, TypeError):
            return jsonify({'error': 'kd_ratio must be a valid number'}), 400
    db.session.commit()
    return jsonify(player.to_dict())

@app.route('/players/<int:player_id>', methods=['DELETE'])
def delete_player(player_id):
    player = db.session.get(Player, player_id)
    if player is None:
        return jsonify({'error': 'Player not found'}), 404
    db.session.delete(player)
    db.session.commit()
    return jsonify({'message': f'Player with ID {player_id} deleted.'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)