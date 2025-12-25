const msg = document.getElementById("msg");
const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
const accessToken = hash.get("access_token");
const refreshToken = hash.get("refresh_token");
const tokenType = hash.get("token_type");

if (!accessToken) {
  msg.textContent = "Missing access token. Please retry login.";
} else {
  chrome.storage.local.set({ accessToken, refreshToken }, () => {
    msg.innerHTML =
      "Token stored. token_type=" +
      (tokenType || "bearer") +
      "<br/><br/><code>" +
      accessToken +
      "</code>";
    // Best-effort close (may be blocked by browser policy)
    setTimeout(() => window.close(), 1200);
  });
}

