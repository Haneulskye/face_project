"use strict";

const API_BASE = "";
const TOKEN_KEY = "admin_token";

const loginView = document.getElementById("loginView");
const dashboardView = document.getElementById("dashboardView");
const tokenInput = document.getElementById("tokenInput");
const loginBtn = document.getElementById("loginBtn");
const loginError = document.getElementById("loginError");
const logoutBtn = document.getElementById("logoutBtn");
const refreshBtn = document.getElementById("refreshBtn");
const deleteAllBtn = document.getElementById("deleteAllBtn");
const userTableBody = document.getElementById("userTableBody");
const userCount = document.getElementById("userCount");
const emptyState = document.getElementById("emptyState");

function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

async function adminFetch(path, options = {}) {
  const response = await fetch(API_BASE + path, {
    ...options,
    headers: {
      ...(options.headers || {}),
      "X-Admin-Token": getToken() || "",
    },
  });
  return response;
}

function showDashboard() {
  loginView.style.display = "none";
  dashboardView.style.display = "block";
  logoutBtn.style.display = "inline-block";
  loadUsers();
}

function showLogin(message) {
  loginView.style.display = "flex";
  dashboardView.style.display = "none";
  logoutBtn.style.display = "none";
  if (message) {
    loginError.textContent = message;
    loginError.style.display = "block";
  }
}

async function attemptLogin() {
  const token = tokenInput.value.trim();
  if (!token) return;
  setToken(token);
  loginError.style.display = "none";

  const response = await adminFetch("/admin/users");
  if (response.status === 401) {
    clearToken();
    showLogin("비밀번호가 올바르지 않습니다.");
    return;
  }
  if (!response.ok) {
    showLogin("서버에 연결할 수 없습니다.");
    return;
  }
  showDashboard();
}

loginBtn.addEventListener("click", attemptLogin);
tokenInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") attemptLogin();
});

logoutBtn.addEventListener("click", () => {
  clearToken();
  showLogin();
});

refreshBtn.addEventListener("click", loadUsers);

function heartRateLabel(record) {
  if (!record) return "-";
  return `${Math.round(record.bpm)} bpm (${record.source || "-"})`;
}

async function loadUsers() {
  const response = await adminFetch("/admin/users");
  if (response.status === 401) {
    clearToken();
    showLogin("세션이 만료되었습니다. 다시 로그인해주세요.");
    return;
  }
  if (!response.ok) {
    alert("사용자 목록을 불러오지 못했습니다.");
    return;
  }

  const { users } = await response.json();
  userCount.textContent = `총 ${users.length}명`;
  emptyState.style.display = users.length === 0 ? "block" : "none";

  userTableBody.innerHTML = "";
  for (const user of users) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(user.name)}</td>
      <td>${escapeHtml(user.nickname || "-")}</td>
      <td>${user.age ?? "-"}</td>
      <td>${user.gender === "M" ? "남성" : user.gender === "F" ? "여성" : escapeHtml(user.gender || "-")}</td>
      <td>${user.height_cm ?? "-"}cm / ${user.weight_kg ?? "-"}kg</td>
      <td><span class="badge ${user.has_iris ? "yes" : "no"}">${user.has_iris ? "등록됨" : "미등록"}</span></td>
      <td>${heartRateLabel(user.latest_heart_rate)}</td>
      <td>${escapeHtml((user.registered_at || "").slice(0, 10))}</td>
      <td><button class="row-delete-btn" data-name="${escapeHtml(user.name)}">삭제</button></td>
    `;
    userTableBody.appendChild(tr);
  }

  userTableBody.querySelectorAll(".row-delete-btn").forEach((btn) => {
    btn.addEventListener("click", () => deleteUser(btn.dataset.name));
  });
}

async function deleteUser(name) {
  if (!confirm(`"${name}" 계정을 삭제할까요? 되돌릴 수 없습니다.`)) return;
  const response = await adminFetch(`/admin/users/${encodeURIComponent(name)}`, { method: "DELETE" });
  if (!response.ok) {
    alert("삭제하지 못했습니다.");
    return;
  }
  loadUsers();
}

deleteAllBtn.addEventListener("click", async () => {
  const response = await adminFetch("/admin/users");
  if (!response.ok) return;
  const { users } = await response.json();
  if (users.length === 0) return;

  if (!confirm(`전체 ${users.length}개 계정을 모두 삭제할까요? 되돌릴 수 없습니다.`)) return;

  for (const user of users) {
    await adminFetch(`/admin/users/${encodeURIComponent(user.name)}`, { method: "DELETE" });
  }
  loadUsers();
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

if (getToken()) {
  showDashboard();
} else {
  showLogin();
}
