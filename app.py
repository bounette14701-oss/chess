import streamlit as st
import streamlit.components.v1 as components
import chess
import chess.engine
import os
import shutil

# --- CONFIGURATION ---
st.set_page_config(page_title="ProChess Cloud", layout="wide", page_icon="♟️")

# --- RECHERCHE STOCKFISH ---
def get_stockfish_path():
    # Sur Streamlit Cloud, le binaire est ici :
    cloud_path = "/usr/games/stockfish"
    if os.path.exists(cloud_path):
        return cloud_path
    return shutil.which("stockfish")

# --- INITIALISATION DE L'ÉTAT ---
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'move_log' not in st.session_state:
    st.session_state.move_log = []

# --- LOGIQUE DU MOTEUR ---
def get_bot_move(board, difficulty):
    path = get_stockfish_path()
    if not path:
        return None
    try:
        # On limite le temps de calcul pour éviter de surcharger le CPU du cloud
        with chess.engine.SimpleEngine.popen_uci(path) as engine:
            skill = int((difficulty - 1) * 2)
            engine.configure({"Skill Level": skill})
            result = engine.play(board, chess.engine.Limit(time=0.1))
            return result.move
    except:
        return None

# --- COMPOSANT ÉCHIQUIER (JS) ---
def interactive_board(fen):
    # On utilise Chessboard.js via CDN pour le drag and drop visuel
    board_html = f"""
    <link rel="stylesheet" href="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css">
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
    
    <div id="myBoard" style="width: 450px; margin: auto;"></div>
    <p style="text-align:center; color: #bababa; font-family: sans-serif; margin-top: 10px;">
        Déplacez une pièce, puis copiez le coup ci-dessous (ex: e2e4)
    </p>

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
    return components.html(board_html, height=520)

# --- INTERFACE ---
st.title("♟️ ProChess : Cloud Edition")

col1, col2 = st.columns([2, 1])

with col1:
    # On affiche le plateau interactif
    interactive_board(st.session_state.board.fen())
    
    # Saisie du coup
    with st.form(key="move_form"):
        move_input = st.text_input("Entrez votre coup (ex: e2e4, g1f3) :").lower().strip()
        submit = st.form_submit_button("Valider le mouvement")

    if submit and move_input:
        try:
            move = chess.Move.from_uci(move_input)
            if move in st.session_state.board.legal_moves:
                # Joueur
                st.session_state.board.push(move)
                st.session_state.move_log.append(f"Vous: {move_input}")
                
                # Bot
                if not st.session_state.board.is_game_over():
                    with st.spinner("L'IA réfléchit..."):
                        bot_move = get_bot_move(st.session_state.board, 5)
                        if bot_move:
                            st.session_state.board.push(bot_move)
                            st.session_state.move_log.append(f"IA: {bot_move.uci()}")
                st.rerun()
            else:
                st.error("Coup illégal pour cette position.")
        except:
            st.error("Format invalide. Utilisez la notation comme 'e2e4'.")

with col2:
    st.sidebar.title("Paramètres")
    difficulty = st.sidebar.slider("Niveau IA", 1, 10, 5)
    if st.sidebar.button("Nouvelle Partie"):
        st.session_state.board = chess.Board()
        st.session_state.move_log = []
        st.rerun()

    st.subheader("Analyse & Historique")
    if st.session_state.board.is_checkmate():
        st.balloons()
        st.success("MAT !")
    elif st.session_state.board.is_check():
        st.warning("Échec !")

    for m in st.session_state.move_log[-10:]:
        st.write(m)

st.divider()
st.caption("Note : Le drag-and-drop est visuel. Pour confirmer le coup au moteur, saisissez-le dans la case texte.")
