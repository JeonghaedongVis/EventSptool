const eventForm = document.getElementById("event-form");
const sheetForm = document.getElementById("sheet-form");
const eventSelect = document.getElementById("event-select");
const eventMeta = document.getElementById("event-meta");
const leadList = document.getElementById("lead-list");
const leadTemplate = document.getElementById("lead-template");
const instagramIngestForm = document.getElementById("instagram-ingest-form");

const state = { events: [], leads: [] };

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

function selectedEvent() {
  const id = eventSelect.value;
  return state.events.find((e) => e.id === id);
}

function refreshEventOptions() {
  eventSelect.innerHTML = state.events.map((e) => `<option value="${e.id}">${e.name}</option>`).join("");
  refreshMeta();
}

function refreshMeta() {
  const ev = selectedEvent();
  if (!ev) {
    eventMeta.textContent = "행사를 먼저 생성해 주세요.";
    leadList.innerHTML = "";
    return;
  }
  const sheet = ev.sheetUrl ? `시트 연결됨: ${ev.sheetUrl}` : "시트 미연결";
  eventMeta.textContent = `현재 행사: ${ev.name} (${ev.country}) · ${sheet}`;
}

async function loadEvents() {
  state.events = await api("/api/events");
  refreshEventOptions();
  if (state.events.length > 0) {
    eventSelect.value = state.events[0].id;
    await loadLeads();
  }
}

async function loadLeads() {
  const ev = selectedEvent();
  if (!ev) return;
  state.leads = await api(`/api/events/${ev.id}/leads`);
  renderLeads();
}

function renderLeads() {
  const ev = selectedEvent();
  leadList.innerHTML = "";
  if (!ev) return;

  if (state.leads.length === 0) {
    leadList.innerHTML = "<p>아직 리드가 없습니다. 테스트 리드 유입 버튼을 눌러보세요.</p>";
    return;
  }

  state.leads.forEach((lead) => {
    const node = leadTemplate.content.cloneNode(true);
    node.querySelector(".lead-name").textContent = `${lead.name} (${lead.phone})`;
    node.querySelector(".lead-stage").textContent = lead.stage;
    node.querySelector(".lead-meta").textContent = `관심진료: ${lead.service} · 유입시각: ${lead.createdAt}`;
    node.querySelector(".stage-select").value = lead.stage;
    node.querySelector(".log").textContent = lead.log || "로그 없음";

    node.querySelector(".stage-select").addEventListener("change", async (e) => {
      await api(`/api/leads/${lead.id}/stage`, {
        method: "POST",
        body: JSON.stringify({ stage: e.target.value }),
      });
      await loadLeads();
    });

    node.querySelectorAll(".quick-buttons button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await api(`/api/leads/${lead.id}/quick-action`, {
          method: "POST",
          body: JSON.stringify({ action: btn.dataset.action }),
        });
        await loadLeads();
      });
    });

    leadList.appendChild(node);
  });
}

eventForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  await api("/api/events", {
    method: "POST",
    body: JSON.stringify({
      name: document.getElementById("event-name").value.trim(),
      country: document.getElementById("event-country").value.trim(),
      defaultService: document.getElementById("default-service").value,
    }),
  });
  eventForm.reset();
  await loadEvents();
});

sheetForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const ev = selectedEvent();
  if (!ev) return;
  await api(`/api/events/${ev.id}/sheet`, {
    method: "POST",
    body: JSON.stringify({ sheetUrl: document.getElementById("sheet-url").value.trim() }),
  });
  await loadEvents();
  eventSelect.value = ev.id;
  refreshMeta();
  alert("시트 연결 저장 완료");
});

document.getElementById("simulate-lead-btn").addEventListener("click", async () => {
  const ev = selectedEvent();
  if (!ev) return alert("행사를 먼저 생성하세요.");
  if (!ev.sheetUrl) return alert("구글시트 주소를 먼저 연결하세요.");
  await api(`/api/events/${ev.id}/leads`, { method: "POST", body: JSON.stringify({}) });
  await loadLeads();
});

document.getElementById("run-auto-reply-btn").addEventListener("click", async () => {
  for (const lead of state.leads.filter((l) => l.stage === "new_lead")) {
    await api(`/api/leads/${lead.id}/auto-reply`, { method: "POST", body: JSON.stringify({}) });
  }
  await loadLeads();
});

instagramIngestForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const ev = selectedEvent();
  if (!ev) return alert("행사를 먼저 생성하세요.");
  if (!ev.sheetUrl) return alert("구글시트 주소를 먼저 연결하세요.");

  await api("/api/ingest/instagram-new", {
    method: "POST",
    body: JSON.stringify({
      eventId: ev.id,
      created_time: document.getElementById("ig-created-time").value.trim(),
      platform: document.getElementById("ig-platform").value.trim(),
      phone_number: document.getElementById("ig-phone").value.trim(),
      full_name: document.getElementById("ig-full-name").value.trim(),
      lead_status: document.getElementById("ig-lead-status").value.trim(),
    }),
  });
  instagramIngestForm.reset();
  await loadLeads();
});

eventSelect.addEventListener("change", async () => {
  refreshMeta();
  await loadLeads();
});

loadEvents().catch((e) => {
  eventMeta.textContent = `서버 연결 실패: ${e.message}`;
});
