# streamlit_quiz.py
import streamlit as st
import random
import time
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Fun Quiz", page_icon="🧠", layout="centered")

# ---------- Utility: sample questions ----------
SAMPLE_QUESTIONS = [
    {
        "question": "Which planet is known as the Red Planet?",
        "option1": "Earth",
        "option2": "Mars",
        "option3": "Jupiter",
        "option4": "Venus",
        "answer": "Mars",
        "category": "Science"
    },
    {
        "question": "Which language is this app built with?",
        "option1": "JavaScript",
        "option2": "Go",
        "option3": "Python",
        "option4": "Ruby",
        "answer": "Python",
        "category": "Technology"
    },
    {
        "question": "What is the capital of France?",
        "option1": "Berlin",
        "option2": "Madrid",
        "option3": "Rome",
        "option4": "Paris",
        "answer": "Paris",
        "category": "Geography"
    },
    {
        "question": "Which animal is known for its black and white stripes?",
        "option1": "Tiger",
        "option2": "Zebra",
        "option3": "Leopard",
        "option4": "Panda",
        "answer": "Zebra",
        "category": "Animals"
    },
    {
        "question": "Which element has the chemical symbol 'O'?",
        "option1": "Gold",
        "option2": "Oxygen",
        "option3": "Osmium",
        "option4": "Silver",
        "answer": "Oxygen",
        "category": "Science"
    }
]

# ---------- File paths ----------
LEADERBOARD_PATH = Path("quiz_leaderboard.csv")

# ---------- Functions ----------
@st.cache_data
def load_questions_from_df(df: pd.DataFrame):
    # Expect columns question, option1..option4, answer, category (category optional)
    questions = []
    for _, row in df.iterrows():
        q = {
            "question": str(row.get("question", "")).strip(),
            "option1": str(row.get("option1", "")).strip(),
            "option2": str(row.get("option2", "")).strip(),
            "option3": str(row.get("option3", "")).strip(),
            "option4": str(row.get("option4", "")).strip(),
            "answer": str(row.get("answer", "")).strip(),
            "category": str(row.get("category", "General")).strip()
        }
        # only include if question text and answer exist
        if q["question"] and q["answer"]:
            questions.append(q)
    return questions

def save_score_to_leaderboard(name, score, total, category):
    row = {"name": name, "score": score, "total": total, "category": category, "time": pd.Timestamp.now()}
    if LEADERBOARD_PATH.exists():
        df = pd.read_csv(LEADERBOARD_PATH)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(LEADERBOARD_PATH, index=False)

def load_leaderboard():
    if LEADERBOARD_PATH.exists():
        return pd.read_csv(LEADERBOARD_PATH)
    return pd.DataFrame(columns=["name","score","total","category","time"])

def reset_quiz_state():
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.user_answers = []
    st.session_state.started = False
    st.session_state.shuffled_order = []

# ---------- Initialize session state ----------
if "questions" not in st.session_state:
    st.session_state.questions = load_questions_from_df(pd.DataFrame(SAMPLE_QUESTIONS))
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "started" not in st.session_state:
    st.session_state.started = False
if "shuffled_order" not in st.session_state:
    st.session_state.shuffled_order = list(range(len(st.session_state.questions)))
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = True
if "per_question_time" not in st.session_state:
    st.session_state.per_question_time = 0  # seconds; 0 means no timer

# ---------- UI layout ----------
st.title("🧠 Fun Quiz — Play & Learn")
st.write("Pick a category, choose number of questions, and have fun! You can also upload your own quiz (CSV).")

# Sidebar: settings
with st.sidebar:
    st.header("Settings")
    categories = ["All"] + sorted({q.get("category","General") for q in st.session_state.questions})
    selected_category = st.selectbox("Category", categories, index=0)
    num_questions = st.number_input("Number of questions", min_value=1, max_value=len(st.session_state.questions), value=min(5, len(st.session_state.questions)))
    st.session_state.show_feedback = st.checkbox("Show immediate feedback after each answer", value=True)
    st.session_state.per_question_time = st.number_input("Timer per question (seconds, 0 = off)", min_value=0, value=0, step=5)
    st.write("---")
    st.header("Upload a quiz (optional)")
    uploaded = st.file_uploader("Upload CSV with columns: question,option1..option4,answer,category", type=["csv"])
    if uploaded is not None:
        try:
            df_uploaded = pd.read_csv(uploaded)
            qlist = load_questions_from_df(df_uploaded)
            if qlist:
                st.success(f"Loaded {len(qlist)} questions from upload.")
                st.session_state.questions = qlist
                # refresh choices for category
                categories = ["All"] + sorted({q.get("category","General") for q in st.session_state.questions})
            else:
                st.warning("Couldn't find valid questions in the file.")
        except Exception as e:
            st.error(f"Failed to read file: {e}")

    st.write("---")
    st.header("Leaderboard")
    lb = load_leaderboard()
    if not lb.empty:
        top = lb.sort_values(by="score", ascending=False).head(5)
        st.table(top[["name","score","total","category","time"]])
    else:
        st.write("No scores yet — be the first!")

# ---------- Prepare filtered question list ----------
if selected_category == "All":
    filtered = st.session_state.questions.copy()
else:
    filtered = [q for q in st.session_state.questions if q.get("category","General") == selected_category]

if not filtered:
    st.warning("No questions for the selected category. Try 'All' or upload a quiz.")
    st.stop()

# Cap number of questions
num_questions = min(num_questions, len(filtered))

# If quiz not started yet: show start screen
if not st.session_state.started:
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.user_answers = []
    st.session_state.shuffled_order = list(range(len(filtered)))
    random.shuffle(st.session_state.shuffled_order)
    # Build the actual quiz list for this run
    st.session_state.active_quiz = [filtered[i] for i in st.session_state.shuffled_order][:num_questions]

    st.subheader("Quiz setup")
    st.write(f"Category: **{selected_category}** • Questions: **{num_questions}**")
    name = st.text_input("Enter your name (for leaderboard)", value="Player")
    start = st.button("Start Quiz ▶️")
    if start:
        st.session_state.started = True
        st.session_state.player_name = name.strip() or "Player"
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.user_answers = []
        # timestamp
        st.session_state.start_time = time.time()
        # shuffle options for each question to reduce memorization
        st.session_state.option_orders = []
        for q in st.session_state.active_quiz:
            opts = [q["option1"], q["option2"], q["option3"], q["option4"]]
            random.shuffle(opts)
            st.session_state.option_orders.append(opts)
        st.experimental_rerun()
    else:
        st.info("When you're ready, press Start Quiz ▶️")
        st.write("Tip: Upload your own quiz CSV to try different questions.")

# ---------- Main quiz flow ----------
if st.session_state.started:
    total_q = len(st.session_state.active_quiz)
    idx = st.session_state.current_q
    q = st.session_state.active_quiz[idx]
    opts = st.session_state.option_orders[idx]

    st.progress((idx)/total_q)
    st.markdown(f"**Question {idx+1} of {total_q}**")
    st.write(f"**{q['question']}**")

    # Timer
    time_left = None
    if st.session_state.per_question_time and st.session_state.per_question_time > 0:
        if f"deadline_{idx}" not in st.session_state:
            st.session_state[f"deadline_{idx}"] = time.time() + st.session_state.per_question_time
        time_left = int(max(0, st.session_state[f"deadline_{idx}"] - time.time()))
        timer_placeholder = st.empty()
        timer_placeholder.markdown(f"⏱ Time left: **{time_left}** s")
    else:
        timer_placeholder = None

    # Show options
    choice = st.radio("Choose an answer:", opts, index=0, key=f"choice_{idx}")
    col1, col2 = st.columns([1,1])
    with col1:
        submit = st.button("Submit", key=f"submit_{idx}")
    with col2:
        skip = st.button("Skip", key=f"skip_{idx}")

    # If timer enabled, force auto-submit when time is up
    if time_left is not None and time_left == 0 and not st.session_state.get(f"answered_{idx}", False):
        st.session_state[f"answered_{idx}"] = True
        st.session_state.user_answers.append({"selected": None, "correct": q["answer"]})
        # no score increment
        st.session_state.current_q += 1
        st.experimental_rerun()

    # Submit handling
    if submit and not st.session_state.get(f"answered_{idx}", False):
        st.session_state[f"answered_{idx}"] = True
        selected = choice
        correct = q["answer"]
        is_correct = selected == correct
        st.session_state.user_answers.append({"selected": selected, "correct": correct, "is_correct": is_correct, "question": q["question"]})
        if is_correct:
            st.session_state.score += 1

        # feedback
        if st.session_state.show_feedback:
            if is_correct:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Wrong. Correct answer: **{correct}**")

    if skip and not st.session_state.get(f"answered_{idx}", False):
        st.session_state[f"answered_{idx}"] = True
        st.session_state.user_answers.append({"selected": None, "correct": q["answer"], "is_correct": False, "question": q["question"]})
        st.session_state.current_q += 1
        st.experimental_rerun()

    # Next button appears after answering
    if st.session_state.get(f"answered_{idx}", False):
        if idx + 1 < total_q:
            if st.button("Next ➜", key=f"next_{idx}"):
                st.session_state.current_q += 1
                st.experimental_rerun()
        else:
            # finished
            if st.button("Finish Quiz 🏁"):
                total_time = int(time.time() - st.session_state.start_time)
                # save to leaderboard
                save_score_to_leaderboard(st.session_state.player_name, st.session_state.score, total_q, selected_category)
                # show results
                st.balloons()
                st.success(f"You scored **{st.session_state.score} / {total_q}** in {total_time} seconds.")
                # detailed report
                df_report = pd.DataFrame(st.session_state.user_answers)
                st.write("### Review")
                if not df_report.empty:
                    def _format_row(r):
                        sel = r.get("selected")
                        corr = r.get("correct")
                        qtext = r.get("question", "")
                        if sel is None:
                            return f"**Q:** {qtext}\n- ❗Skipped — correct: **{corr}**"
                        elif r.get("is_correct"):
                            return f"**Q:** {qtext}\n- ✅ You: **{sel}**"
                        else:
                            return f"**Q:** {qtext}\n- ❌ You: **{sel}** • Correct: **{corr}**"
                    for _, row in df_report.iterrows():
                        st.markdown(_format_row(row))
                # show leaderboard
                st.write("---")
                st.write("### Leaderboard (top scores)")
                lb = load_leaderboard()
                if not lb.empty:
                    st.dataframe(lb.sort_values(by="score", ascending=False).head(10))
                else:
                    st.write("No leaderboard data.")
                # allow download of result CSV
                st.download_button("Download your results (CSV)", df_report.to_csv(index=False).encode('utf-8'), file_name="quiz_results.csv")
                # Reset to allow new run
                if st.button("Play again"):
                    reset_quiz_state()
                    st.experimental_rerun()

# ---------- Footer ----------
st.sidebar.write("---")
st.sidebar.write("Built with ❤️ using Streamlit.")
st.write("---")
st.caption("Tip: For a class project, you can expand this by adding: timed leaderboards (server), images for questions, category-based badges, or a scoring weight per question.")
