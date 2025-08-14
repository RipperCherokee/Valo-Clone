import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Improved Database Configuration ---
db_user = os.environ.get('DB_USER', 'postgres')
db_password = os.environ.get('DB_PASSWORD') 
db_host = os.environ.get('DB_HOST', 'db')
db_name = os.environ.get('DB_NAME', 'valorant_stats')
# CORRECTED: sslmode defaults to 'disable' for local development.
db_sslmode = os.environ.get('DB_SSLMODE', 'disable') 

# Check if the password is provided.
if not db_password:
    raise ValueError("DB_PASSWORD environment variable not set.")

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
    f"?sslmode={db_sslmode}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Model ---
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    kd_ratio = db.Column(db.Float, nullable=False)

    def to_dict(self):
        """Converts the player object to a dictionary for JSON serialization."""
        return {
            'id': self.id,
            'username': self.username,
            'rank': self.rank,
            'kd_ratio': self.kd_ratio
        }

# --- Database Initialization Command ---
# This is the proper way to initialize the database tables.
@app.cli.command("init-db")
def init_db_command():
    """Creates the database tables."""
    with app.app_context():
        db.create_all()
    print("Initialized the database.")

# --- API Endpoints (CRUD Operations) ---

# Health Check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Checks if the service is running."""
    return jsonify({"status": "healthy"}), 200

# CREATE a new player
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

    new_player = Player(
        username=data['username'].strip(),
        rank=data['rank'],
        kd_ratio=kd_ratio
    )
    db.session.add(new_player)
    db.session.commit()
    return jsonify(new_player.to_dict()), 201

# READ all players
@app.route('/players', methods=['GET'])
def get_all_players():
    players = db.session.execute(db.select(Player)).scalars().all()
    return jsonify([player.to_dict() for player in players])

# READ a single player by ID
@app.route('/players/<int:player_id>', methods=['GET'])
def get_player(player_id):
    player = db.session.get(Player, player_id)
    if player is None:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify(player.to_dict())

# UPDATE a player's stats
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

# DELETE a player
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