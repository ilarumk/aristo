import streamlit as st
from datetime import datetime
from ai_config import initialize_gemini, get_initial_guidance_prompt, get_debate_guidance_prompt, get_debate_structure_prompt, DEBATE_MILESTONES

# Get the API key
def get_api_key():
    if 'user_api_key' in st.session_state:
        return st.session_state.user_api_key
    elif 'gemini_api_key' in st.secrets:
        return st.secrets.gemini_api_key
    return None

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
        if st.button("⚙️ Settings"):
            st.session_state.show_settings = not st.session_state.get('show_settings', False)

    if st.session_state.get('show_settings', False):
        with st.expander("Settings", expanded=True):
            new_api_key = st.text_input("Enter your Gemini API Key (optional)", type="password")
            if st.button("Save API Key"):
                if new_api_key:
                    st.session_state.user_api_key = new_api_key
                    st.success("API Key saved for this session!")
                else:
                    st.warning("No API key entered. Using the default key if available.")
                st.session_state.show_settings = False
                st.experimental_rerun()

    # Get the API key
    api_key = get_api_key()
    if not api_key:
        st.error("No API key available. Please enter a Gemini API key in the settings or set it in Streamlit secrets.")
        return

    # Initialize Gemini model
    model = initialize_gemini(api_key)

    # Main content area
    if st.button("🏠 Home"):
        st.session_state.current_topic = None
        st.experimental_rerun()

    if 'current_topic' not in st.session_state or st.session_state.current_topic is None:
        show_topics_page()
    else:
        show_debate_page(model)

def show_topics_page():
    st.header("Welcome to Aristo!")
    st.write("Choose a topic to start your debate preparation.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Your Topics")
        if 'topics' not in st.session_state:
            st.session_state.topics = []
        for topic in st.session_state.topics:
            if st.button(f"📌 {topic}", key=f"main_{topic}"):
                st.session_state.current_topic = topic
                st.session_state.current_focus = 0
                st.session_state.current_responses = {}
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

def show_debate_page(model):
    st.header(f"Current Topic: {st.session_state.current_topic}", divider='rainbow')

    # Progress indicator
    progress = st.progress(st.session_state.current_focus / len(DEBATE_MILESTONES))
    st.subheader(f"Current Focus: {DEBATE_MILESTONES[st.session_state.current_focus]}")

    tab1, tab2 = st.tabs(["Debate Preparation", "Notes"])

    with tab1:
        if st.session_state.current_topic not in st.session_state.get('chat_histories', {}):
            st.session_state.chat_histories = {st.session_state.current_topic: []}
        if 'current_focus' not in st.session_state:
            st.session_state.current_focus = 0
        if 'current_responses' not in st.session_state:
            st.session_state.current_responses = {}
        if 'initial_guidance' not in st.session_state:
            st.session_state.initial_guidance = ""

        chat_history = st.session_state.chat_histories[st.session_state.current_topic]

        # Initial guidance
        if not st.session_state.initial_guidance:
            initial_prompt = get_initial_guidance_prompt(st.session_state.current_topic, DEBATE_MILESTONES[st.session_state.current_focus])
            st.session_state.initial_guidance = model.generate_content(initial_prompt).text

        st.write("Initial Guidance:")
        st.info(st.session_state.initial_guidance)

        # Display chat history for current focus
        chat_container = st.container()
        with chat_container:
            for message in chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # User input and feedback area
        with st.container():
            # Create a form for user input
            with st.form(key='user_input_form'):
                user_input = st.text_area(
                    "Your response", 
                    key=f"user_input_{st.session_state.current_focus}",
                    height=150, 
                    value=st.session_state.current_responses.get(st.session_state.current_focus, "")
                )
                submit_button = st.form_submit_button(label="Get Feedback")

            if submit_button and user_input:
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
                
                # Display the new feedback
                with chat_container.chat_message("assistant"):
                    st.write(ai_message)

            # Always update current_responses with the latest user input
            st.session_state.current_responses[st.session_state.current_focus] = user_input

        # Navigation buttons at the bottom
        st.markdown("<br>" * 2, unsafe_allow_html=True)  # Add some space
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Previous Stage", disabled=(st.session_state.current_focus == 0)):
                st.session_state.current_focus = max(0, st.session_state.current_focus - 1)
                st.session_state.initial_guidance = ""
                st.session_state.chat_histories[st.session_state.current_topic] = []
                st.experimental_rerun()
        with col3:
            next_button_label = "Finalize" if st.session_state.current_focus == len(DEBATE_MILESTONES) - 1 else "Complete and Move to Next Stage ➡️"
            if st.button(next_button_label, type="primary"):
                # Add the current response to notes
                if st.session_state.current_topic not in st.session_state.get('notes', {}):
                    st.session_state.notes = {st.session_state.current_topic: []}
                # Save the final user input to notes
                current_notes = st.session_state.notes[st.session_state.current_topic]
                current_response = st.session_state.current_responses.get(st.session_state.current_focus, "")
                if st.session_state.current_focus < len(current_notes):
                    current_notes[st.session_state.current_focus] = f"{DEBATE_MILESTONES[st.session_state.current_focus]}: {current_response}"
                else:
                    current_notes.append(f"{DEBATE_MILESTONES[st.session_state.current_focus]}: {current_response}")
                st.success("Stage completed and added to notes!")
                
                # Move to next stage or finalize
                if st.session_state.current_focus < len(DEBATE_MILESTONES) - 1:
                    st.session_state.current_focus += 1
                    st.session_state.initial_guidance = ""
                    st.session_state.chat_histories[st.session_state.current_topic] = []
                else:
                    st.success("Congratulations! You've completed all stages. Please check the Notes tab to generate your debate structure.")
                st.experimental_rerun()

    with tab2:
        show_notes_page(model)

def show_notes_page(model):
    st.subheader(f"Notes for: {st.session_state.current_topic}")

    if st.session_state.current_topic not in st.session_state.get('notes', {}):
        st.write("No notes available for this topic yet. Complete the debate preparation stages to generate notes!")
    else:
        for i, note in enumerate(st.session_state.notes[st.session_state.current_topic]):
            st.text_area(f"Note {i+1}", value=note, height=150, key=f"note_{st.session_state.current_topic}_{i}")
        
    new_note = st.text_area("Add a custom note", key=f"new_note_{st.session_state.current_topic}")
    if st.button("Add Custom Note"):
        if new_note:
            if st.session_state.current_topic not in st.session_state.get('notes', {}):
                st.session_state.notes = {st.session_state.current_topic: []}
            st.session_state.notes[st.session_state.current_topic].append(new_note)
            st.success("Custom note added!")
            st.experimental_rerun()

    if st.button("Generate Debate Summary"):
        if st.session_state.current_topic in st.session_state.get('notes', {}) and st.session_state.notes[st.session_state.current_topic]:
            notes = "\n".join(st.session_state.notes[st.session_state.current_topic])
            prompt = get_debate_structure_prompt(st.session_state.current_topic, notes)
            response = model.generate_content(prompt)
            debate_summary = response.text
            st.markdown("## Debate Summary")
            st.write(debate_summary)
            
            # Save the debate summary for the current user
            if 'debate_summaries' not in st.session_state:
                st.session_state.debate_summaries = {}
            st.session_state.debate_summaries[st.session_state.current_topic] = debate_summary
            st.success("Debate summary generated and saved!")
        else:
            st.warning("No notes available. Complete the debate preparation stages to generate a summary.")

    if st.button("Print Notes and Debate Summary"):
        notes_text = f"Notes for topic: {st.session_state.current_topic}\n\n"
        for i, note in enumerate(st.session_state.notes.get(st.session_state.current_topic, [])):
            notes_text += f"Note {i+1}:\n{note}\n\n"
        
        if 'debate_summaries' in st.session_state and st.session_state.current_topic in st.session_state.debate_summaries:
            notes_text += f"\nDebate Summary:\n{st.session_state.debate_summaries[st.session_state.current_topic]}\n"
        
        st.download_button(
            label="Download Notes and Debate Summary",
            data=notes_text,
            file_name=f"debate_notes_and_summary_{st.session_state.current_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()