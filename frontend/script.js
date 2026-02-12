let chart;

const BASE_URL = "https://examprep-v3qu.onrender.com";

function analyze() {
  const text = document.getElementById("inputText").value;

  if (!text.trim()) {
    alert("Please enter text or upload a PDF first");
    return;
  }

  fetch(`${BASE_URL}/analyze-questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  })
    .then(res => res.json())
    .then(data => {
      renderChart(data.topic_weightage);
      renderTable(data.questions);
      renderMCQs(data.questions);
      renderPredictions(data.predictions);
      renderDNA(data.dna_patterns);
      renderStudyPlan(data.study_plan);
    })
    .catch(err => {
      console.error(err);
      alert("Backend error");
    });
}

function renderChart(topicData) {
  if (!topicData) return;

  const labels = Object.keys(topicData);
  const values = Object.values(topicData);

  if (chart) chart.destroy();

  const ctx = document.getElementById("topicChart").getContext("2d");
  chart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Topic Weightage",
        data: values
      }]
    }
  });
}

function renderTable(questions) {
  const table = document.getElementById("resultTable");
  table.innerHTML = "";

  questions.forEach(q => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${q.question}</td>
      <td>${q.topic}</td>
      <td>${q.difficulty}</td>
      <td>${q.type}</td>
    `;
    table.appendChild(row);
  });
}

// ✅ MUST be outside renderTable
function uploadPDF() {
  const fileInput = document.getElementById("pdfFile");

  if (!fileInput || !fileInput.files.length) {
    alert("Please select a PDF file");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  fetch(`${BASE_URL}/upload-pdf`, {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
        return;
      }

      document.getElementById("inputText").value = data.text;
      alert("PDF extracted successfully. Click Analyze.");
    })
    .catch(err => {
      console.error(err);
      alert("PDF upload failed");
    });
}

// File name preview
document.getElementById("pdfFile").addEventListener("change", e => {
  document.getElementById("fileName").innerText =
    e.target.files[0]?.name || "No file selected";
});

// Dark mode
function toggleDarkMode() {
  document.body.classList.toggle("dark");
}

// Insights
function generateInsights(topicData) {
  const list = document.getElementById("insightsList");
  list.innerHTML = "";

  if (!topicData) return;

  const sorted = Object.entries(topicData).sort((a,b)=>b[1]-a[1]);

  list.innerHTML += `<li>🔥 Most repeated topic: <b>${sorted[0][0]}</b></li>`;
  list.innerHTML += `<li>📊 Total topics detected: <b>${sorted.length}</b></li>`;
  list.innerHTML += `<li>📚 Focus recommendation: Revise <b>${sorted[0][0]}</b> first</li>`;
}

// Hook insights after analyze
const originalAnalyze = analyze;
analyze = function () {
  originalAnalyze();
  fetch(`${BASE_URL}/analyze-questions`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ text: inputText.value })
  })
  .then(res => res.json())
  .then(data => generateInsights(data.topic_weightage));
};

// Export PDF
function exportPDF() {
  window.print();
}
function renderMCQs(questions) {
  const container = document.getElementById("mcqContainer");
  container.innerHTML = "";

  questions.forEach((q, index) => {
    if (!q.mcqs || q.mcqs.length === 0) return;

    q.mcqs.forEach(mcq => {
      const div = document.createElement("div");
      div.className = "mcq-box";

      div.innerHTML = `
        <p><strong>Q${index + 1} (${q.topic})</strong>: ${mcq.q}</p>
        <ul>
          ${mcq.options.map(opt => `<li>${opt}</li>`).join("")}
        </ul>
        <p class="answer">✅ Answer: ${mcq.answer}</p>
      `;

      container.appendChild(div);
    });
  });
}
function renderPredictions(predictions) {
  const list = document.getElementById("predictionList");
  list.innerHTML = "";

  predictions.forEach(item => {
    const li = document.createElement("li");
    li.innerHTML = `
      📌 ${item.question}
      <span style="float:right; font-weight:bold; color:#4f46e5;">
        ${item.confidence}%
      </span>
    `;
    list.appendChild(li);
  });
}
function renderDNA(dnaPatterns) {
  const list = document.getElementById("dnaList");
  list.innerHTML = "";

  Object.entries(dnaPatterns).forEach(([dna, count]) => {
    const li = document.createElement("li");
    li.innerText = `${dna} → ${count} times`;
    list.appendChild(li);
  });
}
function renderStudyPlan(plan) {
  const table = document.getElementById("studyPlanTable");
  table.innerHTML = "";

  plan.forEach(p => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${p.topic}</td>
      <td>${p.recommended_hours} hrs</td>
      <td>${p.reason}</td>
    `;
    table.appendChild(row);
  });
}
// dropdown toggle
document.querySelectorAll(".toggle").forEach(header=>{
  header.addEventListener("click",()=>{
    header.parentElement.classList.toggle("collapsed");
  });
});