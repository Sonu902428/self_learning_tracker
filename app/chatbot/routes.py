from flask import Blueprint, request, jsonify
from app.chatbot.engine import chatbot_response

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/chat", methods=["POST"])
def chat():

    message = request.json.get("message")

    reply = chatbot_response(message)

    return jsonify({"reply": reply})

def route_question(question):

    q = question.lower()

    if "subject" in q:
        return "database"

    if "topic" in q:
        return "system"

    if "chapter" in q or "pdf" in q or "explain" in q:
        return "pdf"

    return "general"