import google.generativeai as genai

def initialize_gemini(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

DEBATE_MILESTONES = [
    "Crafting Your Opening Statement",
    "Developing Key Arguments",
    "Anticipating Counter-Arguments",
    "Preparing Rebuttals",
    "Formulating Thought-Provoking Questions",
    "Crafting a Powerful Conclusion",
    "Polishing Your Delivery"
]

def get_debate_guidance_prompt(topic, focus, user_input, is_revision=False):
    base_prompt = f"""
    You are guiding a student in preparing for a debate on: '{topic}'.
    The current focus is: {focus}.
    
    Based on their response: "{user_input}", provide specific feedback and guidance to improve their argument.
    Include:
    1. Strengths of their current argument
    2. Areas for improvement
    3. Suggestions for additional points or evidence
    4. An example of how to phrase a key point more effectively
    
    Keep your language simple and engaging for a 5th to 9th grade student.
    """
    
    if is_revision:
        base_prompt += "\nThis is a revision of the previous response. Focus on refining and improving the arguments further."
    
    base_prompt += "\nEnd with a question asking if they want to further improve this part or if they're ready to move to the next stage."
    
    return base_prompt

def get_debate_structure_prompt(topic, notes):
    return f"""
    Based on the following notes for the debate topic '{topic}', 
    create a structured outline for a debate. Include sections for:
    1. Opening Statement
    2. Main Arguments (at least 3)
    3. Potential Counter-Arguments and Rebuttals
    4. Conclusion
    
    Notes:
    {notes}
    
    Present the structure in a clear, easy-to-follow format suitable for a 5th to 9th grade student.
    """