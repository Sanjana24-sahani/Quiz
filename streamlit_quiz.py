import streamlit as st

st.set_page_config(page_title="Friends Fun Quiz", page_icon="😄")

st.title("😄 Friends Group Fun Quiz")

# ---------- FIXED FRIEND LIST ----------
friends = [
    "Akshat",
    "Sonali",
    "Deepanshu",
    "Sanjana",
]

# ---------- QUESTIONS ----------
questions = [
    "Group me sabse zyada late kaun aata hai? 😄",
    "Kaun aisa hai jo phone bina charge ke ghar se nikal hi nahi sakta? 📱",
    "Agar group ka road trip plan fail ho, to uski sabse badi wajah kaun hoga? 😂",
    "Kaun sabse zyada food lover hai 🍕",
    "Group me sabse zyada dramatic reactions kaun deta/deti hai? 🎭",
    "Kaun sabse zyada neend ka shikaar rehta hai? 😴",
    "Kaun bina soche sabse pehle 'haan' bol deta hai?",
    "Kaun sabse zyada pagalpan ke ideas deta hai? 🤪",
    "Kaun sirf reels dekhne ke liye phone uthata hai? 📱"
]

# ---------- SESSION STATE ----------
if "submitted_users" not in st.session_state:
    st.session_state.submitted_users = set()

if "all_answers" not in st.session_state:
    st.session_state.all_answers = []

# ---------- STEP 1: ENTER NAME ----------
st.header("✍️ Enter Your Name")
user_name = st.text_input("Your name")

# ---------- STEP 2: QUESTIONS ----------
if user_name and user_name not in st.session_state.submitted_users:
    st.header("📝 Answer the Questions")

    user_answers = {}
    for i, q in enumerate(questions):
        user_answers[q] = st.radio(
            q,
            friends,
            key=f"{user_name}_{i}"
        )

    if st.button("✅ Submit Answers"):
        st.session_state.all_answers.append({
            "user": user_name,
            "answers": user_answers
        })
        st.session_state.submitted_users.add(user_name)
        st.success("Answers submitted successfully! 🎉")

# ---------- STEP 3: SHOW RESULTS AFTER SUBMISSION ----------
if user_name in st.session_state.submitted_users:
    st.divider()
    st.header("📊 All Participants' Answers")

    for entry in st.session_state.all_answers:
        st.subheader(f"👤 {entry['user']}")
        for q, a in entry["answers"].items():
            st.write(f"**{q}** → {a}")
        st.divider()
