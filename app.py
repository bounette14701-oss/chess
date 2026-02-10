import reflex as rx
import chess
import chess.engine
import random

# --- LOGIQUE DU JEU (BACKEND) ---
class State(rx.State):
    fen: str = chess.STARTING_FEN
    move_log: list[str] = []
    difficulty: int = 5

    def handle_move(self, move_data: dict):
        """Appelé quand une pièce est lâchée sur le plateau"""
        board = chess.Board(self.fen)
        move_uci = move_data["sourceSquare"] + move_data["targetSquare"]
        
        try:
            move = chess.Move.from_uci(move_uci)
            if move in board.legal_moves:
                board.push(move)
                self.move_log.append(f"Joueur: {move_uci}")
                
                # Réponse immédiate de l'IA (Stockfish ou Random)
                if not board.is_game_over():
                    bot_move = random.choice(list(board.legal_moves)) # Exemple simplifié
                    board.push(bot_move)
                    self.move_log.append(f"IA: {bot_move.uci()}")
                
                self.fen = board.fen()
        except Exception:
            pass

# --- INTERFACE (FRONTEND) ---
def index():
    return rx.center(
        rx.vstack(
            rx.heading("ProChess Reflex", size="9"),
            
            # Ici, on peut intégrer un vrai composant React Chessboard
            # via l'intégration facile de Reflex pour les bibliothèques JS
            rx.box(
                rx.html(f"<chess-board fen='{State.fen}' draggable='true'></chess-board>"),
                width="400px",
                height="400px",
            ),
            
            rx.hstack(
                rx.vstack(
                    rx.text("Historique"),
                    rx.list(
                        rx.foreach(State.move_log, lambda m: rx.list_item(m))
                    ),
                    max_height="200px",
                    overflow_y="auto"
                ),
                rx.vstack(
                    rx.text("Difficulté IA"),
                    rx.slider(default_value=5, min_=1, max_=10, on_change=State.set_difficulty),
                    rx.button("Nouvelle Partie", on_click=rx.redirect("/")),
                )
            ),
            padding="2em",
            background_color="#1a1a1a",
            border_radius="15px",
            color="white"
        ),
        height="100vh",
        background_color="#121212"
    )

app = rx.App()
app.add_page(index)
