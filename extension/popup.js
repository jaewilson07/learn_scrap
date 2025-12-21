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

async function ensureToken() {
  const token = await getToken();
  if (!token) {
    throw new Error("Not signed in. Click 'Sign in with Google' first.");
  }
  return token;
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
  const token = await ensureToken();
  const page = await extractCurrentPage();

  const resp = await fetch(`${baseUrl}/bookmarks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
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
  const token = await ensureToken();

  const resp = await fetch(`${baseUrl}/bookmarks?limit=10`, {
    headers: { Authorization: `Bearer ${token}` },
  });

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

