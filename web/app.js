"use strict";

const MINIMUM_AGE = 14;

// ---------------------------------------------------------------------
// State
// ---------------------------------------------------------------------
const state = {
  view: "main",
  capturedBlob: null,
  mediaStream: null,
  currentName: null,
};

const history = []; // simple back-stack of view names

// ---------------------------------------------------------------------
// API layer
// ---------------------------------------------------------------------
const API_BASE = ""; // same-origin: FastAPI serves this page too

function userMessageForDetail(detail, status) {
  switch (detail) {
    case "face_not_detected":
      return "얼굴을 인식하지 못했습니다. 정면을 바라보고 다시 시도해주세요.";
    case "low_quality_face":
      return "사진이 너무 흐릿합니다. 밝은 곳에서 정면으로 다시 촬영해주세요.";
    case "consent_required":
      return "개인정보 수집에 동의해야 등록할 수 있습니다.";
    case "age_restricted":
      return "만 14세 미만은 가입할 수 없습니다.";
    case "name_already_registered":
      return "이미 등록된 사용자 ID입니다.";
    case "user_not_found":
      return "등록된 사용자 정보를 찾을 수 없습니다.";
    case "invalid_image":
      return "이미지를 처리할 수 없습니다. 다시 촬영해주세요.";
    default:
      return detail || `요청을 처리하지 못했습니다. (HTTP ${status})`;
  }
}

async function apiRequest(path, { method = "GET", body } = {}) {
  try {
    const response = await fetch(API_BASE + path, { method, body });
    if (response.ok) {
      return { ok: true, data: await response.json() };
    }
    let detail = null;
    try {
      detail = (await response.json()).detail;
    } catch (e) {
      /* no JSON body */
    }
    return { ok: false, message: userMessageForDetail(detail, response.status) };
  } catch (e) {
    return { ok: false, message: "서버에 연결할 수 없습니다. 네트워크와 서버 주소를 확인해주세요." };
  }
}

function authenticateFace(blob) {
  const form = new FormData();
  form.append("image", blob, "face.jpg");
  return apiRequest("/auth/face", { method: "POST", body: form });
}

function registerUser(fields, blob) {
  const form = new FormData();
  form.append("name", fields.name);
  form.append("age", String(fields.age));
  form.append("nickname", fields.nickname);
  form.append("gender", fields.gender);
  form.append("height_cm", String(fields.heightCm));
  if (fields.weightKg !== null && fields.weightKg !== undefined) {
    form.append("weight_kg", String(fields.weightKg));
  }
  form.append("consent", fields.consent ? "true" : "false");
  form.append("image", blob, "face.jpg");
  return apiRequest("/users/register", { method: "POST", body: form });
}

function getUser(name) {
  return apiRequest(`/users/${encodeURIComponent(name)}`);
}

function latestHeartRate(name) {
  return apiRequest(`/users/${encodeURIComponent(name)}/heart-rate/latest`);
}

function heartRateHistory(name) {
  return apiRequest(`/users/${encodeURIComponent(name)}/heart-rate/history`);
}

function measureHeartRate(name) {
  return apiRequest(`/users/${encodeURIComponent(name)}/heart-rate/measure`, { method: "POST" });
}

// ---------------------------------------------------------------------
// Heart rate status helpers
// ---------------------------------------------------------------------
function heartStatusFor(bpm) {
  if (bpm == null) return { key: "unknown", label: "측정 전" };
  if (bpm < 60) return { key: "warning", label: "서맥" };
  if (bpm > 100) return { key: "warning", label: "빈맥" };
  return { key: "normal", label: "정상" };
}

function solutionMessageFor(statusKey) {
  switch (statusKey) {
    case "warning":
      return "운동 중이신가요? 숨을 고르거나, 당뇨 등 지병이 있다면 주의하세요.";
    case "normal":
      return "현재 심박수는 정상 범위입니다.";
    default:
      return "심박수 측정 기능은 준비 중입니다.";
  }
}

// ---------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------
const titles = {
  main: "메인화면",
  scan: "얼굴 인식 중",
  register: "회원가입",
  registerSuccess: "등록 완료",
  profile: "얼굴 인식 완료",
  history: "전체기록",
};

function showView(name, { pushHistory = true, replaceHistory = false } = {}) {
  if (name === "scan") {
    stopCamera(); // always restart fresh
  } else if (state.view === "scan") {
    stopCamera();
  }

  if (pushHistory && state.view !== name) {
    if (replaceHistory) {
      history.length = 0;
    } else {
      history.push(state.view);
    }
  }

  state.view = name;
  document.querySelectorAll(".view").forEach((el) => el.classList.remove("active"));
  document.getElementById(`view-${name}`).classList.add("active");
  document.getElementById("pageTitle").textContent = titles[name];
  document.getElementById("backBtn").style.display = history.length > 0 ? "block" : "none";

  if (name === "scan") startCamera();
  if (name === "profile") loadProfile();
  if (name === "history") loadHistory();
}

function goBack() {
  const prev = history.pop();
  if (prev) showView(prev, { pushHistory: false });
}

function goHome() {
  showView("main", { replaceHistory: true });
}

// ---------------------------------------------------------------------
// Menu
// ---------------------------------------------------------------------
const dropdown = document.getElementById("dropdownMenu");
document.getElementById("menuBtn").addEventListener("click", (e) => {
  e.stopPropagation();
  dropdown.classList.toggle("open");
});
document.addEventListener("click", () => dropdown.classList.remove("open"));
document.getElementById("menuHome").addEventListener("click", () => {
  dropdown.classList.remove("open");
  goHome();
});
document.getElementById("menuAbout").addEventListener("click", () => {
  dropdown.classList.remove("open");
  alert("얼굴·홍채·rPPG 기반 멀티모달 인증 시스템 데모 앱");
});
document.getElementById("backBtn").addEventListener("click", goBack);

// ---------------------------------------------------------------------
// MAIN
// ---------------------------------------------------------------------
document.getElementById("startScanBtn").addEventListener("click", () => showView("scan"));

// ---------------------------------------------------------------------
// SCAN (camera)
// ---------------------------------------------------------------------
const video = document.getElementById("cameraVideo");
const cameraMessage = document.getElementById("cameraMessage");
const captureBtn = document.getElementById("captureBtn");
const scanOverlay = document.getElementById("scanOverlay");
const scanError = document.getElementById("scanError");
const scanSuccessOverlay = document.getElementById("scanSuccessOverlay");
const irisMatchRow = document.getElementById("irisMatchRow");
const irisMatchLabel = document.getElementById("irisMatchLabel");

async function startCamera() {
  scanError.style.display = "none";
  cameraMessage.style.display = "none";
  captureBtn.disabled = true;

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showCameraMessage("이 브라우저에서는 카메라를 사용할 수 없습니다.");
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });
    state.mediaStream = stream;
    video.srcObject = stream;
    video.style.display = "block";
    captureBtn.disabled = false;
  } catch (err) {
    showCameraMessage("카메라 권한이 필요합니다. 브라우저 주소창의 카메라 아이콘에서 허용해주세요.");
  }
}

function showCameraMessage(text) {
  video.style.display = "none";
  cameraMessage.textContent = text;
  cameraMessage.style.display = "flex";
  captureBtn.disabled = true;
}

function stopCamera() {
  if (state.mediaStream) {
    state.mediaStream.getTracks().forEach((t) => t.stop());
    state.mediaStream = null;
  }
  video.srcObject = null;
}

captureBtn.addEventListener("click", async () => {
  scanError.style.display = "none";
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  // Mirror horizontally so the saved photo matches what the user saw.
  ctx.translate(canvas.width, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
  if (!blob) return;

  scanOverlay.style.display = "flex";
  captureBtn.disabled = true;

  const result = await authenticateFace(blob);

  scanOverlay.style.display = "none";
  captureBtn.disabled = false;

  if (!result.ok) {
    scanError.textContent = result.message;
    scanError.style.display = "block";
    return;
  }

  const data = result.data;
  if (data.authenticated && data.name) {
    state.currentName = data.name;

    // 얼굴 인증이 최종 판정을 내리고, 같은 사진에서 함께 계산된 홍채
    // 일치 여부는 보조 정보로 잠깐 함께 보여준다.
    const irisMatched = !!(data.iris && data.iris.matched);
    irisMatchRow.classList.toggle("matched", irisMatched);
    irisMatchRow.classList.toggle("unmatched", !irisMatched);
    irisMatchLabel.textContent = irisMatched ? "홍채 인증 일치" : "홍채 인증 불일치";
    scanSuccessOverlay.style.display = "flex";

    await new Promise((resolve) => setTimeout(resolve, 700));
    scanSuccessOverlay.style.display = "none";

    showView("profile", { replaceHistory: true });
  } else if (data.reason === "face_not_detected") {
    scanError.textContent = "얼굴을 인식하지 못했습니다. 정면을 바라보고 다시 촬영해주세요.";
    scanError.style.display = "block";
  } else {
    state.capturedBlob = blob;
    resetRegisterForm();
    showView("register");
  }
});

// ---------------------------------------------------------------------
// REGISTER
// ---------------------------------------------------------------------
const regName = document.getElementById("regName");
const regAge = document.getElementById("regAge");
const regNickname = document.getElementById("regNickname");
const regHeight = document.getElementById("regHeight");
const regWeight = document.getElementById("regWeight");
const regConsent = document.getElementById("regConsent");
const genderM = document.getElementById("genderM");
const genderF = document.getElementById("genderF");
const ageHint = document.getElementById("ageHint");
const registerPhotoWarning = document.getElementById("registerPhotoWarning");
const registerError = document.getElementById("registerError");
const submitRegisterBtn = document.getElementById("submitRegisterBtn");

let selectedGender = "M";
genderM.addEventListener("click", () => setGender("M"));
genderF.addEventListener("click", () => setGender("F"));
function setGender(g) {
  selectedGender = g;
  genderM.classList.toggle("selected", g === "M");
  genderF.classList.toggle("selected", g === "F");
}

function resetRegisterForm() {
  regName.value = "";
  regAge.value = "";
  regNickname.value = "";
  regHeight.value = "";
  regWeight.value = "";
  regConsent.checked = false;
  setGender("M");
  registerError.style.display = "none";
  registerPhotoWarning.style.display = state.capturedBlob ? "none" : "block";
  validateRegisterForm();
}

function validateRegisterForm() {
  const age = parseInt(regAge.value, 10);
  const isUnderAge = !isNaN(age) && age < MINIMUM_AGE;
  ageHint.style.display = isUnderAge ? "block" : "none";

  const weightRaw = regWeight.value.trim();
  const weightValid = weightRaw === "" || !isNaN(parseFloat(weightRaw));

  const valid =
    regName.value.trim() !== "" &&
    regNickname.value.trim() !== "" &&
    !isNaN(age) &&
    !isUnderAge &&
    regHeight.value.trim() !== "" &&
    !isNaN(parseFloat(regHeight.value)) &&
    weightValid &&
    regConsent.checked &&
    !!state.capturedBlob;

  submitRegisterBtn.disabled = !valid;
  return valid;
}

[regName, regAge, regNickname, regHeight, regWeight].forEach((el) =>
  el.addEventListener("input", validateRegisterForm)
);
regConsent.addEventListener("change", validateRegisterForm);

submitRegisterBtn.addEventListener("click", async () => {
  if (!validateRegisterForm()) return;

  const weightRaw = regWeight.value.trim();
  const fields = {
    name: regName.value.trim(),
    age: parseInt(regAge.value, 10),
    nickname: regNickname.value.trim(),
    gender: selectedGender,
    heightCm: parseFloat(regHeight.value),
    weightKg: weightRaw === "" ? null : parseFloat(weightRaw),
    consent: regConsent.checked,
  };

  submitRegisterBtn.disabled = true;
  submitRegisterBtn.textContent = "저장 중...";

  const result = await registerUser(fields, state.capturedBlob);

  submitRegisterBtn.textContent = "저장하기";

  if (!result.ok) {
    registerError.textContent = result.message;
    registerError.style.display = "block";
    submitRegisterBtn.disabled = false;
    return;
  }

  state.currentName = result.data.name;
  document.getElementById("successMessage").textContent = `환영합니다, ${fields.nickname}님`;
  showView("registerSuccess", { replaceHistory: true });
});

document.getElementById("successConfirmBtn").addEventListener("click", () => {
  showView("profile", { replaceHistory: true });
});

// ---------------------------------------------------------------------
// PROFILE
// ---------------------------------------------------------------------
async function loadProfile() {
  const loading = document.getElementById("profileLoading");
  const content = document.getElementById("profileContent");
  const errorEl = document.getElementById("profileError");
  loading.style.display = "flex";
  content.style.display = "none";
  errorEl.style.display = "none";

  const result = await getUser(state.currentName);

  loading.style.display = "none";

  if (!result.ok) {
    errorEl.textContent = result.message;
    errorEl.style.display = "block";
    return;
  }

  const profile = result.data;
  content.style.display = "block";

  document.getElementById("profileNickname").textContent = profile.nickname || profile.name;
  document.getElementById("profileSub").textContent =
    `${profile.name} · ${profile.age}세 · ${profile.gender === "M" ? "남성" : "여성"}`;
  document.getElementById("profileHeight").textContent = `${Math.round(profile.height_cm)}cm`;
  document.getElementById("profileWeight").textContent =
    profile.weight_kg != null ? `${Math.round(profile.weight_kg)}kg` : "-";

  await refreshHeartRateCard();
}

function sourceLabel(source) {
  switch (source) {
    case "galaxy_watch":
      return "갤럭시 워치로 측정됨";
    case "apple_watch":
      return "애플 워치로 측정됨";
    default:
      return "워치로 측정됨";
  }
}

async function refreshHeartRateCard() {
  const heartCard = document.getElementById("heartCard");
  const heartValue = document.getElementById("heartValue");
  const heartSource = document.getElementById("heartSource");
  const heartSolution = document.getElementById("heartSolution");

  const result = await latestHeartRate(state.currentName);
  let bpm = null;
  let available = false;
  let source = null;
  if (result.ok) {
    bpm = result.data.bpm;
    available = result.data.available;
    source = result.data.source;
  }

  const status = heartStatusFor(available ? bpm : null);
  heartCard.className = "heart-card" + (status.key !== "unknown" ? ` status-${status.key}` : "");
  heartValue.textContent = available && bpm != null ? `${Math.round(bpm)} bpm · ${status.label}` : "측정 준비 중입니다";
  heartSource.textContent = available && source ? sourceLabel(source) : "";
  heartSource.style.display = available && source ? "block" : "none";
  heartSolution.textContent = solutionMessageFor(status.key);
}

document.getElementById("measureBtn").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  btn.disabled = true;
  btn.textContent = "측정 중...";
  await measureHeartRate(state.currentName);
  await refreshHeartRateCard();
  btn.disabled = false;
  btn.textContent = "심박수 측정";
});

document.getElementById("viewHistoryBtn").addEventListener("click", () => showView("history"));

// ---------------------------------------------------------------------
// HISTORY
// ---------------------------------------------------------------------
async function loadHistory() {
  const loading = document.getElementById("historyLoading");
  const empty = document.getElementById("historyEmpty");
  const list = document.getElementById("historyList");
  loading.style.display = "flex";
  empty.style.display = "none";
  list.style.display = "none";
  list.innerHTML = "";

  const result = await heartRateHistory(state.currentName);
  loading.style.display = "none";

  const records = result.ok && result.data.available ? result.data.records : [];

  if (records.length === 0) {
    empty.style.display = "flex";
    return;
  }

  list.style.display = "block";
  records.forEach((r) => {
    const item = document.createElement("div");
    item.className = "history-item";
    const label = heartStatusFor(r.bpm).label;
    item.innerHTML = `<div class="bpm">${Math.round(r.bpm)} bpm · ${label}</div><div class="time">${r.measured_at}</div>`;
    list.appendChild(item);
  });
}
