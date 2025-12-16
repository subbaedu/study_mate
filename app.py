### Group C, Project name: Study Mate

# This Streamlit application allows users to:
# 1) Create and save flashcard sets (term–definition pairs)
# 2) Load existing sets from disk (JSON files)
# 3) Practice the flashcards via a multiple-choice quiz

## Packages
# streamlit : web interface
# json      : persistent storage of flashcard sets
# random    : randomization in quiz questions
# pathlib  : platform-independent file handling

import streamlit as st
import json
import random
from pathlib import Path

## Setting data storage
# All flashcard sets are stored as JSON files
# inside the local "data/" directory

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)  # creating data folder if it doesn't exist

## Basic controls
# These helper functions handle:
# - listing available sets
# - loading and saving sets
# - modifying cards inside a set

def list_sets():
    """Return a list of set names (without .json)."""
    return sorted([p.stem for p in DATA_DIR.glob("*.json")])

def load_set(set_name):
    """Load a flashcard set from data/<set_name>.json. Returns a dict."""
    path = DATA_DIR / f"{set_name}.json"
    if not path.exists():
        # If file doesn't exist yet, start an empty set
        return {"name": set_name, "cards": []}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_set(set_data):
    """Save a flashcard set dict to data/<name>.json."""
    set_name = set_data["name"]
    path = DATA_DIR / f"{set_name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(set_data, f, ensure_ascii=False, indent=2)

def add_card(set_data, term, definition):
    """Add one card (term+definition) to the set."""
    set_data["cards"].append({"term": term.strip(), "definition": definition.strip()})

def delete_card(set_data, index):
    """Delete a card by its index."""
    set_data["cards"].pop(index)

# Quiz logic
# This function generates a single quiz question:
# - one correct definition
# - three incorrect (but unique) definitions
# - options are shuffled to avoid position bias

def generate_question(cards):
    """
    Returns: (term, correct_definition, options_list)
    options_list has 4 definitions (1 correct + 3 incorrect), shuffled.
    Works even if there are duplicate definitions.
    """
    correct_card = random.choice(cards)
    term = correct_card["term"]
    correct_def = correct_card["definition"]

    # Pool of wrong definitions (exclude the correct definition)
    wrong_def_pool = [c["definition"] for c in cards if c["definition"] != correct_def]

    # Remove duplicates so sampling is safe
    wrong_def_pool = list(set(wrong_def_pool))

    # Need 3 wrong options to form a 4-choice question
    if len(wrong_def_pool) < 3:
        st.warning(
            "Not enough unique wrong definitions to create 4 options. "
            "Add more cards with different definitions."
        )
        st.stop()

    wrong_defs = random.sample(wrong_def_pool, k=3)

    options = wrong_defs + [correct_def]
    random.shuffle(options)
    return term, correct_def, options


## Creating Streamlit surface
# The UI logic starts here.
# Streamlit re-runs this script top-to-bottom
# every time the user interacts with the page.

# Landing page title
st.title("Create or load your flashcard set!")

# Session state initialization
# session_state stores information that must persist
# across Streamlit re-runs (e.g. current set, quiz score)

if "mode" not in st.session_state:
    st.session_state.mode = "Edit"  # "Edit" or "Quiz"

if "q_term" not in st.session_state:
    st.session_state.q_term = None
if "q_correct_def" not in st.session_state:
    st.session_state.q_correct_def = None
if "q_options" not in st.session_state:
    st.session_state.q_options = []
if "score" not in st.session_state:
    st.session_state.score = 0
if "questions_answered" not in st.session_state:
    st.session_state.questions_answered = 0
if "feedback" not in st.session_state:
    st.session_state.feedback = ""

if "current_set_name" not in st.session_state:
    st.session_state.current_set_name = None


# Sidebar: set management
# Users can:
# - load an existing set
# - create a new set
# - switch between Edit and Quiz modes

st.sidebar.header("Your learning sets")

existing_sets = list_sets()
chosen = st.sidebar.selectbox(
    "Load an existing set",
    options=["(none)"] + existing_sets,
)

new_set_name = st.sidebar.text_input("Or create a new set (name)")

colA, colB = st.sidebar.columns(2)

with colA:
    if st.sidebar.button("Load set"):
        if chosen != "(none)":
            st.session_state.current_set_name = chosen
        else:
            st.sidebar.warning("Pick a set first.")

with colB:
    if st.sidebar.button("Create set"):
        name = new_set_name.strip()
        if not name:
            st.sidebar.warning("Please type a name.")
        else:
            data = load_set(name)
            save_set(data)
            st.session_state.current_set_name = name
            st.sidebar.success(f"Created: {name}")

st.sidebar.divider()
st.session_state.mode = st.sidebar.radio("Mode", ["Edit", "Quiz"])

# Load the selected set

if st.session_state.current_set_name is None:
    st.info("Choose or create a set from the sidebar to begin.")
    st.stop()

set_name = st.session_state.current_set_name
set_data = load_set(set_name)
cards = set_data["cards"]

# Main content area
# Two modes:
# - Edit mode: create and manage flashcards
# - Quiz mode: practice via multiple-choice questions

if st.session_state.mode == "Edit":

    # EDIT MODE

    st.subheader(f"Current set: **{set_name}**")
    st.write(f"Cards in set: **{len(cards)}**")

    st.divider()
    st.subheader("Add a flashcard")

    term = st.text_input("Term", key="edit_term")
    definition = st.text_area("Definition", key="edit_def")

    if st.button("Add card"):
        if not term.strip() or not definition.strip():
            st.warning("Please fill both the term and the definition.")
        else:
            add_card(set_data, term, definition)
            save_set(set_data)
            st.success("Card added!")
            st.rerun()

    st.divider()
    st.subheader("Cards in this set")

    if not cards:
        st.caption("No cards yet. Add your first one above.")
    else:
        # Display all cards with option to delete
        for i, card in enumerate(cards):
            col1, col2 = st.columns([4, 1])

            with col1:
                with st.expander(f"{i+1}. {card['term']}"):
                    st.write(card["definition"])

            with col2:
                if st.button("❌ Delete", key=f"delete_{i}"):
                    delete_card(set_data, i)
                    save_set(set_data)
                    st.success("Card deleted!")
                    st.rerun()


else:

    # QUIZ MODE

    st.subheader(f"Quiz: **{set_name}**")

    # Minimum requirement for quiz logic
    if len(cards) < 4:
        st.warning("You need at least 4 cards in this set to start the quiz.")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Start / New quiz"):
            st.session_state.score = 0
            st.session_state.questions_answered = 0
            st.session_state.feedback = ""
            term, correct_def, options = generate_question(cards)
            st.session_state.q_term = term
            st.session_state.q_correct_def = correct_def
            st.session_state.q_options = options
            st.rerun()

    with col2:
        if st.button("Next question"):
            st.session_state.feedback = ""
            term, correct_def, options = generate_question(cards)
            st.session_state.q_term = term
            st.session_state.q_correct_def = correct_def
            st.session_state.q_options = options
            st.rerun()

    with col3:
        if st.button("Reset score"):
            st.session_state.score = 0
            st.session_state.questions_answered = 0
            st.session_state.feedback = ""
            st.success("Score reset!")

    st.divider()

    # Initialize first question if quiz just started
    if st.session_state.q_term is None:
        term, correct_def, options = generate_question(cards)
        st.session_state.q_term = term
        st.session_state.q_correct_def = correct_def
        st.session_state.q_options = options

    st.write(f"**Score:** {st.session_state.score} / {st.session_state.questions_answered}")
    st.markdown(f"### Term: **{st.session_state.q_term}**")

    choice = st.radio(
        "Pick the correct definition:",
        st.session_state.q_options,
        key="quiz_choice",
    )

    if st.button("Submit answer"):
        st.session_state.questions_answered += 1

        if choice == st.session_state.q_correct_def:
            st.session_state.score += 1
            st.session_state.feedback = "✅ Correct!"
        else:
            st.session_state.feedback = (
                "❌ Wrong.\n\n"
                f"**Correct answer:** {st.session_state.q_correct_def}"
            )

        st.rerun()

    if st.session_state.feedback:
        st.info(st.session_state.feedback)
