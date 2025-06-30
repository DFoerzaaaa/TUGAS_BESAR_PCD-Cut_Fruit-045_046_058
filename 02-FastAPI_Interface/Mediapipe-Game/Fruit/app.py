import streamlit as st
import subprocess
import os
import sys
from PIL import Image

# Set page configuration
st.set_page_config(page_title="Fruit Game", layout="centered")

# Custom CSS for gradient background and styling
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to right, #a8e063, #56ab2f);
    }
    .title {
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 40px;
        margin-bottom: 20px;
        text-align: center;
    }
    .button-container {
        display: flex;
        justify-content: center;
        gap: 20px;
    }
    .game-button {
        text-align: center;
        color: black;
        font-size: 18px;
    }
    .game-over {
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
        color: white;
        font-size: 40px;
        margin-top: 40px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if 'current_game' not in st.session_state:
    st.session_state.current_game = None
    st.session_state.game_over = False
    st.session_state.error_message = None
    st.session_state.game_score = 0

def run_game(game_file):
    """Run the specified game script using the virtual environment's Python and capture score."""
    if not os.path.isfile(game_file):
        st.session_state.error_message = f"Error: {game_file} not found in the current directory."
        return False
    try:
        python_exe = sys.executable
        result = subprocess.run([python_exe, game_file], capture_output=True, text=True, check=True)
        # Extract score from output (assuming game prints score as "Score: X" on exit)
        output = result.stdout
        score_line = [line for line in output.split('\n') if line.startswith('Score:')]
        score = int(score_line[0].split(':')[1].strip()) if score_line else 0
        st.session_state.game_score = score
        st.session_state.error_message = None
        return True
    except subprocess.CalledProcessError as e:
        st.session_state.error_message = f"Error running {game_file}: {e.stderr}"
        return False
    except FileNotFoundError:
        st.session_state.error_message = f"Error: Python executable not found at {python_exe}."
        return False

# Main menu
if not st.session_state.current_game:
    st.markdown('<div class="title">🎮 Let\'s Play The Game 🍓</div>', unsafe_allow_html=True)

    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("👃🍎 Nose Fruit", key="nose_fruit", help="Play Nose Fruit game"):
            st.session_state.current_game = "nose_fruit.py"
            st.session_state.game_over = False
            st.rerun()

    with col2:
        if st.button("😋🍌 Fruit Eater", key="fruit_eater", help="Play Fruit Eater game"):
            st.session_state.current_game = "fruit_eater.py"
            st.session_state.game_over = False
            st.rerun()

    with col3:
        if st.button("👐🍒 Fruit Catcher", key="fruit_catcher", help="Play Fruit Catcher game"):
            st.session_state.current_game = "fruit_catcher.py"
            st.session_state.game_over = False
            st.rerun()

# Game execution and post-game menu
if st.session_state.current_game and not st.session_state.game_over:
    success = run_game(st.session_state.current_game)
    st.session_state.game_over = True
    st.rerun()

# Game over menu
if st.session_state.current_game and st.session_state.game_over:
    st.markdown('<div class="game-over">💀 Game Over!!!</div>', unsafe_allow_html=True)

    # Tombol di tengah
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.empty()  # Spacer kiri

    with col2:
        # Tengah
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Menu", key="menu", help="Return to main menu"):
                st.session_state.current_game = None
                st.session_state.game_over = False
                st.session_state.error_message = None
                st.rerun()
        with c2:
            if st.button("Play Again", key="play_again", help="Play the same game again"):
                st.session_state.game_over = False
                st.rerun()

    with col3:
        st.empty()  # Spacer kanan
