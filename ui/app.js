const eventForm = document.getElementById("event-form");
const sheetForm = document.getElementById("sheet-form");
const eventSelect = document.getElementById("event-select");
const configEventSelect = document.getElementById("config-event-select");
const eventMeta = document.getElementById("event-meta");
const leadList = document.getElementById("lead-list");
const leadTemplate = document.getElementById("lead-template");
const instagramIngestForm = document.getElementById("instagram-ingest-form");
const appendSheetRowBtn = document.getElementById("append-sheet-row-btn");
const configForm = document.getElementById("config-form");
const uiLanguageSelect = document.getElementById("ui-language");

const state = { events: [], leads: [] };
const i18n = {
  ko: {
    title: "이벤트 CRM MVP",
    subtitle: "새 행사 생성 → 구글시트 연결 → 자동응답/상담 진행",
    language: "언어",
    save_event: "행사 저장",
    connect_sheet: "시트 연결",
    config_menu: "Config 메뉴 (행사별 답변/상태 규칙)",
    save_config: "Config 저장",
    simulate_lead: "테스트 리드 유입",
    run_auto_reply: "자동응답 실행",
  },
  en: {
    title: "Event CRM MVP",
    subtitle: "Create Event → Connect Google Sheet → Auto-reply / Consulting",
    language: "Language",
    save_event: "Save Event",
    connect_sheet: "Connect Sheet",
    config_menu: "Config Menu (Templates / Status Rules)",
    save_config: "Save Config",
    simulate_lead: "Simulate Lead",
    run_auto_reply: "Run Auto-reply",
  },
  ru: {
    title: "Event CRM MVP",
    subtitle: "Создать событие → Подключить Google Sheet → Автоответ / Консультация",
    language: "Язык",
    save_event: "Сохранить событие",
    connect_sheet: "Подключить таблицу",
    config_menu: "Меню Config (шаблоны / правила статуса)",
    save_config: "Сохранить Config",
    simulate_lead: "Тестовый лид",
    run_auto_reply: "Запустить автоответ",
  },
};

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
  configEventSelect.innerHTML = eventSelect.innerHTML;
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
  const webhook = ev.sheetWebhookUrl ? "Webhook 연결됨" : "Webhook 미연결";
  eventMeta.textContent = `현재 행사: ${ev.name} (${ev.country}) · ${sheet} · ${webhook}`;
}

function loadConfigForm(ev) {
  const cfg = ev?.config || {};
  document.getElementById("tpl-ko").value = cfg.replyTemplates?.ko || "";
  document.getElementById("tpl-en").value = cfg.replyTemplates?.en || "";
  document.getElementById("tpl-ru").value = cfg.replyTemplates?.ru || "";
  document.getElementById("cfg-created-status").value = cfg.statusConfig?.created || "CREATED";
  document.getElementById("cfg-consulting-values").value = (cfg.statusConfig?.consulting || ["IN_PROGRESS", "상담 중"]).join(",");
  document.getElementById("cfg-phone-prefix").value = cfg.phonePrefixToStrip || "p:";
}

function applyI18n(lang) {
  const dict = i18n[lang] || i18n.ko;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (dict[key]) el.textContent = dict[key];
  });
}

async function loadEvents() {
  state.events = await api("/api/events");
  refreshEventOptions();
  if (state.events.length > 0) {
    eventSelect.value = state.events[0].id;
    configEventSelect.value = state.events[0].id;
    loadConfigForm(selectedEvent());
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
  const webhookUrl = document.getElementById("sheet-webhook-url").value.trim();
  if (webhookUrl) {
    await api(`/api/events/${ev.id}/sheet-webhook`, {
      method: "POST",
      body: JSON.stringify({ sheetWebhookUrl: webhookUrl }),
    });
  }
  await loadEvents();
  eventSelect.value = ev.id;
  configEventSelect.value = ev.id;
  refreshMeta();
  alert("시트 연결 저장 완료");
});

configForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const eventId = configEventSelect.value;
  if (!eventId) return alert("행사를 먼저 선택하세요.");
  const consultingValues = document
    .getElementById("cfg-consulting-values")
    .value.split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  await api(`/api/events/${eventId}/config`, {
    method: "POST",
    body: JSON.stringify({
      phonePrefixToStrip: document.getElementById("cfg-phone-prefix").value.trim() || "p:",
      statusConfig: {
        created: document.getElementById("cfg-created-status").value.trim() || "CREATED",
        consulting: consultingValues,
      },
      replyTemplates: {
        ko: document.getElementById("tpl-ko").value.trim(),
        en: document.getElementById("tpl-en").value.trim(),
        ru: document.getElementById("tpl-ru").value.trim(),
      },
    }),
  });
  await loadEvents();
  eventSelect.value = eventId;
  configEventSelect.value = eventId;
  refreshMeta();
  alert("Config 저장 완료");
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

appendSheetRowBtn.addEventListener("click", async () => {
  const ev = selectedEvent();
  if (!ev) return alert("행사를 먼저 생성하세요.");
  if (!ev.sheetUrl) return alert("구글시트 주소를 먼저 연결하세요.");

  await api(`/api/events/${ev.id}/append-instagram-row`, {
    method: "POST",
    body: JSON.stringify({
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
  configEventSelect.value = eventSelect.value;
  refreshMeta();
  loadConfigForm(selectedEvent());
  await loadLeads();
});

configEventSelect.addEventListener("change", () => {
  eventSelect.value = configEventSelect.value;
  refreshMeta();
  loadConfigForm(selectedEvent());
});

uiLanguageSelect.addEventListener("change", () => {
  applyI18n(uiLanguageSelect.value);
});

loadEvents().catch((e) => {
  eventMeta.textContent = `서버 연결 실패: ${e.message}`;
});
applyI18n("ko");
