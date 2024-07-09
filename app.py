import streamlit as st
import json
from datetime import datetime
from ai_config import initialize_gemini, get_debate_guidance_prompt, get_debate_structure_prompt

# Initialize session state
if 'topics' not in st.session_state:
    st.session_state.topics = []
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = None
if 'chat_histories' not in st.session_state:
    st.session_state.chat_histories = {}
if 'notes' not in st.session_state:
    st.session_state.notes = {}
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False
if 'debate_progress' not in st.session_state:
    st.session_state.debate_progress = 0

# App settings
@st.cache_data
def load_settings():
    try:
        return st.secrets["gemini_api_key"]
    except:
        return ""

def save_settings(api_key):
    st.secrets["gemini_api_key"] = api_key

# Main app
def main():
    st.set_page_config(layout="wide", page_title="Aristo - Elevate Your Debate Skills")

    # Application header
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(
            """
            <h1 style='color: #8B4513; text-align: left;'>Aristo - Elevate Your Debate Skills</h1>
            """,
            unsafe_allow_html=True
        )
    with col3:
        if st.button("⚙️ App Settings"):
            st.session_state.show_settings = not st.session_state.show_settings

    if st.session_state.show_settings:
        with st.expander("App Settings", expanded=True):
            api_key = st.text_input("Enter Gemini API Key", value=load_settings(), type="password")
            if st.button("Save API Key"):
                save_settings(api_key)
                st.success("API Key saved successfully!")
                st.experimental_rerun()

    # Main content area
    if st.button("🏠 Home"):
        st.session_state.current_topic = None
        st.experimental_rerun()

    if st.session_state.current_topic:
        show_debate_page()
    else:
        show_topics_page()

def show_topics_page():
    st.header("Welcome to Aristo!")
    st.write("Choose a topic to start your debate preparation.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Your Topics")
        for topic in st.session_state.topics:
            if st.button(f"📌 {topic}", key=f"main_{topic}"):
                st.session_state.current_topic = topic
                st.session_state.debate_progress = 0
                st.experimental_rerun()

        new_topic = st.text_input("Add a new topic")
        if st.button("Add Topic"):
            if new_topic and new_topic not in st.session_state.topics:
                st.session_state.topics.append(new_topic)
                st.experimental_rerun()

    with col2:
        st.subheader("Suggested Topics")
        suggested_topics = [
            "Should homework be banned?",
            "Is social media good for kids?",
            "Should school uniforms be mandatory?",
            "Are video games beneficial or harmful?",
            "Should kids have smartphones?"
        ]
        for topic in suggested_topics:
            col1, col2 = st.columns([3, 1])
            col1.write(f"🔹 {topic}")
            if col2.button("Add", key=f"add_{topic}"):
                if topic not in st.session_state.topics:
                    st.session_state.topics.append(topic)
                    st.experimental_rerun()

from ai_config import initialize_gemini, get_debate_guidance_prompt, get_debate_structure_prompt, DEBATE_MILESTONES

def show_debate_page():
    st.header(f"Current Topic: {st.session_state.current_topic}")

    tab1, tab2 = st.tabs(["Debate Preparation", "Notes"])

    with tab1:
        api_key = load_settings()
        model = initialize_gemini(api_key)
        if not model:
            st.error("Please set up your Gemini API key in the settings.")
            return

        if st.session_state.current_topic not in st.session_state.chat_histories:
            st.session_state.chat_histories[st.session_state.current_topic] = []
        if 'current_focus' not in st.session_state:
            st.session_state.current_focus = 0
        if 'current_response' not in st.session_state:
            st.session_state.current_response = ""

        chat_history = st.session_state.chat_histories[st.session_state.current_topic]

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(chat_history):
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # Debate guidance
        progress = st.progress(st.session_state.current_focus / len(DEBATE_MILESTONES))
        st.subheader(f"Current Focus: {DEBATE_MILESTONES[st.session_state.current_focus]}")

        # User input and feedback area
        with st.container():
            st.markdown("<br>" * 2, unsafe_allow_html=True)  # Add some space
            
            # Callback function to handle form submission
            def handle_submit():
                user_input = st.session_state.user_input
                if user_input:
                    is_revision = len(chat_history) > 0 and chat_history[-1]["role"] == "assistant"
                    chat_history.append({"role": "user", "content": user_input})
                    
                    # Generate AI response
                    prompt = get_debate_guidance_prompt(
                        st.session_state.current_topic,
                        DEBATE_MILESTONES[st.session_state.current_focus],
                        user_input,
                        is_revision
                    )
                    response = model.generate_content(prompt)
                    ai_message = response.text

                    chat_history.append({"role": "assistant", "content": ai_message})
                    st.session_state.current_response = user_input

            # Create a form for user input
            with st.form(key='user_input_form'):
                user_input = st.text_area("Your response", key="user_input", height=150, value=st.session_state.current_response)
                submit_button = st.form_submit_button(label="Get Feedback", on_click=handle_submit)

            # Options after receiving feedback
            if len(chat_history) > 0 and chat_history[-1]["role"] == "assistant":
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Revise Response"):
                        st.session_state.current_response = user_input
                        st.experimental_rerun()
                with col2:
                    if st.button("Complete and Move to Next Stage"):
                        # Add the current response to notes
                        if st.session_state.current_topic not in st.session_state.notes:
                            st.session_state.notes[st.session_state.current_topic] = []
                        st.session_state.notes[st.session_state.current_topic].append(user_input)
                        st.success("Stage completed and added to notes!")
                        
                        # Move to next stage
                        st.session_state.current_focus += 1
                        if st.session_state.current_focus >= len(DEBATE_MILESTONES):
                            st.session_state.current_focus = 0
                            st.success("Congratulations! You've completed all stages. Starting over from the beginning.")
                        st.session_state.current_response = ""
                        st.experimental_rerun()

    with tab2:
        show_notes_page()

def show_notes_page():
    st.subheader(f"Notes for: {st.session_state.current_topic}")

    if st.session_state.current_topic not in st.session_state.notes:
        st.write("No notes available for this topic yet. Add notes during the debate preparation!")
    else:
        for i, note in enumerate(st.session_state.notes[st.session_state.current_topic]):
            st.text_area(f"Note {i+1}", value=note, height=150, key=f"note_{st.session_state.current_topic}_{i}")
        
    new_note = st.text_area("Add a custom note", key=f"new_note_{st.session_state.current_topic}")
    if st.button("Add Custom Note"):
        if new_note:
            if st.session_state.current_topic not in st.session_state.notes:
                st.session_state.notes[st.session_state.current_topic] = []
            st.session_state.notes[st.session_state.current_topic].append(new_note)
            st.success("Custom note added!")
            st.experimental_rerun()

    if st.button("Generate Debate Structure"):
        if st.session_state.current_topic in st.session_state.notes and st.session_state.notes[st.session_state.current_topic]:
            api_key = load_settings()
            model = initialize_gemini(api_key)
            if model:
                notes = "\n".join(st.session_state.notes[st.session_state.current_topic])
                prompt = get_debate_structure_prompt(st.session_state.current_topic, notes)
                response = model.generate_content(prompt)
                st.markdown("## Debate Structure")
                st.write(response.text)
            else:
                st.error("Please set up your Gemini API key in the settings.")
        else:
            st.warning("No notes available. Add some notes during debate preparation to generate a structure.")

    if st.button("Print Notes"):
        notes_text = f"Notes for topic: {st.session_state.current_topic}\n\n"
        for i, note in enumerate(st.session_state.notes.get(st.session_state.current_topic, [])):
            notes_text += f"Note {i+1}:\n{note}\n\n"
        
        st.download_button(
            label="Download Notes",
            data=notes_text,
            file_name=f"debate_notes_{st.session_state.current_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
