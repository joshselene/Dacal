
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

function getToken() {
  return (
    sessionStorage.getItem("access_token") ||
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    sessionStorage.getItem("token")
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
      if (typeof error.detail === "string") {
        message = error.detail;
      } else if (error.detail && typeof error.detail.message === "string") {
        const errs = (error.detail.validation_report?.errors || [])
          .map((e) => `${e.rule}: ${e.message}`)
          .join("; ");
        message = errs ? `${error.detail.message} (${errs})` : error.detail.message;
      } else {
        message = JSON.stringify(error.detail || error);
      }
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
  if (!data) return [];
  if (Array.isArray(data.items)) return data.items;
  if (Array.isArray(data.classes)) return data.classes;
  if (Array.isArray(data.modules)) return data.modules;
  if (Array.isArray(data.students)) return data.students;
  if (Array.isArray(data.schedules)) return data.schedules;
  if (Array.isArray(data.sessions)) return data.sessions;
  return [];
}

export const classWorkspaceApi = {
  // Classes
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

  async updateClass(classId, classData) {
    return request(`/classes/${classId}`, {
      method: "PATCH",
      body: JSON.stringify(classData),
    });
  },

  async deleteClass(classId) {
    return request(`/classes/${classId}`, {
      method: "DELETE",
    });
  },

  // Modules
  async listModules(classId) {
    const data = await request(`/classes/${classId}/modules`);
    return normalizeList(data);
  },

  async createModule(classId, moduleData) {
    return request(`/classes/${classId}/modules`, {
      method: "POST",
      body: JSON.stringify(moduleData),
    });
  },

  async updateModule(classId, moduleId, moduleData) {
    return request(`/classes/${classId}/modules/${moduleId}`, {
      method: "PATCH",
      body: JSON.stringify(moduleData),
    });
  },

  async deleteModule(classId, moduleId) {
    return request(`/classes/${classId}/modules/${moduleId}`, {
      method: "DELETE",
    });
  },

  // Students / Learners
  async listStudents(classId) {
    const data = await request(`/classes/${classId}/students`);
    return normalizeList(data);
  },

  async addStudent(classId, studentDataOrName) {
    const payload =
      typeof studentDataOrName === "string"
        ? { name: studentDataOrName }
        : studentDataOrName;
    return request(`/classes/${classId}/students`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateStudent(classId, studentId, studentDataOrName) {
    const payload =
      typeof studentDataOrName === "string"
        ? { name: studentDataOrName }
        : studentDataOrName;
    return request(`/classes/${classId}/students/${studentId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async deleteStudent(classId, studentId) {
    return request(`/classes/${classId}/students/${studentId}`, {
      method: "DELETE",
    });
  },

  // Schedules
  async listSchedules(classId) {
    const data = await request(`/classes/${classId}/schedules`);
    return normalizeList(data);
  },

  async addSchedule(classId, scheduleData) {
    return request(`/classes/${classId}/schedules`, {
      method: "POST",
      body: JSON.stringify(scheduleData),
    });
  },

  async updateSchedule(classId, scheduleId, scheduleData) {
    return request(`/classes/${classId}/schedules/${scheduleId}`, {
      method: "PATCH",
      body: JSON.stringify(scheduleData),
    });
  },

  async deleteSchedule(classId, scheduleId) {
    return request(`/classes/${classId}/schedules/${scheduleId}`, {
      method: "DELETE",
    });
  },

  // Experiences / Scenarios (Plan-Validate-Build workflow)
  async listExperiences() {
    const data = await request("/experiences");
    return normalizeList(data);
  },

  async createExperience(payload) {
    return request("/experiences", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateExperience(experienceId, payload) {
    return request(`/experiences/${experienceId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async updateAnswers(experienceId, answers) {
    return request(`/experiences/${experienceId}/answers`, {
      method: "PATCH",
      body: JSON.stringify({ answers }),
    });
  },

  async generateConcepts(experienceId) {
    return request(`/experiences/${experienceId}/concepts`, {
      method: "POST",
    });
  },

  async updateConcept(experienceId, conceptPreview) {
    return request(`/experiences/${experienceId}/concept`, {
      method: "PUT",
      body: JSON.stringify({ concept_preview: conceptPreview }),
    });
  },

  async approveConcept(experienceId) {
    return request(`/experiences/${experienceId}/approve`, {
      method: "POST",
    });
  },

  async generateExperience(experienceId) {
    return request(`/experiences/${experienceId}/generate`, {
      method: "POST",
    });
  },

  async runSafetyCheck() {
    return request("/safety-check", {
      method: "POST",
    });
  },

  async plainLanguageEdit(experienceId, instruction) {
    return request(`/experiences/${experienceId}/edit`, {
      method: "POST",
      body: JSON.stringify({ instruction }),
    });
  },

  async updateConfiguration(experienceId, configuration, spec = null) {
    return request(`/experiences/${experienceId}/configuration`, {
      method: "PATCH",
      body: JSON.stringify({ configuration, ...(spec ? { spec } : {}) }),
    });
  },

  async approveVersionForLaunch(experienceId) {
    return request(`/experiences/${experienceId}/approve-version`, {
      method: "POST",
    });
  },

  async listVersions(experienceId) {
    const data = await request(`/experiences/${experienceId}/versions`);
    return normalizeList(data);
  },

  async createVersion(experienceId, configurationSnapshot, spec = null) {
    return request(`/experiences/${experienceId}/versions`, {
      method: "POST",
      body: JSON.stringify({
        configuration_snapshot: configurationSnapshot,
        ...(spec ? { spec } : {}),
      }),
    });
  },

  async restoreVersion(experienceId, versionId) {
    return request(`/experiences/${experienceId}/versions/${versionId}/restore`, {
      method: "POST",
    });
  },

  async duplicateExperience(experienceId) {
    return request(`/experiences/${experienceId}/duplicate`, {
      method: "POST",
    });
  },

  // Runtime & Tutor Console
  async launchRun(payload) {
    return request("/runs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async listRuns() {
    const data = await request("/runs");
    return normalizeList(data);
  },

  async getRun(runId) {
    return request(`/runs/${runId}`);
  },

  async sendRunCommand(runId, command, payload = {}) {
    return request(`/runs/${runId}/command`, {
      method: "POST",
      body: JSON.stringify({ command, payload }),
    });
  },

  // Non-Diagnostic Session Notebook
  async getLearnerNotebook(learnerId) {
    return request(`/learners/${learnerId}/notebook`);
  },

  async listNotebookSessions(learnerId = null) {
    const qs = learnerId ? `?learner_id=${learnerId}` : "";
    return request(`/notebook${qs}`);
  },

  // Notifications, Audit & School Admin
  async listNotifications() {
    return request("/notifications");
  },

  async markNotificationRead(notificationId) {
    return request(`/notifications/${notificationId}/read`, {
      method: "POST",
    });
  },

  async markAllNotificationsRead() {
    return request("/notifications/read-all", {
      method: "POST",
    });
  },

  async listAuditEvents() {
    return request("/audit-events");
  },

  async exportSchoolData() {
    return request("/school/export");
  },

  async deleteSchoolData() {
    return request("/school/data", {
      method: "DELETE",
    });
  },

  async validateSpec(spec) {
    return request("/validate", {
      method: "POST",
      body: JSON.stringify({ spec }),
    });
  },
};
