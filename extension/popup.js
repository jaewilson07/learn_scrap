async function getStored(keys) {
  return await chrome.storage.local.get(keys);
}

async function setStored(obj) {
  await chrome.storage.local.set(obj);
}

function setStatus(text) {
  document.getElementById("status").textContent = text;
}

async function getBaseUrl() {
  const { baseUrl } = await getStored(["baseUrl"]);
  return baseUrl || "http://localhost:8001";
}

async function getToken() {
  const { accessToken } = await getStored(["accessToken"]);
  return accessToken || null;
}

async function getRefreshToken() {
  const { refreshToken } = await getStored(["refreshToken"]);
  return refreshToken || null;
}

async function setTokens({ accessToken, refreshToken }) {
  await setStored({ accessToken, refreshToken });
}

async function ensureToken() {
  const token = await getToken();
  if (!token) {
    throw new Error("Not signed in. Click 'Sign in with Google' first.");
  }
  return token;
}

async function refreshAccessToken() {
  const baseUrl = await getBaseUrl();
  const refreshToken = await getRefreshToken();
  if (!refreshToken) {
    throw new Error("Missing refresh token. Please sign in again.");
  }

  const resp = await fetch(`${baseUrl}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Refresh failed (${resp.status}): ${text}`);
  }

  const json = await resp.json();
  await setTokens({ accessToken: json.access_token, refreshToken: json.refresh_token });
  return json.access_token;
}

async function fetchWithAuth(url, options = {}) {
  let token = await ensureToken();
  const first = await fetch(url, {
    ...options,
    headers: { ...(options.headers || {}), Authorization: `Bearer ${token}` },
  });

  if (first.status !== 401) return first;

  // Attempt one refresh + retry.
  token = await refreshAccessToken();
  return await fetch(url, {
    ...options,
    headers: { ...(options.headers || {}), Authorization: `Bearer ${token}` },
  });
}

async function login() {
  const baseUrl = await getBaseUrl();
  const returnTo = chrome.runtime.getURL("auth.html");
  const url = `${baseUrl}/login?return_to=${encodeURIComponent(returnTo)}`;
  await chrome.tabs.create({ url });
  setStatus("Opened login tab. Complete Google sign-in there.");
}

async function extractCurrentPage() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error("No active tab");

  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      return {
        url: window.location.href,
        title: document.title,
        html: document.documentElement?.outerHTML || "",
      };
    },
  });

  return result;
}

async function savePage() {
  const baseUrl = await getBaseUrl();
  const page = await extractCurrentPage();

  const resp = await fetchWithAuth(`${baseUrl}/bookmarks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(page),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Save failed (${resp.status}): ${text}`);
  }

  const json = await resp.json();
  setStatus(`Saved.\nBookmark id: ${json.id}\nURL: ${page.url}`);
}

async function listBookmarks() {
  const baseUrl = await getBaseUrl();

  const resp = await fetchWithAuth(`${baseUrl}/bookmarks?limit=10`);

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`List failed (${resp.status}): ${text}`);
  }

  const json = await resp.json();
  const lines = (json.bookmarks || []).map((b) => `- ${b.title || "(no title)"}\n  ${b.url}`);
  setStatus(lines.length ? `Latest bookmarks:\n${lines.join("\n")}` : "No bookmarks yet.");
}

async function init() {
  const baseUrl = await getBaseUrl();
  document.getElementById("baseUrl").value = baseUrl;

  document.getElementById("saveBaseUrl").addEventListener("click", async () => {
    const val = document.getElementById("baseUrl").value.trim();
    await setStored({ baseUrl: val || "http://localhost:8001" });
    setStatus(`Saved backend URL: ${val || "http://localhost:8001"}`);
  });

  document.getElementById("login").addEventListener("click", async () => {
    try {
      await login();
    } catch (e) {
      setStatus(String(e?.message || e));
    }
  });

  document.getElementById("savePage").addEventListener("click", async () => {
    try {
      await savePage();
    } catch (e) {
      setStatus(String(e?.message || e));
    }
  });

  document.getElementById("listBookmarks").addEventListener("click", async () => {
    try {
      await listBookmarks();
    } catch (e) {
      setStatus(String(e?.message || e));
    }
  });

  const token = await getToken();
  if (token) {
    setStatus("Ready (token present).");
  } else {
    setStatus("Not signed in yet.");
  }
}

init();

