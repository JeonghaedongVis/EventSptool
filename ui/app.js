const state = {
  events: JSON.parse(localStorage.getItem("events") || "[]"),
  leads: JSON.parse(localStorage.getItem("leads") || "[]"),
};

const eventForm = document.getElementById("event-form");
const sheetForm = document.getElementById("sheet-form");
const eventSelect = document.getElementById("event-select");
const eventMeta = document.getElementById("event-meta");
const leadList = document.getElementById("lead-list");
const leadTemplate = document.getElementById("lead-template");

function persist() {
  localStorage.setItem("events", JSON.stringify(state.events));
  localStorage.setItem("leads", JSON.stringify(state.leads));
}

function selectedEvent() {
  const id = eventSelect.value;
  return state.events.find((e) => e.id === id);
}

function refreshEventOptions() {
  eventSelect.innerHTML = state.events
    .map((e) => `<option value="${e.id}">${e.name}</option>`)
    .join("");
  refreshMeta();
  renderLeads();
}

function refreshMeta() {
  const ev = selectedEvent();
  if (!ev) {
    eventMeta.textContent = "행사를 먼저 생성해 주세요.";
    return;
  }
  const sheet = ev.sheetUrl ? `시트 연결됨: ${ev.sheetUrl}` : "시트 미연결";
  eventMeta.textContent = `현재 행사: ${ev.name} (${ev.country}) · ${sheet}`;
}

function renderLeads() {
  const ev = selectedEvent();
  leadList.innerHTML = "";
  if (!ev) return;

  const leads = state.leads.filter((l) => l.eventId === ev.id);
  if (leads.length === 0) {
    leadList.innerHTML = "<p>아직 리드가 없습니다. 테스트 리드 유입 버튼을 눌러보세요.</p>";
    return;
  }

  leads.forEach((lead) => {
    const node = leadTemplate.content.cloneNode(true);
    node.querySelector(".lead-name").textContent = `${lead.name} (${lead.phone})`;
    node.querySelector(".lead-stage").textContent = lead.stage;
    node.querySelector(".lead-meta").textContent = `관심진료: ${lead.service} · 유입시각: ${lead.createdAt}`;
    node.querySelector(".stage-select").value = lead.stage;
    node.querySelector(".log").textContent = lead.log || "로그 없음";

    node.querySelector(".stage-select").addEventListener("change", (e) => {
      lead.stage = e.target.value;
      lead.log = `상태 변경: ${lead.stage}`;
      persist();
      renderLeads();
    });

    node.querySelectorAll(".quick-buttons button").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        lead.stage = action === "btn_booking_push" ? "booking_push" : "consulting";
        lead.log = `문의응답선택 실행: ${action} → 메시지 전송 완료(모의)`;
        persist();
        renderLeads();
      });
    });

    leadList.appendChild(node);
  });
}

eventForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("event-name").value.trim();
  const country = document.getElementById("event-country").value.trim();
  const service = document.getElementById("default-service").value;
  const newEvent = {
    id: crypto.randomUUID(),
    name,
    country,
    defaultService: service,
    sheetUrl: "",
  };
  state.events.push(newEvent);
  persist();
  refreshEventOptions();
  eventSelect.value = newEvent.id;
  refreshMeta();
  eventForm.reset();
});

sheetForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const ev = selectedEvent();
  if (!ev) return;
  ev.sheetUrl = document.getElementById("sheet-url").value.trim();
  persist();
  refreshMeta();
  alert("시트 연결 저장 완료");
});

document.getElementById("simulate-lead-btn").addEventListener("click", () => {
  const ev = selectedEvent();
  if (!ev) return alert("행사를 먼저 생성하세요.");
  if (!ev.sheetUrl) return alert("구글시트 주소를 먼저 연결하세요.");

  state.leads.push({
    id: crypto.randomUUID(),
    eventId: ev.id,
    name: `리드${Math.floor(Math.random() * 1000)}`,
    phone: "+82-10-1234-5678",
    service: ev.defaultService,
    stage: "new_lead",
    createdAt: new Date().toLocaleString(),
    log: "신규 리드 유입",
  });
  persist();
  renderLeads();
});

document.getElementById("run-auto-reply-btn").addEventListener("click", () => {
  const ev = selectedEvent();
  if (!ev) return;
  const target = state.leads.filter((l) => l.eventId === ev.id && l.stage === "new_lead");
  target.forEach((lead) => {
    lead.stage = "auto_replied";
    lead.log = "자동응답 실행 완료 (모의): 환영 템플릿 발송";
  });
  persist();
  renderLeads();
});

eventSelect.addEventListener("change", () => {
  refreshMeta();
  renderLeads();
});

refreshEventOptions();
