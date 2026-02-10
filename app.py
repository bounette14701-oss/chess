import streamlit as st
import chess
import chess.svg
import chess.engine
import random
import base64
import os
import shutil

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="ProChess Cloud", layout="wide")

def render_svg(svg):
    """Affiche le SVG de l'échiquier de manière centrée."""
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    html = f'<div style="display: flex; justify-content: center;"><img src="data:image/svg+xml;base64,{b64}" width="500px"/></div>'
    return st.write(html, unsafe_allow_html=True)

# --- RECHERCHE DU MOTEUR STOCKFISH ---
def get_stockfish_path():
    """Localise le binaire Stockfish sur Streamlit Cloud ou en local."""
    # Sur Streamlit Cloud (Linux), le package 'stockfish' l'installe souvent ici :
    cloud_path = "/usr/games/stockfish"
    if os.path.exists(cloud_path):
        return cloud_path
    
    # Sinon, on cherche dans le PATH (Windows ou MacOS)
    path = shutil.which("stockfish")
    return path

# --- INITIALISATION DE L'ÉTAT ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'move_log' not in st.session_state:
    st.session_state.move_log = []
if 'puzzle_index' not in st.session_state:
    st.session_state.puzzle_index = 0
if 'game_over' not in st.session_state:
    st.session_state.game_over = False

# --- BASE DE DONNÉES DE PUZZLES ---
PUZZLES = [
    {"fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR b KQkq - 3 3", "solution": "f7f5", "desc": "Trouvez le meilleur coup pour les noirs."},
    {"fen": "6k1/pp3p1p/6p1/5q2/8/1P1R1P2/P1Q2P1P/4r1K1 w - - 1 26", "solution": "g1g2", "desc": "Évitez le mat immédiat."}
]

# --- LOGIQUE DU MOTEUR ---
def get_bot_move(board, difficulty):
    engine_path = get_stockfish_path()
    
    if engine_path:
        try:
            with chess.engine.SimpleEngine.popen_uci(engine_path) as engine:
                # Skill Level de 0 à 20
                skill_level = int((difficulty - 1) * 2) 
                # Temps de réflexion croissant avec la difficulté
                limit = chess.engine.Limit(time=0.02 * difficulty)
                
                engine.configure({"Skill Level": skill_level})
                result = engine.play(board, limit)
                return result.move
        except Exception as e:
            st.error(f"Erreur moteur : {e}")
            return random.choice(list(board.legal_moves))
    else:
        # Si aucun moteur n'est trouvé, le bot joue au hasard
        st.sidebar.warning("Stockfish non trouvé. Mode aléatoire activé.")
        return random.choice(list(board.legal_moves))

# --- SIDEBAR ---
st.sidebar.title("♟️ ProChess Cloud")
mode = st.sidebar.radio("Mode de jeu", ["Bot (IA)", "Problèmes (Puzzles)", "Joueur vs Joueur"])

if mode == "Bot (IA)":
    difficulty = st.sidebar.slider("Niveau de l'IA (1 à 10)", 1, 10, 5)

if st.sidebar.button("Nouvelle Partie / Reset"):
    st.session_state.board = chess.Board()
    st.session_state.move_log = []
    st.session_state.game_over = False
    st.rerun()

# --- INTERFACE PRINCIPALE ---
st.title(f"♟️ {mode}")

col1, col2 = st.columns([2, 1])

with col1:
    # Affichage de l'échiquier
    last_move = st.session_state.board.peek() if st.session_state.board.move_stack else None
    board_svg = chess.svg.board(st.session_state.board, lastmove=last_move, size=500)
    render_svg(board_svg)

    # Entrée du coup
    if not st.session_state.game_over:
        with st.form(key="move_form", clear_on_submit=True):
            move_input = st.text_input("Votre coup (ex: e2e4, g1f3) :").lower().strip()
            submit_move = st.form_submit_button("Valider le coup")
        
        if submit_move and move_input:
            try:
                move = chess.Move.from_uci(move_input)
                if move in st.session_state.board.legal_moves:
                    # Joueur joue
                    st.session_state.board.push(move)
                    st.session_state.move_log.append(f"Vous : {move_input}")
                    
                    # IA joue (si mode Bot)
                    if mode == "Bot (IA)" and not st.session_state.board.is_game_over():
                        with st.spinner("L'IA réfléchit..."):
                            bot_move = get_bot_move(st.session_state.board, difficulty)
                            st.session_state.board.push(bot_move)
                            st.session_state.move_log.append(f"Bot : {bot_move.uci()}")
                    
                    # Vérification Puzzle
                    if mode == "Problèmes (Puzzles)":
                        if move_input == PUZZLES[st.session_state.puzzle_index]["solution"]:
                            st.success("Bravo ! Vous avez trouvé la solution.")
                        else:
                            st.error("Ce n'est pas le bon coup.")

                    st.rerun()
                else:
                    st.error(f"Le coup '{move_input}' est illégal.")
            except ValueError:
                st.error("Format invalide (utilisez la notation UCI comme 'e2e4').")

with col2:
    st.subheader("Analyse")
    
    if st.session_state.board.is_check():
        st.error("⚠️ ÉCHEC !")
    
    if st.session_state.board.is_game_over():
        st.session_state.game_over = True
        st.balloons()
        st.success(f"Fin ! Résultat : {st.session_state.board.result()}")

    st.write("**Historique :**")
    for m in st.session_state.move_log[-8:]:
        st.write(f"- {m}")

# --- SECTION PUZZLES ---
if mode == "Problèmes (Puzzles)":
    st.divider()
    puzzle = PUZZLES[st.session_state.puzzle_index]
    st.info(f"💡 Objectif : {puzzle['desc']}")
    if st.button("Charger la position du puzzle"):
        st.session_state.board = chess.Board(puzzle["fen"])
        st.session_state.move_log = []
        st.rerun()

# --- INFOS TECHNIQUES ---
with st.expander("Informations Techniques"):
    engine_status = "Installé" if get_stockfish_path() else "Non détecté (Mode aléatoire)"
    st.write(f"Moteur Stockfish : {engine_status}")
    st.write(f"Chemin détecté : {get_stockfish_path()}")
