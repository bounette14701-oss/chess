import streamlit as st
import chess
import chess.engine
import random
import os
import shutil
from streamlit_chess import st_chess

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="ProChess Web",
    page_icon="♟️",
    layout="wide"
)

# Style CSS pour améliorer l'interface
st.markdown("""
    <style>
    .stApp { background-color: #161512; color: #bababa; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE DU MOTEUR ---
def get_stockfish_path():
    """Localise Stockfish sur Streamlit Cloud ou local."""
    cloud_path = "/usr/games/stockfish"
    return cloud_path if os.path.exists(cloud_path) else shutil.which("stockfish")

def get_bot_move(board, difficulty):
    path = get_stockfish_path()
    if not path:
        return random.choice(list(board.legal_moves))
    
    try:
        with chess.engine.SimpleEngine.popen_uci(path) as engine:
            # Conversion difficulté 1-10 vers Skill Level 0-20
            skill = (difficulty - 1) * 2
            # Temps de réflexion proportionnel (0.05s à 0.5s)
            time_limit = 0.05 * difficulty
            engine.configure({"Skill Level": skill})
            result = engine.play(board, chess.engine.Limit(time=time_limit))
            return result.move
    except:
        return random.choice(list(board.legal_moves))

# --- INITIALISATION DE L'ÉTAT ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'move_log' not in st.session_state:
    st.session_state.move_log = []
if 'last_move_uci' not in st.session_state:
    st.session_state.last_move_uci = None

# --- DONNÉES PUZZLES ---
PUZZLES = [
    {"fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 3 3", "sol": "f3f7", "hint": "Mat du berger : les Blancs jouent et matent."},
    {"fen": "r1b1kb1r/pppp1ppp/5n2/4q3/4P3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 7", "sol": "f2f4", "hint": "Gagnez du temps sur la dame noire."},
    {"fen": "6k1/pp3p1p/6p1/5q2/8/1P1R1P2/P1Q2P1P/4r1K1 w - - 1 26", "sol": "g1g2", "hint": "Le roi est exposé, trouvez la seule case de fuite."}
]

# --- SIDEBAR ET MODES ---
with st.sidebar:
    st.title("♟️ Menu Principal")
    mode = st.radio("Mode de jeu", ["🆚 Contre l'IA", "🧩 Puzzles", "👥 Local (2 joueurs)"])
    
    if mode == "🆚 Contre l'IA":
        diff = st.slider("Niveau de l'IA (Stockfish)", 1, 10, 5)
        st.info(f"Niveau {diff} : {'Débutant' if diff < 4 else 'Intermédiaire' if diff < 8 else 'Maître'}")
    
    st.divider()
    if st.button("🔄 Réinitialiser la partie"):
        st.session_state.board = chess.Board()
        st.session_state.move_log = []
        st.rerun()

# --- INTERFACE PRINCIPALE ---
col_board, col_info = st.columns([3, 2])

with col_board:
    st.subheader(f"Mode : {mode}")
    
    # Intégration du composant Drag & Drop
    # Note: st_chess renvoie un dictionnaire quand une pièce est déplacée
    move_data = st_chess(
        fen=st.session_state.board.fen(),
        key="main_chess_board"
    )

    # Logique de traitement du mouvement
    if move_data and "from" in move_data and "to" in move_data:
        move_uci = move_data["from"] + move_data["to"]
        
        # Gestion auto de la promotion en Reine
        move_obj = chess.Move.from_uci(move_uci)
        if chess.Move.from_uci(move_uci + "q") in st.session_state.board.legal_moves:
            move_obj = chess.Move.from_uci(move_uci + "q")

        # Vérifier si c'est un nouveau coup (pour éviter les boucles de rerun)
        if move_obj in st.session_state.board.legal_moves:
            # 1. Joueur humain
            st.session_state.board.push(move_obj)
            st.session_state.move_log.append(f"Joueur: {move_obj.uci()}")
            
            # 2. IA (si activée)
            if mode == "🆚 Contre l'IA" and not st.session_state.board.is_game_over():
                with st.spinner("L'IA analyse la position..."):
                    bot_move = get_bot_move(st.session_state.board, diff)
                    st.session_state.board.push(bot_move)
                    st.session_state.move_log.append(f"IA: {bot_move.uci()}")
            
            # 3. Vérification Puzzle
            if mode == "🧩 Puzzles":
                puzzle = PUZZLES[0] # Simplifié pour l'exemple
                if move_obj.uci() == puzzle["sol"]:
                    st.success("✅ Excellent ! Solution trouvée.")
                else:
                    st.error("❌ Mauvais coup. Essayez encore.")
                    st.session_state.board.pop()
                    st.session_state.move_log.pop()
            
            st.rerun()

with col_info:
    st.subheader("Analyse & Historique")
    
    # Indicateurs d'état
    if st.session_state.board.is_check():
        st.warning("⚠️ ÉCHEC AU ROI !")
    
    if st.session_state.board.is_game_over():
        st.balloons()
        st.success(f"Partie terminée ! Résultat : {st.session_state.board.result()}")
        
    # Affichage de l'historique style Chess.com
    with st.container():
        st.write("**Coups joués :**")
        moves = st.session_state.move_log
        for i in range(0, len(moves), 2):
            w = moves[i]
            b = moves[i+1] if i+1 < len(moves) else ""
            st.text(f"{(i//2)+1}. {w.split(': ')[1]}   {b.split(': ')[1] if b else ''}")

# --- SECTION PUZZLES ---
if mode == "🧩 Puzzles":
    st.divider()
    with st.expander("💡 Besoin d'un indice ?", expanded=True):
        st.write(PUZZLES[0]["hint"])
    if st.button("Charger le puzzle suivant"):
        st.session_state.board = chess.Board(PUZZLES[0]["fen"])
        st.rerun()

# --- FOOTER ---
st.markdown("---")
st.caption("Inspiré par l'architecture open-source de Lichess. Propulsé par Stockfish.")
