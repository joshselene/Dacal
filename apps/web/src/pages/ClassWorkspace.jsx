
import { useEffect, useState } from "react";
import { classWorkspaceApi } from "../services/classWorkspaceApi";
import "./ClassWorkspace.css";

export default function ClassWorkspace() {
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [students, setStudents] = useState([]);
  const [schedules, setSchedules] = useState([]);

  const [className, setClassName] = useState("");
  const [description, setDescription] = useState("");
  const [studentName, setStudentName] = useState("");

  const [scheduleTitle, setScheduleTitle] = useState("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [dayOfWeek, setDayOfWeek] = useState("");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("10:00");
  const [scheduleNotes, setScheduleNotes] = useState("");

  const [editingClassId, setEditingClassId] = useState(null);
  const [editingStudentId, setEditingStudentId] = useState(null);
  const [editingScheduleId, setEditingScheduleId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadClasses();
  }, []);

  async function loadClasses() {
    setLoading(true);
    setError("");

    try {
      const data = await classWorkspaceApi.listClasses();
      setClasses(data);
    } catch (err) {
      setError(err.message || "Could not load classes.");
    } finally {
      setLoading(false);
    }
  }

  async function openClass(classroom) {
    setSelectedClass(classroom);
    setError("");

    try {
      const [studentData, scheduleData] = await Promise.all([
        classWorkspaceApi.listStudents(classroom.id),
        classWorkspaceApi.listSchedules(classroom.id),
      ]);

      setStudents(studentData);
      setSchedules(scheduleData);
    } catch (err) {
      setStudents([]);
      setSchedules([]);
      setError(err.message || "Could not load class details.");
    }
  }

  async function saveClass(event) {
    event.preventDefault();
    if (!className.trim()) return;

    setSaving(true);
    setError("");

    try {
      if (editingClassId) {
        await classWorkspaceApi.updateClass(editingClassId, {
          name: className.trim(),
          description: description.trim() || null,
        });
      } else {
        await classWorkspaceApi.createClass({
          name: className.trim(),
          description: description.trim() || null,
        });
      }

      setClassName("");
      setDescription("");
      setEditingClassId(null);
      await loadClasses();
    } catch (err) {
      setError(err.message || "Could not save the class.");
    } finally {
      setSaving(false);
    }
  }

  function startEditClass(classroom) {
    setEditingClassId(classroom.id);
    setClassName(classroom.name);
    setDescription(classroom.description || "");
  }

  async function removeClass(classroom) {
    if (!window.confirm(`Delete "${classroom.name}"?`)) return;

    setError("");

    try {
      await classWorkspaceApi.deleteClass(classroom.id);

      if (selectedClass?.id === classroom.id) {
        setSelectedClass(null);
        setStudents([]);
        setSchedules([]);
      }

      if (editingClassId === classroom.id) {
        setEditingClassId(null);
        setClassName("");
        setDescription("");
      }

      await loadClasses();
    } catch (err) {
      setError(err.message || "Could not delete the class.");
    }
  }

  async function saveStudent(event) {
    event.preventDefault();
    if (!selectedClass || !studentName.trim()) return;

    setSaving(true);
    setError("");

    try {
      if (editingStudentId) {
        await classWorkspaceApi.updateStudent(
          selectedClass.id,
          editingStudentId,
          studentName.trim()
        );
      } else {
        await classWorkspaceApi.addStudent(
          selectedClass.id,
          studentName.trim()
        );
      }

      setStudentName("");
      setEditingStudentId(null);
      await openClass(selectedClass);
    } catch (err) {
      setError(err.message || "Could not save the student.");
    } finally {
      setSaving(false);
    }
  }

  async function removeStudent(student) {
    if (!selectedClass) return;
    if (!window.confirm(`Remove ${student.name}?`)) return;

    try {
      await classWorkspaceApi.deleteStudent(
        selectedClass.id,
        student.id
      );

      if (editingStudentId === student.id) {
        setEditingStudentId(null);
        setStudentName("");
      }

      await openClass(selectedClass);
    } catch (err) {
      setError(err.message || "Could not remove the student.");
    }
  }

  function resetScheduleForm() {
    setScheduleTitle("");
    setScheduledDate("");
    setDayOfWeek("");
    setStartTime("09:00");
    setEndTime("10:00");
    setScheduleNotes("");
    setEditingScheduleId(null);
  }

  function startEditSchedule(schedule) {
    setEditingScheduleId(schedule.id);
    setScheduleTitle(schedule.title);
    setScheduledDate(schedule.scheduled_date || "");
    setDayOfWeek(schedule.day_of_week || "");
    setStartTime(schedule.start_time.slice(0, 5));
    setEndTime(schedule.end_time.slice(0, 5));
    setScheduleNotes(schedule.notes || "");
  }

  async function saveSchedule(event) {
    event.preventDefault();
    if (!selectedClass) return;

    if (!scheduledDate && !dayOfWeek) {
      setError("Choose a date or a day of the week.");
      return;
    }

    if (endTime <= startTime) {
      setError("End time must be later than start time.");
      return;
    }

    const payload = {
      title: scheduleTitle.trim(),
      scheduled_date: scheduledDate || null,
      day_of_week: dayOfWeek || null,
      start_time: startTime,
      end_time: endTime,
      notes: scheduleNotes.trim() || null,
    };

    setSaving(true);
    setError("");

    try {
      if (editingScheduleId) {
        await classWorkspaceApi.updateSchedule(
          selectedClass.id,
          editingScheduleId,
          payload
        );
      } else {
        await classWorkspaceApi.addSchedule(
          selectedClass.id,
          payload
        );
      }

      resetScheduleForm();
      await openClass(selectedClass);
    } catch (err) {
      setError(err.message || "Could not save the schedule.");
    } finally {
      setSaving(false);
    }
  }

  async function removeSchedule(schedule) {
    if (!selectedClass) return;
    if (!window.confirm(`Delete "${schedule.title}"?`)) return;

    try {
      await classWorkspaceApi.deleteSchedule(
        selectedClass.id,
        schedule.id
      );

      if (editingScheduleId === schedule.id) {
        resetScheduleForm();
      }

      await openClass(selectedClass);
    } catch (err) {
      setError(err.message || "Could not delete the schedule.");
    }
  }

  return (
    <main className="class-workspace">
      <header className="workspace-header">
        <div>
          <p className="workspace-eyebrow">CHERNYX AI STUDIO</p>
          <h1>Class Workspace</h1>
          <p className="workspace-subtitle">
            Organise your classes, students and teaching schedules.
          </p>
        </div>
        <span className="workspace-count">
          {classes.length} {classes.length === 1 ? "class" : "classes"}
        </span>
      </header>

      {error && (
        <div className="workspace-error" role="alert">
          {error}
          <button onClick={() => setError("")} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}

      <section className="workspace-grid">
        <aside className="workspace-panel">
          <h2>{editingClassId ? "Edit class" : "Create a class"}</h2>

          <form onSubmit={saveClass} className="workspace-form">
            <label>
              Class name
              <input
                value={className}
                onChange={(e) => setClassName(e.target.value)}
                placeholder="e.g. Mathematics — Grade 8"
                maxLength={255}
                required
              />
            </label>

            <label>
              Description
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What will this class cover?"
                rows={3}
              />
            </label>

            <button className="primary-button" disabled={saving}>
              {saving
                ? "Saving..."
                : editingClassId
                  ? "Save changes"
                  : "Create class"}
            </button>

            {editingClassId && (
              <button
                type="button"
                className="secondary-button"
                onClick={() => {
                  setEditingClassId(null);
                  setClassName("");
                  setDescription("");
                }}
              >
                Cancel editing
              </button>
            )}
          </form>

          <div className="class-list-heading">
            <h2>Your classes</h2>
            <button className="text-button" onClick={loadClasses}>
              Refresh
            </button>
          </div>

          {loading ? (
            <p className="muted-text">Loading classes...</p>
          ) : classes.length === 0 ? (
            <p className="empty-state">
              No classes yet. Create your first class above.
            </p>
          ) : (
            <div className="class-list">
              {classes.map((classroom) => (
                <article
                  key={classroom.id}
                  className={`class-card ${
                    selectedClass?.id === classroom.id ? "selected" : ""
                  }`}
                >
                  <button
                    className="class-card-main"
                    onClick={() => openClass(classroom)}
                  >
                    <strong>{classroom.name}</strong>
                    <span>{classroom.description || "No description"}</span>
                  </button>

                  <div className="card-actions">
                    <button
                      className="text-button"
                      onClick={() => startEditClass(classroom)}
                    >
                      Edit
                    </button>
                    <button
                      className="text-button danger-text"
                      onClick={() => removeClass(classroom)}
                    >
                      Delete
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </aside>

        <section className="workspace-panel details-panel">
          {!selectedClass ? (
            <div className="details-empty">
              <div className="empty-icon">▤</div>
              <h2>Your teaching space</h2>
              <p>
                Select a class to manage its students and schedule.
              </p>
            </div>
          ) : (
            <>
              <div className="selected-class-header">
                <div>
                  <p className="workspace-eyebrow">SELECTED CLASS</p>
                  <h2>{selectedClass.name}</h2>
                  <p>{selectedClass.description || "No description added."}</p>
                </div>
                <span className="student-count">
                  {students.length} students
                </span>
              </div>

              <section className="detail-section">
                <h3>Students</h3>

                <form onSubmit={saveStudent} className="inline-form">
                  <input
                    value={studentName}
                    onChange={(e) => setStudentName(e.target.value)}
                    placeholder="Enter student name"
                    maxLength={255}
                    required
                  />
                  <button className="primary-button" disabled={saving}>
                    {editingStudentId ? "Save name" : "Add student"}
                  </button>
                  {editingStudentId && (
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => {
                        setEditingStudentId(null);
                        setStudentName("");
                      }}
                    >
                      Cancel
                    </button>
                  )}
                </form>

                {students.length === 0 ? (
                  <p className="empty-state">No students added yet.</p>
                ) : (
                  <ul className="student-list">
                    {students.map((student) => (
                      <li key={student.id}>
                        <span className="student-avatar">
                          {student.name.charAt(0).toUpperCase()}
                        </span>
                        <span className="student-name">{student.name}</span>
                        <button
                          className="text-button"
                          onClick={() => {
                            setEditingStudentId(student.id);
                            setStudentName(student.name);
                          }}
                        >
                          Edit
                        </button>
                        <button
                          className="text-button danger-text"
                          onClick={() => removeStudent(student)}
                        >
                          Remove
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section className="detail-section">
                <h3>Class schedule</h3>

                <form onSubmit={saveSchedule} className="workspace-form">
                  <label>
                    Schedule title
                    <input
                      value={scheduleTitle}
                      onChange={(e) => setScheduleTitle(e.target.value)}
                      placeholder="e.g. Algebra lesson"
                      maxLength={255}
                      required
                    />
                  </label>

                  <div className="form-two-columns">
                    <label>
                      Specific date (optional)
                      <input
                        type="date"
                        value={scheduledDate}
                        onChange={(e) => setScheduledDate(e.target.value)}
                      />
                    </label>

                    <label>
                      Repeat on day (optional)
                      <select
                        value={dayOfWeek}
                        onChange={(e) => setDayOfWeek(e.target.value)}
                      >
                        <option value="">Choose day</option>
                        {[
                          "Monday",
                          "Tuesday",
                          "Wednesday",
                          "Thursday",
                          "Friday",
                          "Saturday",
                          "Sunday",
                        ].map((day) => (
                          <option key={day} value={day}>
                            {day}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <div className="form-two-columns">
                    <label>
                      Start time
                      <input
                        type="time"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        required
                      />
                    </label>

                    <label>
                      End time
                      <input
                        type="time"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                        required
                      />
                    </label>
                  </div>

                  <label>
                    Notes (optional)
                    <textarea
                      value={scheduleNotes}
                      onChange={(e) => setScheduleNotes(e.target.value)}
                      placeholder="Materials to prepare, lesson reminders..."
                      rows={2}
                    />
                  </label>

                  <div className="form-actions">
                    <button className="primary-button" disabled={saving}>
                      {saving
                        ? "Saving..."
                        : editingScheduleId
                          ? "Save schedule changes"
                          : "Add schedule"}
                    </button>

                    {editingScheduleId && (
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={resetScheduleForm}
                      >
                        Cancel editing
                      </button>
                    )}
                  </div>
                </form>

                {schedules.length === 0 ? (
                  <p className="empty-state">
                    No schedule entries yet.
                  </p>
                ) : (
                  <div className="schedule-list">
                    {schedules.map((schedule) => (
                      <article className="schedule-card" key={schedule.id}>
                        <div className="schedule-time">
                          <strong>{schedule.start_time.slice(0, 5)}</strong>
                          <span>to {schedule.end_time.slice(0, 5)}</span>
                        </div>

                        <div className="schedule-info">
                          <strong>{schedule.title}</strong>
                          <span>
                            {schedule.scheduled_date || schedule.day_of_week}
                          </span>
                          {schedule.notes && <p>{schedule.notes}</p>}
                        </div>

                        <div className="card-actions">
                          <button
                            className="text-button"
                            onClick={() => startEditSchedule(schedule)}
                          >
                            Edit
                          </button>
                          <button
                            className="text-button danger-text"
                            onClick={() => removeSchedule(schedule)}
                          >
                            Delete
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </section>
      </section>
    </main>
  );
}
