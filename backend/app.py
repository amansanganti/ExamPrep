from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import pdfplumber

TOPIC_KEYWORDS = {
    "Deadlock": ["deadlock", "circular wait", "starvation"],
    "Process Management": ["process", "thread", "pcb"],
    "CPU Scheduling": ["cpu scheduling", "scheduling", "scheduler"],
    "Memory Management": ["memory", "paging", "segmentation", "virtual memory"],
    "Synchronization": ["semaphore", "mutex", "critical section"]
}
MCQ_BANK = {
    "Deadlock": [
        {
            "q": "Which condition is necessary for deadlock?",
            "options": ["Preemption", "Circular Wait", "Paging", "Scheduling"],
            "answer": "Circular Wait"
        }
    ],
    "CPU Scheduling": [
        {
            "q": "Which scheduling algorithm minimizes waiting time?",
            "options": ["FCFS", "Round Robin", "SJF", "Priority"],
            "answer": "SJF"
        }
    ],
    "Memory Management": [
        {
            "q": "Which technique allows programs larger than memory?",
            "options": ["Paging", "Segmentation", "Virtual Memory", "Swapping"],
            "answer": "Virtual Memory"
        }
    ]
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

def generate_generic_mcq(question, topic):
    return {
        "q": f"What is the best description of {topic}?",
        "options": [
            "It explains a core concept",
            "It defines an algorithm",
            "It is unrelated to the subject",
            "It is a hardware component"
        ],
        "answer": "It explains a core concept"
    }

def generate_mcqs(topic, difficulty):
    if topic in MCQ_BANK:
        return MCQ_BANK[topic]

    base_question = f"Which statement best describes {topic}?"

    if difficulty == "Easy":
        options = [
            f"Basic definition of {topic}",
            "Advanced system design",
            "Hardware architecture",
            "Network protocols"
        ]
        answer = f"Basic definition of {topic}"

    elif difficulty == "Hard":
        options = [
            f"Design considerations of {topic}",
            f"Performance trade-offs in {topic}",
            "Unrelated OS concept",
            "Hardware-level implementation"
        ]
        answer = f"Performance trade-offs in {topic}"

    else:  # Medium
        options = [
            f"Core concept of {topic}",
            "Input devices",
            "Output buffering",
            "BIOS operations"
        ]
        answer = f"Core concept of {topic}"

    return [{
        "q": base_question,
        "options": options,
        "answer": answer
    }]  
        
@app.route("/")
def home():
    return jsonify({
        "status": "Backend running",
        "message": "Exam Question Pattern Analyzer API"
    })

def generate_generic_mcq(question, topic):
    return {
        "q": f"Which statement best describes {topic}?",
        "options": [
            "It is a fundamental concept",
            "It is an advanced algorithm",
            "It is unrelated to the subject",
            "It is a hardware component"
        ],
        "answer": "It is a fundamental concept"
    }

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

        # ✅ 1. ALWAYS initialize
        final_topic = None

        # ✅ 2. Try predefined topics
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in q_lower for kw in keywords):
                final_topic = topic
                break

        # ✅ 3. Fallback topic detection
        if not final_topic:
            final_topic = guess_topic_from_question(original_q)

        # ✅ 4. Absolute safety
        if not final_topic:
            final_topic = "General"

        # ✅ 5. Detect difficulty & type
        difficulty = detect_difficulty(original_q)
        q_type = detect_question_type(original_q)

        # ✅ 6. Generate MCQs (BANK or DYNAMIC)
        if final_topic in MCQ_BANK:
            mcqs = MCQ_BANK[final_topic]
        else:
            mcqs = generate_mcqs(final_topic, difficulty)

        # ✅ 7. Count topics
        topic_count[final_topic] = topic_count.get(final_topic, 0) + 1

        # ✅ 8. Append ONCE
        question_topics.append({
            "question": original_q,
            "topic": final_topic,
            "difficulty": difficulty,
            "type": q_type,
            "mcqs": mcqs
        })

    return jsonify({
        "total_questions": len(question_topics),
        "questions": question_topics,
        "topic_weightage": topic_count
    })

@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files allowed"}), 400

    extracted_text = ""

    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "message": "PDF processed successfully",
        "text": extracted_text
    })

if __name__ == "__main__":
    app.run(debug=True)