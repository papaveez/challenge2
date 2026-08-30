let token = localStorage.getItem('token') || null;

export function getToken() {
  return token;
}

export function setToken(t) {
  token = t;
  if (t) localStorage.setItem('token', t);
  else localStorage.removeItem('token');
}

export async function api(path, { method = 'GET', body = null } = {}) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let payload = body;
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }

  const res = await fetch(path, { method, headers, body: payload });
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON response */
  }
  if (!res.ok) {
    const detail = data?.detail || `Request failed (${res.status})`;
    const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    err.status = res.status;
    throw err;
  }
  return data;
}
