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
def predict_questions(topic_count):
    predictions = []

    if not topic_count:
        return predictions

    max_count = max(topic_count.values())

    for topic, count in sorted(topic_count.items(), key=lambda x: x[1], reverse=True):
        # Confidence calculation (relative frequency)
        confidence = int((count / max_count) * 100)

        # Question pattern based on importance
        if count >= 3:
            questions = [
                f"Explain {topic}",
                f"Discuss challenges in {topic}"
            ]
        elif count == 2:
            questions = [f"Describe {topic}"]
        else:
            questions = [f"What is {topic}?"]

        for q in questions:
            predictions.append({
                "question": q,
                "confidence": confidence
            })

    return predictions[:8]  # limit predictions

def generate_study_plan(topic_count, question_data):
    plan = []

    max_count = max(topic_count.values())

    for topic, count in topic_count.items():
        related = [q for q in question_data if q["topic"] == topic]

        hard = any(q["difficulty"] == "Hard" for q in related)

        if count >= max_count * 0.7:
            hours = 2.5 if hard else 2
        elif count >= max_count * 0.4:
            hours = 1.5
        else:
            hours = 1

        plan.append({
            "topic": topic,
            "recommended_hours": hours,
            "reason": "High exam frequency" if count >= max_count * 0.7 else "Moderate exam frequency"
        })

    return sorted(plan, key=lambda x: x["recommended_hours"], reverse=True)

def detect_verb(question):
    q = question.lower()

    verbs = [
        "explain", "describe", "define",
        "compare", "analyze", "discuss",
        "evaluate", "design"
    ]

    for v in verbs:
        if v in q:
            return v.title()

    return "General"        

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

    # 🔁 MAIN LOOP
    for q in raw_questions:
        original_q = q.strip()
        q_lower = original_q.lower()

        if len(q_lower) < 10:
            continue

        # 1️⃣ Topic detection
        final_topic = None
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in q_lower for kw in keywords):
                final_topic = topic
                break

        if not final_topic:
            final_topic = guess_topic_from_question(original_q)

        if not final_topic:
            final_topic = "General"

        # 2️⃣ Other attributes
        difficulty = detect_difficulty(original_q)
        q_type = detect_question_type(original_q)
        verb = detect_verb(original_q)

        # 3️⃣ MCQs
        mcqs = MCQ_BANK.get(final_topic, generate_mcqs(final_topic, difficulty))

        # 4️⃣ Count topic
        topic_count[final_topic] = topic_count.get(final_topic, 0) + 1

        # 5️⃣ DNA
        dna = {
            "topic": final_topic,
            "difficulty": difficulty,
            "type": q_type,
            "verb": verb
        }

        # 6️⃣ Append ONCE
        question_topics.append({
            "question": original_q,
            "topic": final_topic,
            "difficulty": difficulty,
            "type": q_type,
            "verb": verb,
            "dna": dna,
            "mcqs": mcqs
        })

    # 🧬 BUILD DNA PATTERNS (AFTER LOOP)
    dna_patterns = {}
    for q in question_topics:
        key = f"{q['topic']} | {q['difficulty']} | {q['type']} | {q['verb']}"
        dna_patterns[key] = dna_patterns.get(key, 0) + 1

    # 📅 STUDY PLAN
    study_plan = generate_study_plan(topic_count, question_topics)

    # 🔮 PREDICTIONS
    predicted_questions = predict_questions(topic_count)

    return jsonify({
        "total_questions": len(question_topics),
        "questions": question_topics,
        "topic_weightage": topic_count,
        "dna_patterns": dna_patterns,
        "study_plan": study_plan,
        "predictions": predicted_questions
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