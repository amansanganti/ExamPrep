from flask import Flask, request, jsonify
from flask_cors import CORS
import re

TOPIC_KEYWORDS = {
    "Deadlock": ["deadlock", "circular wait", "starvation"],
    "Process Management": ["process", "thread", "pcb"],
    "CPU Scheduling": ["cpu scheduling", "scheduling", "scheduler"],
    "Memory Management": ["memory", "paging", "segmentation", "virtual memory"],
    "Synchronization": ["semaphore", "mutex", "critical section"]
}

app = Flask(__name__)
CORS(app)

def guess_topic_from_question(question):
    words = re.findall(r"[a-zA-Z]{4,}", question.lower())

    stopwords = {
        "explain", "define", "discuss", "what", "which",
        "describe", "short", "note", "how", "methods"
    }

    keywords = [w for w in words if w not in stopwords]

    if len(keywords) >= 2:
        return f"{keywords[0].title()} {keywords[1].title()}"
    elif len(keywords) == 1:
        return keywords[0].title()
    else:
        return "Other"

def detect_difficulty(question):
    q = question.lower()

    if any(word in q for word in ["compare", "analyze", "design", "evaluate"]):
        return "Hard"
    elif any(word in q for word in ["explain", "describe", "discuss"]):
        return "Medium"
    elif any(word in q for word in ["define", "what is", "list"]):
        return "Easy"
    else:
        return "Medium"


def detect_question_type(question):
    q = question.lower()

    if any(word in q for word in ["calculate", "find", "solve"]):
        return "Numerical"
    elif any(word in q for word in ["compare", "analyze", "justify"]):
        return "Conceptual"
    else:
        return "Theory"
        
@app.route("/")
def home():
    return jsonify({
        "status": "Backend running",
        "message": "Exam Question Pattern Analyzer API"
    })

@app.route("/analyze-questions", methods=["POST"])
def analyze_questions():
    data = request.json
    text = data.get("text", "")

    if not text.strip():
        return jsonify({"error": "No text provided"}), 400

    raw_questions = re.split(r'\?|\.|\n', text)

    topic_count = {}
    question_topics = []

    for q in raw_questions:
        original_q = q.strip()
        q_lower = original_q.lower()

        if len(q_lower) < 10:
            continue

        final_topic = None

        # Try predefined topics first
        for topic, keywords in TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw in q_lower:
                    final_topic = topic
                    break
            if final_topic:
                break

        # Fallback if no topic matched
        if not final_topic:
            final_topic = guess_topic_from_question(original_q)

        # Count topic
        topic_count[final_topic] = topic_count.get(final_topic, 0) + 1

        question_topics.append({
            "question": original_q,
            "topic": final_topic,
            "difficulty": detect_difficulty(original_q),
            "type": detect_question_type(original_q)
        })

    return jsonify({
        "total_questions": len(question_topics),
        "questions": question_topics,
        "topic_weightage": topic_count
    })

if __name__ == "__main__":
    app.run(debug=True)