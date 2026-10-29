
const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function getAuthToken() {
  // Check common token keys used by the existing login.
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    sessionStorage.getItem("access_token") ||
    sessionStorage.getItem("token")
  );
}

async function request(path, options = {}) {
  const token = getAuthToken();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(
      errorBody.detail || `Request failed (${response.status})`
    );
  }

  if (response.status === 204) return null;
  return response.json();
}

export const classWorkspaceApi = {
  listClasses: () => request("/classes"),

  createClass: (data) =>
    request("/classes", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateClass: (id, data) =>
    request(`/classes/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteClass: (id) =>
    request(`/classes/${id}`, { method: "DELETE" }),

  listStudents: (classId) =>
    request(`/classes/${classId}/students`),

  addStudent: (classId, name) =>
    request(`/classes/${classId}/students`, {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  updateStudent: (classId, studentId, name) =>
    request(`/classes/${classId}/students/${studentId}`, {
      method: "PATCH",
      body: JSON.stringify({ name }),
    }),

  deleteStudent: (classId, studentId) =>
    request(`/classes/${classId}/students/${studentId}`, {
      method: "DELETE",
    }),

  listSchedules: (classId) =>
    request(`/classes/${classId}/schedules`),

  addSchedule: (classId, data) =>
    request(`/classes/${classId}/schedules`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateSchedule: (classId, scheduleId, data) =>
    request(`/classes/${classId}/schedules/${scheduleId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteSchedule: (classId, scheduleId) =>
    request(`/classes/${classId}/schedules/${scheduleId}`, {
      method: "DELETE",
    }),
};
