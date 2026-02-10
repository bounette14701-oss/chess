import streamlit as st
import streamlit.components.v1 as components
import chess
import chess.engine
import os
import shutil

# --- CONFIGURATION ---
st.set_page_config(page_title="ProChess Cloud", layout="wide", page_icon="♟️")

# Design sombre inspiré de Lichess
st.markdown("""
    <style>
    .stApp { background-color: #161512; color: #bababa; }
    iframe { border-radius: 8px; border: 2px solid #3c3c3c !important; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTEUR STOCKFISH ---
def get_bot_move(board, difficulty):
    path = "/usr/games/stockfish" if os.path.exists("/usr/games/stockfish") else shutil.which("stockfish")
    if not path: return None
    try:
        with chess.engine.SimpleEngine.popen_uci(path) as engine:
            skill = int((difficulty - 1) * 2)
            engine.configure({"Skill Level": skill})
            result = engine.play(board, chess.engine.Limit(time=0.1))
            return result.move
    except: return None

# --- INITIALISATION DE L'ÉTAT ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'move_log' not in st.session_state:
    st.session_state.move_log = []

# --- GESTION DU COUP VIA URL ---
# Cette partie intercepte le coup envoyé par le JavaScript
if "m" in st.query_params:
    move_uci = st.query_params["m"]
    st.query_params.clear() # On nettoie l'URL
    
    try:
        move = chess.Move.from_uci(move_uci)
        if move in st.session_state.board.legal_moves:
            # Coup du Joueur
            st.session_state.board.push(move)
            st.session_state.move_log.append(f"Joueur: {move_uci}")
            
            # Coup du Bot immédiat
            if not st.session_state.board.is_game_over():
                bot_move = get_bot_move(st.session_state.board, st.session_state.get('diff', 5))
                if bot_move:
                    st.session_state.board.push(bot_move)
                    st.session_state.move_log.append(f"Bot: {bot_move.uci()}")
            st.rerun()
    except: pass

# --- COMPOSANT ÉCHIQUIER INTERACTIF ---
def chessboard_component(fen):
    # Ce script JS crée l'échequier et renvoie le coup à Streamlit via l'URL
    js_code = f"""
    <link rel="stylesheet" href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
    
    <div id="board" style="width: 450px; margin: auto;"></div>
    
    <script>
        var board = null;
        var game = new Chess('{fen}');

        function onDrop (source, target) {{
            var move = game.move({{ from: source, to: target, promotion: 'q' }});
            if (move === null) return 'snapback';

            // PONT MAGIQUE : On envoie le coup à l'application parente
            const url = new URL(window.parent.location.href);
            url.searchParams.set('m', source + target);
            window.parent.location.href = url.href;
        }}

        board = Chessboard('board', {{
            draggable: true,
            position: '{fen}',
            onDrop: onDrop,
            pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{{piece}}.png'
        }});
    </script>
    """
    return components.html(js_code, height=500)

# --- INTERFACE ---
col_board, col_side = st.columns([2, 1])

with col_side:
    st.title("♟️ ProChess")
    st.session_state.diff = st.slider("Difficulté Stockfish", 1, 10, 5)
    
    if st.button("🔄 Nouvelle Partie"):
        st.session_state.board = chess.Board()
        st.session_state.move_log = []
        st.query_params.clear()
        st.rerun()

    st.subheader("Historique")
    for m in st.session_state.move_log[-8:]:
        st.caption(m)

with col_board:
    # On affiche l'échiquier
    chessboard_component(st.session_state.board.fen())
    
    # Affichage du statut sous le plateau
    if st.session_state.board.is_checkmate():
        st.error("MAT ! La partie est terminée.")
    elif st.session_state.board.is_check():
        st.warning("ÉCHEC AU ROI")
    else:
        st.info("Faites glisser une pièce pour jouer.")
