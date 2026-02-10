import streamlit as st
import streamlit.components.v1 as components
import chess
import chess.engine
import os
import shutil
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="ProChess Cloud", layout="wide", page_icon="♟️")

# --- RECHERCHE STOCKFISH ---
def get_stockfish_path():
    cloud_path = "/usr/games/stockfish"
    return cloud_path if os.path.exists(cloud_path) else shutil.which("stockfish")

# --- INITIALISATION DE L'ÉTAT ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'move_log' not in st.session_state:
    st.session_state.move_log = []

# --- LOGIQUE DU MOTEUR ---
def get_bot_move(board, difficulty):
    path = get_stockfish_path()
    if not path: return None
    try:
        with chess.engine.SimpleEngine.popen_uci(path) as engine:
            skill = (difficulty - 1) * 2
            engine.configure({"Skill Level": skill})
            result = engine.play(board, chess.engine.Limit(time=0.1))
            return result.move
    except:
        return None

# --- COMPOSANT ÉCHIQUIER INTERACTIF (JS) ---
def interactive_board(fen):
    # Ce code injecte Chessboard.js et Chess.js pour le drag & drop
    board_html = f"""
    <link rel="stylesheet" href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
    
    <div id="myBoard" style="width: 500px; margin: auto;"></div>
    
    <script>
        var board = null;
        var game = new Chess('{fen}');

        function onDrop (source, target) {{
            var move = game.move({{
                from: source,
                to: target,
                promotion: 'q' 
            }});

            if (move === null) return 'snapback';

            // Envoi du coup à Streamlit
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: move.from + move.to
            }}, '*');
        }}

        var config = {{
            draggable: true,
            position: '{fen}',
            onDrop: onDrop,
            pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{{piece}}.png'
        }};
        board = Chessboard('myBoard', config);
    </script>
    """
    # On utilise un iframe pour capturer le message du JS
    return components.html(board_html, height=550)

# --- INTERFACE ---
st.title("♟️ ProChess Cloud Edition")

col1, col2 = st.columns([2, 1])

with col1:
    # Sidebar options
    mode = st.sidebar.selectbox("Mode", ["Bot", "Puzzles", "Local"])
    difficulty = st.sidebar.slider("Difficulté", 1, 10, 5)
    
    if st.sidebar.button("Nouvelle Partie"):
        st.session_state.board = chess.Board()
        st.session_state.move_log = []
        st.rerun()

    # Affichage du plateau
    # Note: On utilise un petit hack pour récupérer le coup du JS via les query params ou un widget
    # Mais ici pour simplifier et assurer la compatibilité Cloud, on va utiliser un input texte caché
    # ou simplement traiter le coup si le joueur l'envoie.
    
    st.markdown("### Faites glisser les pièces pour jouer")
    interactive_board(st.session_state.board.fen())
    
    # Zone de saisie (le JS peut aider, mais Streamlit a besoin d'un déclencheur Python)
    move_input = st.text_input("Confirmez votre coup ici (ex: e2e4) ou jouez au clavier :").lower().strip()
    
    if st.button("Valider le coup"):
        try:
            move = chess.Move.from_uci(move_input)
            if move in st.session_state.board.legal_moves:
                st.session_state.board.push(move)
                st.session_state.move_log.append(f"Vous: {move.uci()}")
                
                if mode == "Bot" and not st.session_state.board.is_game_over():
                    bot_move = get_bot_move(st.session_state.board, difficulty)
                    if bot_move:
                        st.session_state.board.push(bot_move)
                        st.session_state.move_log.append(f"IA: {bot_move.uci()}")
                st.rerun()
            else:
                st.error("Coup invalide.")
        except:
            st.error("Format invalide.")

with col2:
    st.subheader("Analyse")
    if st.session_state.board.is_check():
        st.error("ROI EN ÉCHEC")
    
    st.write("**Historique :**")
    for m in st.session_state.move_log[-10:]:
        st.write(m)

st.info("Astuce : Le drag-and-drop visuel fonctionne ! Pour valider le coup dans la logique du serveur, tapez-le dans la case et cliquez sur valider.")
