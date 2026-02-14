const form = document.getElementById("diary-form");
const formMessage = document.getElementById("form-message");
const entryList = document.getElementById("entry-list");
const emptyMessage = document.getElementById("empty-message");
const refreshBtn = document.getElementById("refresh-btn");

function renderEntries(entries) {
  entryList.innerHTML = "";

  if (!entries.length) {
    emptyMessage.style.display = "block";
    return;
  }

  emptyMessage.style.display = "none";

  entries.forEach((entry) => {
    const item = document.createElement("li");
    item.className = "entry-item";
    item.innerHTML = `
      <div class="entry-meta"><strong>${entry.student_name}</strong> · ${entry.created_at}</div>
      <div class="entry-content">${entry.content}</div>
    `;
    entryList.appendChild(item);
  });
}

async function loadEntries() {
  const response = await fetch("/api/entries");
  const data = await response.json();
  renderEntries(data.entries || []);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  const response = await fetch("/api/entries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    formMessage.style.color = "#b91c1c";
    formMessage.textContent = data.error || "저장 중 오류가 발생했습니다.";
    return;
  }

  formMessage.style.color = "#047857";
  formMessage.textContent = data.message;
  form.reset();
  await loadEntries();
});

refreshBtn.addEventListener("click", loadEntries);

loadEntries();
