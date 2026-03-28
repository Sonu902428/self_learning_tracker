# import json
# from pathlib import Path
# # from openai import OpenAI

# from app.chatbot.tools import get_subject_count, get_topic_count
# # client = OpenAI()


# def handle_special_queries(message):

#     msg = message.lower()

#     if "how many subjects" in msg:
#         return f"You have {get_subject_count()} subjects."

#     if "how many topics" in msg:
#         return f"You have {get_topic_count()} topics."

#     return None


# knowledge = json.load(open(Path(__file__).parent / "knowledge.json"))

# def ask_ai(user_message, context=""):

#     system_prompt = f"""
#     You are an AI assistant for LearnTrack SaaS platform.

#     Knowledge:
#     {knowledge}

#     Context:
#     {context}
#     """

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_message}
#         ]
#     )

#     return response.choices[0].message.content



# def chatbot_response(message):

#     special = handle_special_queries(message)

#     if special:
#         return special

#     return ask_ai(message)

import json
from pathlib import Path
from app.chatbot.tools import get_subject_count, get_topic_count,count_topic_in_subject
from app.models import Topic, Subject

data = json.load(open(Path(__file__).parent / "knowledge.json"))

def chatbot_response(message):

    msg = message.lower()

    if "topic" in msg and "in" in msg:

        subject_name = msg.split("in", 1)[-1].strip()

        count = count_topic_in_subject(subject_name)

        return f"You have {count} topics in {subject_name}"
    # database queries
    if "how many subjects" in msg:
        return f"You have {get_subject_count()} subjects."

    if "how many topics" in msg:
        return f"You have {get_topic_count()} topics."

    
  

    # knowledge responses
    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            if pattern in msg:
                return intent["response"]

    return "Sorry, I didn't understand. Please ask about LearnTrack."




# from chatbot.routes import route_question
# from chatbot.tools import get_subject_count, get_topic_count
# from chatbot.prompts import search_pdf


# def chatbot(question):

#     route = route_question(question)

#     if route == "database":
#         return get_subject_count()

#     if route == "system":
#         return get_topic_count()

#     if route == "pdf":
#         return search_pdf(question)

#     return "I am not sure about that."