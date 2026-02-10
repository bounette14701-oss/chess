from fasthtml.common import *
import chess
import chess.engine
import os
import shutil

# --- LOGIQUE DU MOTEUR ---
def get_stockfish():
    # Cherche stockfish dans le système
    return shutil.which("stockfish") or "/usr/games/stockfish"

# --- INITIALISATION ---
app, rt = fast_app(
    hdrs=(
        Link(rel="stylesheet", href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css"),
        Script(src="https://code.jquery.com/jquery-3.5.1.min.js"),
        Script(src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"),
        Script(src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"),
    )
)

# État global simplifié (pour une démo mono-utilisateur)
# Dans une vraie app, on utiliserait des sessions
game_state = {"board": chess.Board(), "difficulty": 5}

@rt("/")
def get():
    return Titled("ProChess FastHTML",
        Container(
            H1("♟️ ProChess Engine"),
            Div(id="board", style="width: 400px; margin: auto;"),
            Div(id="status", style="margin-top: 20px; text-align: center; font-weight: bold;"),
            
            # Script de contrôle pour le Drag & Drop
            Script(f"""
                var board = null;
                var game = new Chess('{game_state['board'].fen()}');

                function onDrop(source, target) {{
                    var move = game.move({{ from: source, to: target, promotion: 'q' }});
                    if (move === null) return 'snapback';

                    // Envoi du coup au serveur Python via HTMX (fetch) sans recharger la page
                    fetch(`/move?uci=${{source + target}}`)
                        .then(response => response.json())
                        .then(data => {{
                            board.position(data.fen);
                            document.getElementById('status').innerText = data.status;
                        }});
                }}

                board = Chessboard('board', {{
                    draggable: true,
                    position: '{game_state['board'].fen()}',
                    onDrop: onDrop,
                    pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{{piece}}.png'
                }});
            """),
            
            P("Mode : Contre le Bot (IA)", style="text-align: center; margin-top: 20px;"),
            Button("Nouvelle Partie", hx_get="/reset", hx_target="body", style="display: block; margin: auto;")
        )
    )

@rt("/move")
def get_move(uci: str):
    board = game_state["board"]
    try:
        move = chess.Move.from_uci(uci)
        if move in board.legal_moves:
            board.push(move)
            
            # Réponse de l'IA
            if not board.is_game_over():
                path = get_stockfish()
                try:
                    with chess.engine.SimpleEngine.popen_uci(path) as engine:
                        engine.configure({"Skill Level": (game_state["difficulty"]-1)*2})
                        result = engine.play(board, chess.engine.Limit(time=0.1))
                        board.push(result.move)
                except:
                    # Fallback si pas de stockfish
                    import random
                    board.push(random.choice(list(board.legal_moves)))

            status = "À vous de jouer"
            if board.is_checkmate(): status = "Mat !"
            elif board.is_check(): status = "Échec !"

            return {"fen": board.fen(), "status": status}
    except:
        return {"fen": board.fen(), "status": "Coup invalide"}

@rt("/reset")
def get_reset():
    game_state["board"] = chess.Board()
    return RedirectResponse("/")

serve()
