// All backend calls go through the Vite dev proxy at /api -> http://localhost:8000
const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const getAuthStatus = () => request("/auth/status");
export const getDashboard = (days = 30) => request(`/dashboard?days=${days}`);
export const runSync = (lookbackDays) =>
  request(`/sync${lookbackDays ? `?lookback_days=${lookbackDays}` : ""}`, {
    method: "POST",
  });

export const getRecoveryDetail = (days = 60) => request(`/detail/recovery?days=${days}`);
export const getSleepDetail = (days = 60) => request(`/detail/sleep?days=${days}`);
export const getCardioDetail = () => request(`/detail/cardio`);
export const getStrainDetail = (days = 60) => request(`/detail/strain?days=${days}`);

export const getProfile = () => request("/profile");
export const updateProfile = (body) =>
  request("/profile", { method: "PUT", body: JSON.stringify(body) });
