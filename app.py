import streamlit as st
import streamlit.components.v1 as components
import chess
import chess.engine
import os
import shutil

# --- CONFIGURATION ---
st.set_page_config(page_title="ProChess Cloud", layout="wide", page_icon="♟️")

# CSS pour un look "Dark Mode" Lichess
st.markdown("""
    <style>
    .stApp { background-color: #161512; color: #bababa; }
    iframe { border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE DU MOTEUR STOCKFISH ---
def get_stockfish_path():
    cloud_path = "/usr/games/stockfish"
    return cloud_path if os.path.exists(cloud_path) else shutil.which("stockfish")

def get_bot_move(board, difficulty):
    path = get_stockfish_path()
    if not path: return None
    try:
        with chess.engine.SimpleEngine.popen_uci(path) as engine:
            # Skill Level 0 à 20
            skill = int((difficulty - 1) * 2)
            engine.configure({"Skill Level": skill})
            # Temps de calcul limité pour la réactivité
            result = engine.play(board, chess.engine.Limit(time=0.1, depth=difficulty+5))
            return result.move
    except:
        return None

# --- GESTION DU PONT JAVASCRIPT -> PYTHON ---
# On récupère le coup depuis l'URL (ex: ?move=e2e4)
if "move" in st.query_params:
    move_uci = st.query_params["move"]
    # Nettoyage immédiat de l'URL pour éviter de rejouer le coup au prochain refresh
    st.query_params.clear()
    
    try:
        move = chess.Move.from_uci(move_uci)
        if 'board' in st.session_state and move in st.session_state.board.legal_moves:
            st.session_state.board.push(move)
            st.session_state.move_log.append(f"Joueur: {move_uci}")
            
            # Tour de l'IA si mode Bot activé
            if st.session_state.get('mode') == "Bot" and not st.session_state.board.is_game_over():
                bot_move = get_bot_move(st.session_state.board, st.session_state.get('diff', 5))
                if bot_move:
                    st.session_state.board.push(bot_move)
                    st.session_state.move_log.append(f"IA: {bot_move.uci()}")
    except:
        pass

# --- INITIALISATION DE L'ÉTAT ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'move_log' not in st.session_state:
    st.session_state.move_log = []

# --- COMPOSANT ÉCHIQUIER INTERACTIF ---
def render_interactive_board(fen):
    """Génère l'échequier avec Chessboard.js et le pont de données."""
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
                promotion: 'q' // Promotion dame automatique pour fluidité
            }});

            if (move === null) return 'snapback';

            // LE PONT : On recharge la page parente avec le coup dans l'URL
            const url = new URL(window.parent.location.href);
            url.searchParams.set('move', source + target);
            window.parent.location.href = url.href;
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
    return components.html(board_html, height=550)

# --- INTERFACE UTILISATEUR ---
st.title("♟️ ProChess Cloud Edition")

col1, col2 = st.columns([2, 1])

with col2:
    st.sidebar.title("Configuration")
    st.session_state.mode = st.sidebar.selectbox("Mode de jeu", ["Bot", "Local"], index=0)
    st.session_state.diff = st.sidebar.slider("Difficulté IA (Stockfish)", 1, 10, 5)
    
    if st.sidebar.button("Nouvelle Partie"):
        st.session_state.board = chess.Board()
        st.session_state.move_log = []
        st.query_params.clear()
        st.rerun()

    st.subheader("Analyse & Historique")
    if st.session_state.board.is_check():
        st.error("⚠️ ÉCHEC AU ROI")
    
    if st.session_state.board.is_game_over():
        st.success(f"Fin de partie ! Résultat : {st.session_state.board.result()}")
        st.balloons()

    # Affichage des 10 derniers coups
    for m in st.session_state.move_log[-10:]:
        st.text(m)

with col1:
    # On affiche l'échiquier interactif
    render_interactive_board(st.session_state.board.fen())

st.divider()

st.caption("Système de coordonnées UCI utilisé par le moteur pour traiter vos déplacements.")
