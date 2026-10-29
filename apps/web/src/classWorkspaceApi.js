
const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function getToken() {
  return (
    sessionStorage.getItem("access_token") ||
    localStorage.getItem("access_token") ||
    localStorage.getItem("token")
  );
}

async function request(endpoint, options = {}) {
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;

    try {
      const error = await response.json();
      message =
        typeof error.detail === "string"
          ? error.detail
          : JSON.stringify(error.detail || error);
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.items)) return data.items;
  if (Array.isArray(data.classes)) return data.classes;
  if (Array.isArray(data.students)) return data.students;
  return [];
}

export const classWorkspaceApi = {
  async listClasses() {
    const data = await request("/classes");
    return normalizeList(data);
  },

  async createClass(classData) {
    return request("/classes", {
      method: "POST",
      body: JSON.stringify(classData),
    });
  },

  async listStudents(classId) {
    const data = await request(`/classes/${classId}/students`);
    return normalizeList(data);
  },

  async addStudent(classId, studentData) {
    return request(`/classes/${classId}/students`, {
      method: "POST",
      body: JSON.stringify(studentData),
    });
  },
};
