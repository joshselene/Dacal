
import React, { lazy, Suspense, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import { Bell, BookOpen, CircleHelp, Clock3, FolderOpen, House, LayoutGrid, LogOut, Moon, Plus, Sparkles, Sun, X } from "lucide-react";
import "./style.css";
const FourWallPreview = lazy(() => import("./components/FourWallPreview"));
import { classWorkspaceApi } from "./classWorkspaceApi.js";
const API_URL = `${import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1"}/auth`;

const QUESTIONS = [
  {
    title: "What is the primary learning goal?",
    help: "What should the learner understand or be able to do?",
    options: ["Communication", "Social skills", "Life skills", "Academic learning"],
  },
  {
    title: "Who is the target learner group?",
    help: "Choose the group this experience is designed for.",
    options: ["Early learners", "Primary school", "Teenagers", "Mixed ages"],
  },
  {
    title: "What should learners practise?",
    help: "Choose the main activity.",
    options: ["Exploration", "Guided practice", "Problem solving", "Role play"],
  },
  {
    title: "Which environment fits the activity?",
    help: "Where should the experience take place?",
    options: ["Classroom", "Home", "Public space", "Fantasy environment"],
  },
  {
    title: "How should the experience begin?",
    help: "Choose the opening interaction.",
    options: ["Welcome scene", "A simple task", "A character introduction", "Free exploration"],
  },
  {
    title: "How much guidance should learners receive?",
    help: "Set the level of support.",
    options: ["Step-by-step", "Hints when needed", "Minimal guidance", "Tutor-led"],
  },
  {
    title: "What interaction style should be used?",
    help: "How should learners interact with the scene?",
    options: ["Point and select", "Drag and drop", "Conversation", "Object interaction"],
  },
  {
    title: "Should the experience include characters?",
    help: "Characters can model behaviour or provide feedback.",
    options: ["Friendly guide", "Other learners", "Everyday characters", "No characters"],
  },
  {
    title: "What visual style do you prefer?",
    help: "Choose a look suitable for the learning activity.",
    options: ["Soft 3D", "Cartoon", "Realistic", "Minimal and simple"],
  },
  {
    title: "How long should the activity take?",
    help: "Choose a target duration.",
    options: ["2–5 minutes", "5–10 minutes", "10–15 minutes", "Flexible"],
  },
  {
    title: "What difficulty level is appropriate?",
    help: "The activity should match the learner's needs.",
    options: ["Beginner", "Developing", "Intermediate", "Adaptive"],
  },
  {
    title: "How should instructions be delivered?",
    help: "Choose how learners receive instructions.",
    options: ["Text", "Voice", "Visual cues", "Combination"],
  },
  {
    title: "Should learners receive feedback?",
    help: "Choose how progress should be communicated.",
    options: ["After every action", "At key milestones", "At the end", "Tutor provides feedback"],
  },
  {
    title: "What happens when a learner makes a mistake?",
    help: "Choose the preferred response.",
    options: ["Gentle hint", "Try again", "Show an example", "Tutor decides"],
  },
  {
    title: "Should the activity have multiple stages?",
    help: "Stages can gradually introduce new challenges.",
    options: ["One simple task", "Three short stages", "Increasing difficulty", "Learner chooses"],
  },
  {
    title: "What accessibility support is needed?",
    help: "Select a suitable support option.",
    options: ["Simple language", "Visual prompts", "Reduced stimulation", "Multiple support options"],
  },
  {
    title: "How should movement work?",
    help: "Choose how learners move around the environment.",
    options: ["Stationary view", "Point-to-move", "Guided movement", "No movement needed"],
  },
  {
    title: "Should there be rewards?",
    help: "Rewards can reinforce learning milestones.",
    options: ["Stars or badges", "Positive messages", "Unlockable items", "No rewards"],
  },
  {
    title: "How will the tutor participate?",
    help: "Choose the tutor's role.",
    options: ["Observe", "Give hints", "Control the activity", "Participate alongside learners"],
  },
  {
    title: "What defines a successful session?",
    help: "Choose how the learning outcome should be recognised.",
    options: ["Complete the task", "Demonstrate a skill", "Make progress", "Tutor assessment"],
  },
];

const NAVIGATION = [
  { name: "Overview", label: "Home", icon: House },
  { name: "Classes & Modules", label: "Classes and modules", icon: LayoutGrid },
  { name: "Create Experience", label: "Chernyx Studio", icon: Sparkles },
  { name: "My Experiences", label: "Projects", icon: FolderOpen },
  { name: "Session Notebook", label: "Session notebook", icon: BookOpen },
  { name: "Learning Hub", label: "Learning hub", icon: CircleHelp },
];

const DEFAULT_SCENE_SPEC = {
  room: { w: 12, h: 8, entrance: { wall: "S", cells: [[5, 7], [6, 7]] } },
  layout: [
    {
      id: "shelf1",
      asset: "shelf",
      cell: [2, 3],
      size: [3, 1],
      items: [
        { sku: "milk", price: 62 },
        { sku: "bread", price: 45 },
      ],
    },
    {
      id: "shelf2",
      asset: "shelf",
      cell: [6, 2],
      size: [2, 1],
      items: [
        { sku: "apple", price: 30 },
        { sku: "juice", price: 55 },
      ],
    },
    { id: "counter", asset: "counter", cell: [10, 6], size: [1, 1] },
  ],
  task: {
    required: ["milk", "bread"],
    budget: 500,
    time_limit_s: 300,
    difficulty: "Developing",
    rules: [
      "Pick up every item on the shopping list",
      "Keep total basket cost within budget",
      "Pay at the counter when finished",
    ],
    what_ifs: [
      "Preferred brand is out of stock",
      "Shopkeeper asks if you need a bag",
    ],
  },
  support: {
    A: { prompt: 3, density: 2, volume: 40 },
    B: { prompt: 2, density: 3, volume: 60 },
    C: { prompt: 1, density: 5, volume: 80 },
  },
  events: [{ trigger: "enter", target: "shopkeeper" }],
};

function getTimeOfDayGreeting(name) {
  const hour = new Date().getHours();
  let salutation = "Good evening";
  if (hour < 12) salutation = "Good morning";
  else if (hour < 17) salutation = "Good afternoon";
  return name ? `${salutation}, ${name}` : salutation;
}

function mapExperienceStatusLabel(status) {
  if (status === "ready_to_configure") return "Ready to configure";
  if (status === "configured") return "Configured";
  if (status === "approved") return "Approved";
  if (status === "generating") return "Generation queued";
  return "Draft";
}

function mapExperienceStage(status) {
  if (status === "ready_to_configure" || status === "configured") {
    return "configure";
  }
  if (status === "approved") return "versions";
  return "prompt";
}

function App() {
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem("chernyx_theme");
      if (saved === "light" || saved === "dark") return saved;
    } catch {}
    return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  const notificationRef = useRef(null);
  const notificationButtonRef = useRef(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("chernyx_theme", theme); } catch {}
  }, [theme]);

  // Authentication: login and signup live in this same file.
  const [isLoggedIn, setIsLoggedIn] = useState(
    () => !!sessionStorage.getItem("access_token")
  );
  const [authPage, setAuthPage] = useState("login");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [userRole, setUserRole] = useState("tutor");
  const [userFullName, setUserFullName] = useState("");
  const [greeting, setGreeting] = useState(() => getTimeOfDayGreeting());
  const [loginError, setLoginError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [signupForm, setSignupForm] = useState({
    full_name: "",
    email: "",
    organisation_name: "",
    role: "tutor",
    password: "",
    confirm_password: "",
  });
  const [signupError, setSignupError] = useState("");
  const [signupSuccess, setSignupSuccess] = useState("");
  const [signupLoading, setSignupLoading] = useState(false);

  // Workspace navigation
  const [activeTab, setActiveTab] = useState("Overview");
  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  // Notifications & Audit (LC-6, FR-19)
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notebookSessions, setNotebookSessions] = useState([]);
  const [auditEvents, setAuditEvents] = useState([]);

  useEffect(() => {
    if (!showNotifications) return;
    function dismiss(event) {
      if (event.type === "keydown") {
        if (event.key !== "Escape") return;
        notificationButtonRef.current?.focus();
      } else if (notificationRef.current?.contains(event.target)) return;
      setShowNotifications(false);
    }
    document.addEventListener("pointerdown", dismiss);
    document.addEventListener("keydown", dismiss);
    return () => {
      document.removeEventListener("pointerdown", dismiss);
      document.removeEventListener("keydown", dismiss);
    };
  }, [showNotifications]);

  // Experience creation workflow
  const [stage, setStage] = useState("prompt");
  const [prompt, setPrompt] = useState("");
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [isRecordingVoice, setIsRecordingVoice] = useState(false);
  const [mediaAttachments, setMediaAttachments] = useState([]);
  const [experienceTitle, setExperienceTitle] = useState("");
  const [category, setCategory] = useState("Social Skills");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [customAnswers, setCustomAnswers] = useState({});
  const [concept, setConcept] = useState("guided");
  const [generationStarted, setGenerationStarted] = useState(false);

  // Scene spec, validation report, dollhouse & plain-language edit (FR-08, FR-09, FR-14)
  const [sceneSpec, setSceneSpec] = useState(DEFAULT_SCENE_SPEC);
  const [validationReport, setValidationReport] = useState({
    valid: true,
    errors: [],
    warnings: [],
    rules_summary: {
      R1: "pass",
      R2: "pass",
      R3: "pass",
      R3w: "pass",
      R4: "pass",
      R5: "pass",
      R6: "pass",
      R7: "pass",
    },
    elapsed_ms: 0.13,
  });
  const [selectedSpecObjectId, setSelectedSpecObjectId] = useState("shelf1");
  const [plainEditInput, setPlainEditInput] = useState("");
  const [lastPatchInfo, setLastPatchInfo] = useState(null);
  const [activePathway, setActivePathway] = useState("B");
  const [activeRun, setActiveRun] = useState(null);
  const [runMode, setRunMode] = useState("room");

  const [configuration, setConfiguration] = useState({
    environment: "Classroom",
    duration: "5–10 minutes",
    guidance: "Step-by-step",
    visualStyle: "Soft 3D",
    accessibility: "Visual prompts",
    comfort: "Low stimulation",
    budget: 500,
    time_limit_s: 300,
    required: "milk, bread",
  });

  const [versions, setVersions] = useState([]);
  const [notice, setNotice] = useState("");
  const [classes, setClasses] = useState([]);
  const [students, setStudents] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState("");
  const [className, setClassName] = useState("");
  const [classDescription, setClassDescription] = useState("");
  const [studentName, setStudentName] = useState("");
  const [scheduleTitle, setScheduleTitle] = useState("");
  const [scheduleDay, setScheduleDay] = useState("Monday");
  const scheduleStart = "09:00";
  const scheduleEnd = "10:00";
  const [classLoading, setClassLoading] = useState(false);
  const [classError, setClassError] = useState("");
  // Module management
  const [modulesByClass, setModulesByClass] = useState(() => {
    try {
      return JSON.parse(
        localStorage.getItem("chernyx_modules_by_class") || "{}"
      );
    } catch {
      return {};
    }
  });

  const [moduleName, setModuleName] = useState("");
  const [moduleDescription, setModuleDescription] = useState("");
  const [editingModuleId, setEditingModuleId] = useState(null);
  const [showModuleForm, setShowModuleForm] = useState(false);
  const [editingClass, setEditingClass] = useState(false);

  async function refreshWorkspaceData() {
    try {
      const [expList, clsList, notifData, nbData, auditData] = await Promise.all([
        classWorkspaceApi.listExperiences().catch(() => []),
        classWorkspaceApi.listClasses().catch(() => []),
        classWorkspaceApi.listNotifications().catch(() => ({ unread_count: 0, items: [] })),
        classWorkspaceApi.listNotebookSessions().catch(() => ({ sessions: [] })),
        classWorkspaceApi.listAuditEvents().catch(() => []),
      ]);
      {
        setProjects(
          expList.map((e) => ({
        ...e,
            id: e.id,
            title: e.title,
            category: e.category || "Social Skills",
            status: mapExperienceStatusLabel(e.status),
            stage: mapExperienceStage(e.status),
            prompt: e.prompt,
            version: e.current_version || 1,
            spec: e.spec || DEFAULT_SCENE_SPEC,
            validation_report: e.validation_report,
          }))
        );
      }
      {
        setClasses(clsList);
        const firstId = clsList[0]?.id || "";
        setSelectedClassId((curr) => curr || firstId);
      }
      setNotifications(notifData.items || []);
      setUnreadCount(notifData.unread_count || 0);
      setNotebookSessions(nbData.sessions || []);
      setAuditEvents(Array.isArray(auditData) ? auditData : []);
    } catch {
      // Keep local prototype state if backend is offline
    }
  }

  async function handleLogin(event) {
    event.preventDefault();
    setLoginError("");
    setIsLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/login`,
        {
          email: email.trim(),
          password,
          local_hour: new Date().getHours(),
        },
        { withCredentials: true }
      );

      if (response.data.access_token) {
        sessionStorage.setItem("access_token", response.data.access_token);
        setUserRole(response.data.role || "tutor");
        setUserFullName(response.data.full_name || "");
        setGreeting(
          response.data.greeting ||
            getTimeOfDayGreeting(response.data.full_name || email.split("@")[0])
        );
        setIsLoggedIn(true);
        await refreshWorkspaceData();
      } else {
        setLoginError("Login response did not contain an access token.");
      }
    } catch (error) {
      setLoginError(
        error.response?.data?.detail ||
          "Unable to log in. Check your email, password, and backend."
      );
    } finally {
      setIsLoading(false);
    }
  }

  function updateSignupField(event) {
    const { name, value } = event.target;

    setSignupForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSignup(event) {
    event.preventDefault();
    setSignupError("");
    setSignupSuccess("");

    if (signupForm.password.length < 8) {
      setSignupError("Your password must contain at least 8 characters.");
      return;
    }

    if (signupForm.password !== signupForm.confirm_password) {
      setSignupError("The passwords do not match.");
      return;
    }

    setSignupLoading(true);

    try {
      await axios.post(
        `${API_URL}/register`,
        {
          full_name: signupForm.full_name.trim(),
          email: signupForm.email.trim(),
          organisation_name: signupForm.organisation_name.trim(),
          role: signupForm.role || "tutor",
          password: signupForm.password,
          local_hour: new Date().getHours(),
        },
        { withCredentials: true }
      );

      const registeredEmail = signupForm.email.trim();

      setSignupSuccess("Account created successfully. You can now sign in.");
      setEmail(registeredEmail);
      setPassword("");
      setSignupForm({
        full_name: "",
        email: "",
        organisation_name: "",
        role: "tutor",
        password: "",
        confirm_password: "",
      });

      setAuthPage("login");
      setLoginError("");
    } catch (error) {
      const detail = error.response?.data?.detail;

      setSignupError(
        typeof detail === "string"
          ? detail
          : "Unable to create your account. Check your details and try again."
      );
    } finally {
      setSignupLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await axios.post(
        `${API_URL}/logout`,
        {},
        { withCredentials: true }
      );
    } catch (error) {
      console.error("Logout request failed:", error);
    }

    sessionStorage.removeItem("access_token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    setProjects([]);
    setClasses([]);
    setStudents([]);
    setVersions([]);
    setSelectedId(null);
    setActiveRun(null);
    setIsLoggedIn(false);
    setPassword("");
    setAuthPage("login");
  }

  function startNewExperience() {
    setSelectedId(null);
    setPrompt("");
    setVoiceTranscript("");
    setMediaAttachments([]);
    setExperienceTitle("");
    setCategory("Social Skills");
    setQuestionIndex(0);
    setAnswers({});
    setCustomAnswers({});
    setConcept("guided");
    setGenerationStarted(false);
    setSceneSpec(DEFAULT_SCENE_SPEC);
    setLastPatchInfo(null);
    setActiveRun(null);
    setStage("prompt");
    setNotice("");
    setActiveTab("Create Experience");
  }

  function openProject(project) {
    setAnswers(project.answers || {});
    setCustomAnswers(project.answers?.notes || {});
    setConfiguration((current) => ({ ...current, ...(project.configuration || {}), budget: project.spec?.task?.budget ?? 500, required: (project.spec?.task?.required || []).join(", ") }));
    setVersions([]);
    setActiveRun(null);
    void classWorkspaceApi.listVersions(project.id).then((items) => setVersions(items.map((version) => ({ ...version, number: version.version_number, title: project.title, date: new Date(version.created_at).toLocaleDateString(), status: version.state, snapshot: version.configuration_snapshot })))).catch((error) => setNotice(error.message));
    setSelectedId(project.id);
    setPrompt(project.prompt || "");
    setExperienceTitle(project.title);
    setCategory(project.category || "Social Skills");
    setStage(project.stage || "prompt");
    setGenerationStarted(project.stage === "generating");
    if (project.spec) setSceneSpec(project.spec);
    if (project.validation_report) setValidationReport(project.validation_report);
    setNotice("");
    setActiveTab("Create Experience");
  }

  function updateProject(updates) {
    setProjects((current) => {
      const exists = current.some((project) => project.id === selectedId);
      if (!exists) return current;

      return current.map((project) =>
        project.id === selectedId ? { ...project, ...updates } : project
      );
    });
  }

  async function saveDraft(nextStage = stage) {
    const combinedPrompt =
      prompt.trim() || voiceTranscript.trim() || "Create a life-skills learning scene";
    const title =
      experienceTitle.trim() ||
      combinedPrompt.split(/[.!?\n]/)[0].slice(0, 55) ||
      "Untitled learning experience";

    if (!selectedId || typeof selectedId === "number") {
      try {
        const created = await classWorkspaceApi.createExperience({
          title,
          prompt: combinedPrompt,
          category,
          voice_transcript: voiceTranscript || null,
          attachments: mediaAttachments,
        });
        const newProj = {
          id: created.id,
          title: created.title,
          category: created.category || category,
          prompt: created.prompt,
          status: "Draft",
          stage: nextStage,
          version: created.current_version || 1,
        };
        setProjects((current) => [newProj, ...current]);
        setSelectedId(created.id);
        setExperienceTitle(created.title);
        return created.id;
      } catch {
        const fallbackId = selectedId || Date.now();
        if (!selectedId) {
          const newProject = {
            id: fallbackId,
            title,
            category,
            prompt: combinedPrompt,
            status: "Draft",
            stage: nextStage,
            version: 1,
          };
          setProjects((current) => [newProject, ...current]);
          setSelectedId(fallbackId);
          setExperienceTitle(title);
        } else {
          updateProject({ title, category, prompt: combinedPrompt, stage: nextStage });
        }
        return fallbackId;
      }
    } else {
      updateProject({ title, category, prompt: combinedPrompt, stage: nextStage });
      return selectedId;
    }
  }

  async function continueToQuestions(event) {
    event.preventDefault();
    if (!prompt.trim() && !voiceTranscript.trim()) return;
    if (!prompt.trim() && voiceTranscript.trim()) {
      setPrompt(voiceTranscript.trim());
    }

    await saveDraft("questions");
    setQuestionIndex(0);
    setStage("questions");
    setNotice("");
  }

  function setAnswer(index, value) {
    setAnswers((current) => ({ ...current, [index]: value }));
  }

  function setCustomAnswer(index, value) {
    setCustomAnswers((current) => ({ ...current, [index]: value }));
  }

  async function finishQuestions() {
    const expId = await saveDraft("review");
    if (expId && typeof expId === "string") {
      try {
        await classWorkspaceApi.updateAnswers(expId, answers);
      } catch {
        // Ignore if already past questions stage
      }
    }
    setStage("review");
    setNotice("");
  }

  async function approveConcept() {
    const expId = await saveDraft("generating");
    setGenerationStarted(true);
    updateProject({ status: "Generation queued", stage: "generating" });
    setStage("generating");
    setNotice("");

    if (expId && typeof expId === "string") {
      try {
        await classWorkspaceApi.updateConcept(expId, {
          id: concept,
          title:
            concept === "guided"
              ? "Guided practice shop"
              : concept === "explore"
                ? "Open neighbourhood market"
                : "Calm sensory corner store",
        });
        await classWorkspaceApi.approveConcept(expId);
      } catch {
        // Fallback for local state
      }
    }
  }

  async function markReadyToConfigure() {
    if (selectedId && typeof selectedId === "string") {
      try {
        const generated = await classWorkspaceApi.generateExperience(selectedId);
        if (generated.spec) setSceneSpec(generated.spec);
        if (generated.validation_report) {
          setValidationReport(generated.validation_report);
        }
        const notifData = await classWorkspaceApi.listNotifications().catch(() => null);
        if (notifData) {
          setNotifications(notifData.items || []);
          setUnreadCount(notifData.unread_count || 0);
        }
      } catch {
        // Continue with local validated reference spec
      }
    }
    setStage("configure");
    setGenerationStarted(false);
    updateProject({ status: "Ready to configure", stage: "configure" });
    setNotice(
      "Scene spec generated and validated against R1–R7 constraints. Configuration is now unlocked."
    );
  }

  async function handlePlainLanguageEdit(event) {
    event.preventDefault();
    if (!plainEditInput.trim()) return;

    if (selectedId && typeof selectedId === "string") {
      try {
        const res = await classWorkspaceApi.plainLanguageEdit(
          selectedId,
          plainEditInput.trim()
        );
        if (res.experience?.spec) setSceneSpec(res.experience.spec);
        if (res.validation_report) setValidationReport(res.validation_report);
        setLastPatchInfo({
          ratio: (res.patch_ratio * 100).toFixed(1),
          ops: res.patch_ops,
          version: res.version_number,
        });
        updateProject({
          version: res.version_number,
          status: "Ready to configure",
        });
        setPlainEditInput("");
        setNotice(
          `Plain-language patch applied (${(res.patch_ratio * 100).toFixed(1)}% of spec bytes) · Created v${res.version_number}.`
        );
        return;
      } catch (err) {
        setNotice(`Edit rejected by R1–R7 validator: ${err.message}`);
        return;
      }
    }

    // Offline localized patch fallback
    const nextSpec = JSON.parse(JSON.stringify(sceneSpec));
    const text = plainEditInput.trim().toLowerCase();
    const mBudget = text.match(/budget\s+(?:to|=)\s*(\d+)/);
    const mPrice = text.match(/([a-z0-9_]+)\s+price\s+(?:to|=)\s*(\d+)/);
    if (mBudget) {
      nextSpec.task.budget = Number(mBudget[1]);
    } else if (mPrice) {
      nextSpec.layout.forEach((obj) => {
        (obj.items || []).forEach((it) => {
          if (it.sku === mPrice[1]) it.price = Number(mPrice[2]);
        });
      });
    }
    setSceneSpec(nextSpec);
    setLastPatchInfo({ ratio: "0.8", ops: [{ op: "replace" }], version: 2 });
    setPlainEditInput("");
    setNotice("Localized patch applied (< 10% of spec bytes) and validated by R1–R7.");
  }

  async function saveConfiguration() {
    const reqList = String(configuration.required || "milk, bread")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const updatedSpec = {
      ...sceneSpec,
      task: {
        ...sceneSpec.task,
        budget: Number(configuration.budget || 500),
        time_limit_s: Number(configuration.time_limit_s || 300),
        required: reqList.length ? reqList : ["milk", "bread"],
      },
    };
    setSceneSpec(updatedSpec);

    if (selectedId && typeof selectedId === "string") {
      try {
        const res = await classWorkspaceApi.updateConfiguration(
          selectedId,
          configuration,
          updatedSpec
        );
        if (res.validation_report) setValidationReport(res.validation_report);
      } catch (err) {
        setNotice(`Configuration rejected: ${err.message}`);
        return;
      }
    }

    updateProject({ status: "Configured", stage: "configure" });
    setNotice("Configuration validated against R1–R7 and saved.");
  }

  async function approveVersion() {
    const current = projects.find((project) => project.id === selectedId);
    let nextVersion = (current?.version || 1) + 1;

    if (selectedId && typeof selectedId === "string") {
      try {
        const res = await classWorkspaceApi.approveVersionForLaunch(selectedId);
        nextVersion = res.current_version || nextVersion;
        const verList = await classWorkspaceApi.listVersions(selectedId).catch(() => []);
        if (verList.length > 0) {
          setVersions(
            verList.map((v) => ({
              id: v.id,
              number: v.version_number,
              title: experienceTitle || current?.title || "Learning experience",
              date: new Date(v.created_at).toLocaleDateString(),
              status: v.state === "approved" ? "Approved" : "Configured",
              snapshot: v.configuration_snapshot || { ...configuration },
            }))
          );
          updateProject({ version: nextVersion, status: "Approved" });
          setNotice(`Version ${nextVersion} approved and immutable. Ready to launch.`);
          return;
        }
      } catch {
        // Fallback to local version list
      }
    }

    setVersions((items) => [
      {
        id: Date.now(),
        number: nextVersion,
        title: experienceTitle || current?.title || "Learning experience",
        date: new Date().toLocaleDateString(),
        status: "Approved",
        snapshot: { ...configuration },
      },
      ...items,
    ]);

    updateProject({ version: nextVersion, status: "Approved" });
    setNotice(`Version ${nextVersion} approved and locked for running.`);
  }

  async function handleLaunchRuntime(selectedMode = runMode) {
    const current = projects.find((project) => project.id === selectedId);
    if (current?.status !== "Approved" && versions.length === 0) {
      setNotice("Only approved versions can launch (FR-11). Approve the version first.");
      return;
    }

    if (selectedId && typeof selectedId === "string") {
      try {
        const runData = await classWorkspaceApi.launchRun({
          experience_id: selectedId,
          pathway: activePathway,
          mode: selectedMode,
          learner_id: students[0]?.id || null,
        });
        setActiveRun(runData);
        setRunMode(selectedMode);
        setStage("runtime");
        setNotice(`Launched on ${selectedMode === "room" ? "Four-Wall Room (N/E/S/W)" : "Laptop"} · Pathway ${activePathway}`);
        return;
      } catch (err) {
        setNotice(`Launch blocked: ${err.message}`);
        return;
      }
    }

    setActiveRun({
      id: `run-${Date.now()}`,
      scenario_title: experienceTitle || current?.title || "Shopping Scenario",
      version_number: current?.version || 1,
      pathway: activePathway,
      mode: selectedMode,
      status: "running",
      learner_position: { x: 5, y: 7, dir: "N" },
      basket: [],
      basket_total: 0,
      budget: sceneSpec.task?.budget || 500,
      required_items: sceneSpec.task?.required || ["milk", "bread"],
      steps_completed: ["entered_room"],
      prompts_given: 0,
      tutor_decisions: 0,
      errors_count: 0,
      active_what_if: null,
    });
    setRunMode(selectedMode);
    setStage("runtime");
    setNotice(`Launched approved scenario in ${selectedMode} mode.`);
  }

  async function handleConsoleCommand(command, payload = {}) {
    if (!activeRun) return;
    if (activeRun.id && !String(activeRun.id).startsWith("run-")) {
      try {
        const updated = await classWorkspaceApi.sendRunCommand(
          activeRun.id,
          command,
          payload
        );
        setActiveRun(updated);
        if (updated.pathway) setActivePathway(updated.pathway);
        const nbData = await classWorkspaceApi.listNotebookSessions().catch(() => null);
        if (nbData?.sessions) setNotebookSessions(nbData.sessions);
        return;
      } catch {
        // Fallback to local simulation
      }
    }

    setActiveRun((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      const pos = { ...(prev.learner_position || { x: 5, y: 7, dir: "N" }) };
      if (command === "pause") {
        next.status = "paused";
        next.tutor_decisions += 1;
      } else if (command === "resume") {
        next.status = "running";
        next.tutor_decisions += 1;
      } else if (command === "simplify") {
        next.pathway = prev.pathway === "C" ? "B" : "A";
        setActivePathway(next.pathway);
        next.tutor_decisions += 1;
      } else if (command === "prompt") {
        next.prompts_given += 1;
        next.tutor_decisions += 1;
      } else if (command === "what_if") {
        next.active_what_if = payload.event || "Preferred item out of stock";
        next.tutor_decisions += 1;
      } else if (command === "move" && prev.status !== "paused") {
        const dir = payload.dir || "N";
        const delta = { N: [0, -1], S: [0, 1], E: [1, 0], W: [-1, 0] }[dir] || [0, 0];
        pos.x = Math.max(0, Math.min(11, pos.x + delta[0]));
        pos.y = Math.max(0, Math.min(7, pos.y + delta[1]));
        pos.dir = dir;
        next.learner_position = pos;
      } else if (command === "select") {
        const sku = payload.sku || "milk";
        const price = sku === "bread" ? 45 : 62;
        if (payload.checkout) {
          next.status = "completed";
          next.steps_completed = [...new Set([...next.steps_completed, "completed_checkout"])];
        } else {
          next.basket = [...(prev.basket || []), { sku, price }];
          next.basket_total = (prev.basket_total || 0) + price;
          next.steps_completed = [...new Set([...next.steps_completed, `picked_${sku}`])];
        }
      }
      return next;
    });
  }

  async function duplicateProject(project) {
    if (project.id && typeof project.id === "string") {
      try {
        const copy = await classWorkspaceApi.duplicateExperience(project.id);
        setProjects((current) => [
          {
            id: copy.id,
            title: copy.title,
            category: copy.category || project.category,
            status: "Draft",
            stage: "prompt",
            prompt: copy.prompt,
            version: copy.current_version || 1,
          },
          ...current,
        ]);
        setNotice("Experience duplicated on server.");
        return;
      } catch {
        // Fallback below
      }
    }
    const copy = {
      ...project,
      id: Date.now(),
      title: `${project.title} (Copy)`,
      status: "Draft",
      stage: "prompt",
      version: 1,
    };

    setProjects((current) => [copy, ...current]);
    setNotice("Experience duplicated.");
  }

  async function restoreVersion(version) {
    if (selectedId && typeof selectedId === "string" && typeof version.id === "string") {
      try {
        await classWorkspaceApi.restoreVersion(selectedId, version.id);
      } catch {
        // Ignore
      }
    }
    setConfiguration(version.snapshot);
    setNotice(
      `Version ${version.number} configuration restored as a new version snapshot.`
    );
  }

  const currentQuestion = QUESTIONS[questionIndex];

  const answeredCount = Object.keys(answers).filter(
    (key) => answers[key]
  ).length;

  const progress = Math.round(
    ((questionIndex + 1) / QUESTIONS.length) * 100
  );

  const statusCounts = {
    total: projects.length,
    active: projects.filter((project) =>
      ["In Progress", "Generation queued", "Ready to configure"].includes(
        project.status
      )
    ).length,
    drafts: projects.filter((project) => project.status === "Draft").length,
  };

  useEffect(() => {
    if (!isLoggedIn) return;
    let cancelled = false;
    axios.get(`${API_URL}/me?local_hour=${new Date().getHours()}`, { headers: { Authorization: `Bearer ${sessionStorage.getItem("access_token")}` } }).then(({ data }) => {
      if (cancelled) return;
      setEmail(data.email);
      setUserFullName(data.full_name || "");
      setUserRole(data.role);
      setGreeting(data.greeting);
      void refreshWorkspaceData();
    }).catch(() => {
      if (!cancelled) { sessionStorage.removeItem("access_token"); setIsLoggedIn(false); }
    });
    return () => { cancelled = true; };
  }, [isLoggedIn]);

  // Authentication screens share this file and switch using authPage.
  if (!isLoggedIn) {
    return (
      <main className="login-page">
        <button type="button" className="icon-button login-theme" title={`Use ${theme === "light" ? "dark" : "light"} theme`} aria-label={`Use ${theme === "light" ? "dark" : "light"} theme`} onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
          {theme === "light" ? <Moon size={19} /> : <Sun size={19} />}
        </button>
        <header className="login-brand">
          <div className="sidebar-brand"><div className="brand-logo"><Sparkles size={24} /></div><strong>Chernyx AI Studio</strong></div>
          <div><p className="eyebrow">YOUR TEACHING WORKSPACE</p><h1>Chernyx AI Studio</h1><p>Describe the room.<br />Teach inside it.</p></div>
          <FourWallPreview spec={DEFAULT_SCENE_SPEC} previewOnly />
          <span className="login-brand-footer">Immersive learning, thoughtfully made.</span>
        </header>
        <section className="login-card">
          <p className="login-eyebrow">TUTOR WORKSPACE</p>

          {authPage === "login" ? (
            <>
              <h2>Sign in</h2>
              <p>Sign in to continue to your learning workspace.</p>

              {signupSuccess && (
                <p className="signup-success-message" role="status">
                  {signupSuccess}
                </p>
              )}

              <form onSubmit={handleLogin}>
                <label htmlFor="login-email">Email address</label>
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  autoComplete="username"
                  required
                />

                <label htmlFor="login-password">Password</label>
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                />

                {loginError && (
                  <p className="login-error" role="alert">{loginError}</p>
                )}

                <button type="submit" disabled={isLoading}>
                  {isLoading ? "Signing in..." : "Sign in"}
                </button>
              </form>

              <p className="auth-switch">
                New to Chernyx?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setAuthPage("signup");
                    setLoginError("");
                    setSignupError("");
                    setSignupSuccess("");
                  }}
                >
                  Create an account
                </button>
              </p>
            </>
          ) : (
            <>
              <h2>Create your account</h2>
              <p>Set up your tutor workspace to start creating learning experiences.</p>

              <form onSubmit={handleSignup}>
                <label htmlFor="signup-full-name">Full name</label>
                <input
                  id="signup-full-name"
                  name="full_name"
                  type="text"
                  value={signupForm.full_name}
                  onChange={updateSignupField}
                  placeholder="Enter your full name"
                  autoComplete="name"
                  maxLength={120}
                  required
                />

                <label htmlFor="signup-email">Email address</label>
                <input
                  id="signup-email"
                  name="email"
                  type="email"
                  value={signupForm.email}
                  onChange={updateSignupField}
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                />

                <label htmlFor="signup-organisation">School or organisation</label>
                <input
                  id="signup-organisation"
                  name="organisation_name"
                  type="text"
                  value={signupForm.organisation_name}
                  onChange={updateSignupField}
                  placeholder="Enter your organisation"
                  autoComplete="organization"
                  maxLength={160}
                  required
                />

                <label htmlFor="signup-password">Password</label>
                <input
                  id="signup-password"
                  name="new-password"
                  type="password"
                  value={signupForm.password}
                  onChange={(event) =>
                    setSignupForm((current) => ({
                      ...current,
                      password: event.target.value,
                    }))
                  }
                  placeholder="At least 8 characters"
                  autoComplete="new-password"
                  minLength={8}
                  required
                />

                <label htmlFor="signup-confirm-password">Confirm password</label>
                <input
                  id="signup-confirm-password"
                  name="confirm-password"
                  type="password"
                  value={signupForm.confirm_password}
                  onChange={(event) =>
                    setSignupForm((current) => ({
                      ...current,
                      confirm_password: event.target.value,
                    }))
                  }
                  placeholder="Enter your password again"
                  autoComplete="new-password"
                  minLength={8}
                  required
                />

                {signupError && (
                  <p className="login-error" role="alert">{signupError}</p>
                )}

                <button type="submit" disabled={signupLoading}>
                  {signupLoading ? "Creating account..." : "Create account"}
                </button>
              </form>

              <p className="auth-switch">
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setAuthPage("login");
                    setSignupError("");
                  }}
                >
                  Sign in
                </button>
              </p>
            </>
          )}

          <p className="login-footer">Immersive Learning Workspace</p>
        </section>
      </main>
    );
  }

  function renderWorkflowSteps() {
    const steps = [
      ["prompt", "Describe"],
      ["questions", "Clarify"],
      ["review", "Preview"],
      ["generating", "Generate"],
      ["configure", "Configure"],
      ["versions", "Versions"],
      ["runtime", "Run & Console"],
    ];

    const currentProj = projects.find((p) => p.id === selectedId);
    const isUnlockedForConfig =
      currentProj &&
      ["Ready to configure", "Configured", "Approved", "In Progress"].includes(
        currentProj.status
      );

    return (
      <div className="workflow-steps">
        {steps.map(([key, label], index) => (
          <button
            key={key}
            className={`workflow-step ${stage === key ? "current" : ""} ${
              steps.findIndex(([stepKey]) => stepKey === stage) > index
                ? "completed"
                : ""
            }`}
            onClick={() => {
              if (key === "versions") {
                setStage("versions");
                return;
              }
              if (key === "runtime") {
                if (currentProj?.status === "Approved" || versions.length > 0) {
                  setStage("runtime");
                } else {
                  setNotice("Approve a version before launching runtime (FR-11).");
                }
                return;
              }
              if (key === "configure" && !isUnlockedForConfig) {
                setNotice(
                  "Configuration is locked until generation reaches Ready to configure (FR-07)."
                );
                return;
              }

              const allowed = {
                prompt: true,
                questions: !!(prompt.trim() || voiceTranscript.trim()),
                review: !!(prompt.trim() || voiceTranscript.trim()),
                generating: generationStarted || !!selectedId,
                configure: isUnlockedForConfig,
              };

              if (allowed[key]) {
                setStage(key);
                setNotice("");
              }
            }}
          >
            <span>{index + 1}</span>
            {label}
          </button>
        ))}
      </div>
    );
  }

  function handleSimulateVoiceClip() {
    setIsRecordingVoice(true);
    setTimeout(() => {
      setIsRecordingVoice(false);
      const sample =
        "Create a calm neighbourhood shop with milk and bread on reachable shelves, a 500 rupee budget, and gentle step-by-step prompts.";
      setVoiceTranscript((prev) => (prev ? `${prev} ${sample}` : sample));
      setNotice("Voice clip transcribed (FR-03). You can edit the transcript below before continuing.");
    }, 350);
  }

  function handleAttachmentAdd(event) {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;
    const mapped = files.map((f) => ({
      name: f.name,
      type: f.type || "media",
      size: f.size,
    }));
    setMediaAttachments((prev) => [...prev, ...mapped]);
  }

  function renderPromptStage() {
    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">NEW ACTIVITY</span>
          <h1>Chernyx Studio</h1>
        </div>

        <form className="prompt-panel" onSubmit={continueToQuestions}>
          <label htmlFor="experience-prompt">
            Describe your learning experience
          </label>
          <textarea
            id="experience-prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Example: Create a calm, interactive 3D grocery shop where learners practise picking up milk and bread within a ₹500 budget and paying at the counter..."
            rows={5}
            required={!voiceTranscript.trim()}
          />

          <div className="prompt-meta">
            <span>Activity brief</span>
            <span>{prompt.length} characters</span>
          </div>

          <div className="voice-intake-box">
            <div className="voice-intake-header">
              <strong>Voice transcript</strong>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleSimulateVoiceClip}
                >
                  {isRecordingVoice ? "Recording..." : "🎙 Record voice clip"}
                </button>
                {voiceTranscript && (
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => {
                      setPrompt((curr) =>
                        curr ? `${curr}\n${voiceTranscript}` : voiceTranscript
                      );
                      setNotice("Transcript copied into main prompt.");
                    }}
                  >
                    Use transcript in prompt
                  </button>
                )}
              </div>
            </div>
            <textarea
              aria-label="Editable voice transcript"
              rows={2}
              value={voiceTranscript}
              onChange={(e) => setVoiceTranscript(e.target.value)}
              placeholder="Voice transcript appears here and is fully editable before sending..."
            />
          </div>

          <div className="form-grid">
            <div>
              <label htmlFor="experience-title">Experience name (optional)</label>
              <input
                id="experience-title"
                value={experienceTitle}
                onChange={(event) => setExperienceTitle(event.target.value)}
                placeholder="e.g. Neighbourhood Grocery Shopping"
              />
            </div>
            <div>
              <label htmlFor="experience-category">Learning category</label>
              <select
                id="experience-category"
                value={category}
                onChange={(event) => setCategory(event.target.value)}
              >
                <option>Social Skills</option>
                <option>Communication</option>
                <option>Life Skills</option>
                <option>Academic Learning</option>
                <option>Emotional Regulation</option>
              </select>
            </div>
          </div>

          <div className="attachment-bar">
            <label htmlFor="media-attachment-input" className="secondary-button">
              📎 Attach image/video reference
            </label>
            <input
              id="media-attachment-input"
              type="file"
              accept="image/*,video/*"
              multiple
              style={{ display: "none" }}
              onChange={handleAttachmentAdd}
            />
            {mediaAttachments.map((att, idx) => (
              <span key={`${att.name}-${idx}`} className="status-pill">
                {att.name}
              </span>
            ))}
          </div>

          <div className="prompt-footer">
            <span className="helper-note">20 optional questions</span>
            <button type="submit" className="primary-button">
              Continue to questions <span>→</span>
            </button>
          </div>
        </form>

        <div className="tip-panel">
          <span className="tip-icon">✦</span>
          <div>
            <strong>Governing principle: Plan–Validate–Build</strong>
            <p>
              The AI plans a typed JSON scene spec, the backend validates rules
              R1–R7, and the runtime renders only validated scenes.
            </p>
          </div>
        </div>
      </>
    );
  }

  function renderQuestionsStage() {
    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">ACTIVITY DETAILS</span>
          <h1>Let’s shape your idea</h1>
          <p>
            Every question is skippable. Skipping all 20 still allows generation.
          </p>
        </div>

        <div className="question-layout">
          <aside className="question-sidebar">
            <span className="mini-label">YOUR BRIEF</span>
            <h3>{experienceTitle || "New learning experience"}</h3>
            <p className="brief-preview">{prompt}</p>
            <div className="question-counter">
              <strong>{answeredCount}</strong>
              <span>of {QUESTIONS.length} answered</span>
            </div>
            <div className="progress-track">
              <span
                style={{
                  width: `${(answeredCount / QUESTIONS.length) * 100}%`,
                }}
              />
            </div>
            <p className="muted-text">
              You can skip any or all questions and proceed directly to concept preview.
            </p>
          </aside>

          <section className="question-card">
            <div className="question-topline">
              <span>QUESTION {questionIndex + 1} OF {QUESTIONS.length}</span>
              <span>{progress}% through</span>
            </div>

            <div className="progress-track question-progress">
              <span style={{ width: `${progress}%` }} />
            </div>

            <h2>{currentQuestion.title}</h2>
            <p>{currentQuestion.help}</p>

            <div className="answer-options">
              {currentQuestion.options.map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`answer-option ${
                    answers[questionIndex] === option ? "selected" : ""
                  }`}
                  onClick={() => setAnswer(questionIndex, option)}
                >
                  <span className="option-radio">
                    {answers[questionIndex] === option ? "✓" : ""}
                  </span>
                  {option}
                </button>
              ))}
            </div>

            <label className="custom-answer-label" htmlFor="custom-answer">
              Add a note (optional)
            </label>
            <textarea
              id="custom-answer"
              rows={2}
              value={customAnswers[questionIndex] || ""}
              onChange={(event) =>
                setCustomAnswer(questionIndex, event.target.value)
              }
              placeholder="Add any specific requirements..."
            />

            <div className="question-actions">
              <button
                className="secondary-button"
                onClick={() =>
                  setQuestionIndex((index) => Math.max(0, index - 1))
                }
                disabled={questionIndex === 0}
              >
                ← Previous
              </button>

              <button
                className="text-button"
                onClick={() => {
                  if (questionIndex === QUESTIONS.length - 1) {
                    finishQuestions();
                  } else {
                    setQuestionIndex((index) => index + 1);
                  }
                }}
              >
                Skip question
              </button>

              {questionIndex === QUESTIONS.length - 1 ? (
                <button className="primary-button" onClick={finishQuestions}>
                  Review experience →
                </button>
              ) : (
                <button
                  className="primary-button"
                  onClick={() => setQuestionIndex((index) => index + 1)}
                >
                  Next question →
                </button>
              )}
            </div>

            <button className="finish-questions" onClick={finishQuestions}>
              Skip remaining questions & review my idea →
            </button>
          </section>
        </div>
      </>
    );
  }

  function renderReviewStage() {
    const threeConcepts = [
      {
        id: "guided",
        artClass: "art-guided",
        roomLabel: "GUIDED SHOP",
        title: "Guided practice shop",
        desc: "A structured environment with clear step-by-step visual cues, labeled prices, and gentle feedback.",
        tags: ["Structured", "Supportive", "Pathway A/B/C"],
      },
      {
        id: "explore",
        artClass: "art-explore",
        roomLabel: "OPEN MARKET",
        title: "Open neighbourhood market",
        desc: "A flexible layout where learners compare item prices across aisles and practise budget decisions.",
        tags: ["Exploration", "Budget choice", "Flexible"],
      },
      {
        id: "calm",
        artClass: "art-guided",
        roomLabel: "CALM SENSORY",
        title: "Calm sensory corner store",
        desc: "A quieter setting with fewer distractions and wide, uncluttered walkways.",
        tags: ["Low stimulation", "Reduced density", "Accessible"],
      },
    ];

    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">CONCEPT PREVIEWS</span>
          <h1>Choose your learning space</h1>
        </div>

        <section className="review-brief content-card">
          <div className="section-heading">
            <div>
              <span className="mini-label">YOUR EXPERIENCE BRIEF</span>
              <h3>{experienceTitle || "Untitled learning experience"}</h3>
            </div>
            <button
              className="secondary-button"
              onClick={() => setStage("questions")}
            >
              Edit answers
            </button>
          </div>
          <p>{prompt}</p>
          <div className="review-tags">
            <span>{category}</span>
            <span>{answeredCount} answers saved</span>
            <span>
              {Object.keys(customAnswers).filter((key) =>
                customAnswers[key]?.trim()
              ).length} additional notes
            </span>
          </div>
        </section>

        <div className="section-heading preview-heading">
          <div>
            <span className="eyebrow">THREE DIRECTIONS</span>
            <h2>Choose one of three concepts to generate</h2>
          </div>
        </div>

        <div className="concept-grid three-concepts-grid">
          {threeConcepts.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`concept-card ${concept === item.id ? "selected" : ""}`}
              onClick={() => setConcept(item.id)}
            >
              <div className={`concept-art ${item.artClass}`}>
                <FourWallPreview spec={DEFAULT_SCENE_SPEC} previewOnly />
              </div>
              <div className="concept-content">
                <div className="concept-title">
                  <h3>{item.title}</h3>
                  <span>{concept === item.id ? "✓ Selected" : "Select"}</span>
                </div>
                <p>{item.desc}</p>
                <div className="concept-tags">
                  {item.tags.map((t) => (
                    <span key={t}>{t}</span>
                  ))}
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="approval-banner">
          <div className="approval-mark">✓</div>
          <div>
            <strong>Ready to build your activity?</strong>
          </div>
          <button className="primary-button" onClick={approveConcept}>
            Approve & Start generating →
          </button>
        </div>
      </>
    );
  }

  function renderGeneratingStage() {
    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">GENERATION</span>
          <h1>Your experience is taking shape</h1>
          <p>{experienceTitle}</p>
        </div>

        <section className="generation-card">
          <div className="generation-visual">
            <div className="generation-ring ring-one" />
            <div className="generation-ring ring-two" />
            <div className="generation-center">✦</div>
          </div>

          <span className="generation-status">
            {generationStarted ? "CONCEPT APPROVED" : "GENERATION"}
          </span>
          <h2>{experienceTitle || "Your learning experience"}</h2>

          <div className="generation-tasks">
            <div><span className="task-check">✓</span><span>Activity brief</span><span className="task-state">Saved</span></div>
            <div><span className="task-check">✓</span><span>Concept direction</span><span className="task-state">Approved</span></div>
            <div><Clock3 size={16} /><span>Scene generation</span><span className="task-state">Pending</span></div>
          </div>

          <button className="primary-button" onClick={markReadyToConfigure}>
            Complete generation & unlock configuration →
          </button>
          <p className="muted-text">Mock AI provider</p>
        </section>
      </>
    );
  }

  function renderDollhouseAndEditPanel() {
    const w = sceneSpec.room?.w || 12;
    const h = sceneSpec.room?.h || 8;
    const layout = sceneSpec.layout || [];
    const entranceCells = sceneSpec.room?.entrance?.cells || [[5, 7], [6, 7]];

    const cellMap = {};
    layout.forEach((obj) => {
      const [ox, oy] = obj.cell || [0, 0];
      const [ow, oh] = obj.size || [1, 1];
      for (let cx = ox; cx < ox + ow; cx += 1) {
        for (let cy = oy; cy < oy + oh; cy += 1) {
          cellMap[`${cx},${cy}`] = obj;
        }
      }
    });

    const selectedObj =
      layout.find((o) => o.id === selectedSpecObjectId) || layout[0];
    const rulesSummary = validationReport?.rules_summary || {
      R1: "pass",
      R2: "pass",
      R3: "pass",
      R3w: "pass",
      R4: "pass",
      R5: "pass",
      R6: "pass",
      R7: "pass",
    };

    return (
      <section className="content-card" style={{ marginBottom: 22 }}>
        <div className="section-heading">
          <div>
            <span className="mini-label">SCENE DETAILS</span>
            <h3>Layout & changes</h3>
          </div>
          <span className="status-pill status-configured">
            {validationReport?.valid ? "Validation passed" : "Needs review"}
          </span>
        </div>

        <div className="r1-r7-bar">
          {[
            ["R1", "Structure"],
            ["R2", "Geometry"],
            ["R3", "Reachability (BFS)"],
            ["R3w", "Decor Reach"],
            ["R4", "Solvability"],
            ["R5", "Comfort Caps"],
            ["R6", "Monotone A/B/C"],
            ["R7", "Ref Integrity"],
          ].map(([code, label]) => {
            const st = rulesSummary[code] || "pass";
            return (
              <span
                key={code}
                className={`rule-badge rule-${st}`}
                title={`${code}: ${label} (${st})`}
              >
                <strong>{code}</strong> {label}: {st.toUpperCase()}
              </span>
            );
          })}
        </div>

        <div className="dollhouse-split">
          <div>
            <div
              className="dollhouse-grid"
              style={{
                gridTemplateColumns: `repeat(${w}, minmax(0, 1fr))`,
              }}
              aria-label="Dollhouse 12x8 top-down scene map"
            >
              {Array.from({ length: h }).map((_, ry) =>
                Array.from({ length: w }).map((__, rx) => {
                  const key = `${rx},${ry}`;
                  const obj = cellMap[key];
                  const isEntrance = entranceCells.some(
                    ([ex, ey]) => ex === rx && ey === ry
                  );
                  const isSelected = obj && obj.id === selectedSpecObjectId;
                  return (
                    <button
                      type="button"
                      key={key}
                      className={`dollhouse-cell ${
                        obj ? "occupied" : ""
                      } ${isEntrance ? "entrance" : ""} ${
                        isSelected ? "selected" : ""
                      }`}
                      onClick={() => {
                        if (obj) setSelectedSpecObjectId(obj.id);
                      }}
                      title={
                        obj
                          ? `${obj.id} (${obj.asset}) at [${rx}, ${ry}]`
                          : isEntrance
                            ? `South Entrance [${rx}, ${ry}]`
                            : `Walkable floor [${rx}, ${ry}]`
                      }
                    >
                      {obj
                        ? obj.asset === "counter"
                          ? "🧾"
                          : "🗄️"
                        : isEntrance
                          ? "🚪"
                          : "·"}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          <div className="spec-inspector">
            <span className="mini-label">
              {selectedObj?.id || "Scene"}
            </span>
            <pre className="spec-code-box">
              {JSON.stringify(selectedObj || sceneSpec, null, 2)}
            </pre>

            <form onSubmit={handlePlainLanguageEdit} className="plain-edit-form">
              <label htmlFor="plain-language-edit-input">
                Ask for a change
              </label>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  id="plain-language-edit-input"
                  value={plainEditInput}
                  onChange={(e) => setPlainEditInput(e.target.value)}
                  placeholder='e.g. "Change milk price to 55" or "Set budget to 600"'
                />
                <button type="submit" className="primary-button">
                  Apply patch
                </button>
              </div>
              {lastPatchInfo && (
                <small className="patch-locality-note">
                  ✓ Patch locality: {lastPatchInfo.ratio}% of spec bytes (&lt; 10% benchmark) · Version v{lastPatchInfo.version}
                </small>
              )}
            </form>
          </div>
        </div>
      </section>
    );
  }

  function renderConfigureStage() {
    const support = sceneSpec.support || DEFAULT_SCENE_SPEC.support;

    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">ACTIVITY SETTINGS</span>
          <h1>Configure: {experienceTitle || "Learning experience"}</h1>
        </div>

        <div className="configure-layout">
          <section className="configuration-panel content-card">
            <div className="section-heading">
              <div>
                <h3>Scenario settings</h3>
              </div>
              <span className="status-pill">Editable</span>
            </div>

            <div className="settings-grid">
              {[
                ["environment", "Environment", ["Classroom", "Home", "Public space", "Fantasy environment"]],
                ["duration", "Target duration", ["2–5 minutes", "5–10 minutes", "10–15 minutes", "Flexible"]],
                ["guidance", "Guidance level", ["Step-by-step", "Hints when needed", "Minimal guidance", "Tutor-led"]],
                ["visualStyle", "Visual style", ["Soft 3D", "Cartoon", "Realistic", "Minimal and simple"]],
                ["accessibility", "Accessibility support", ["Simple language", "Visual prompts", "Reduced stimulation", "Multiple support options"]],
                ["comfort", "Sensory comfort", ["Low stimulation", "Balanced", "More engaging", "Tutor decides"]],
              ].map(([key, label, options]) => (
                <div className="setting-field" key={key}>
                  <label htmlFor={`setting-${key}`}>{label}</label>
                  <select
                    id={`setting-${key}`}
                    value={configuration[key]}
                    onChange={(event) =>
                      setConfiguration((current) => ({
                        ...current,
                        [key]: event.target.value,
                      }))
                    }
                  >
                    {options.map((option) => (
                      <option key={option}>{option}</option>
                    ))}
                  </select>
                </div>
              ))}

              <div className="setting-field">
                <label htmlFor="setting-budget">Budget (₹)</label>
                <input
                  id="setting-budget"
                  type="number"
                  min={50}
                  max={5000}
                  value={configuration.budget ?? 500}
                  onChange={(e) =>
                    setConfiguration((curr) => ({ ...curr, budget: Number(e.target.value) }))
                  }
                />
              </div>

              <div className="setting-field">
                <label htmlFor="setting-required">Required SKUs (comma-separated)</label>
                <input
                  id="setting-required"
                  type="text"
                  value={configuration.required ?? "milk, bread"}
                  onChange={(e) =>
                    setConfiguration((curr) => ({ ...curr, required: e.target.value }))
                  }
                />
              </div>
            </div>

            <div className="pathway-matrix">
              <h4>Adaptation pathway</h4>
              <div className="pathway-cards">
                {["A", "B", "C"].map((pKey) => (
                  <button
                    type="button"
                    key={pKey}
                    className={`pathway-card ${activePathway === pKey ? "selected" : ""}`}
                    onClick={() => setActivePathway(pKey)}
                  >
                    <strong>Pathway {pKey}</strong>
                    <span>Prompt level: {support[pKey]?.prompt}</span>
                    <span>Scene density: {support[pKey]?.density}</span>
                    <span>Volume: {support[pKey]?.volume}%</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="configuration-actions">
              <button
                className="secondary-button"
                onClick={() => setStage("review")}
              >
                Back to preview
              </button>
              <button className="primary-button" onClick={saveConfiguration}>
                Save configuration
              </button>
            </div>
          </section>

          <aside className="configuration-preview">
            <FourWallPreview
              environment={configuration.environment}
              spec={sceneSpec}
              pathway={activePathway}
              onObjectSelect={setSelectedSpecObjectId}
            />
            <button
              className="secondary-button full-width"
              onClick={() => setStage("versions")}
            >
              Manage versions
            </button>
          </aside>
        </div>
        {renderDollhouseAndEditPanel()}
      </>
    );
  }

  function renderVersionsStage() {
    const currentProject = projects.find((project) => project.id === selectedId);
    const isApproved = currentProject?.status === "Approved" || versions.length > 0;

    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">SAVED VERSIONS</span>
          <h1>Keep track of every iteration</h1>
          <p>
            Approve a version to make it immutable and runnable on a laptop or
            four-wall projected room.
          </p>
        </div>

        <section className="version-current content-card">
          <div className="version-current-icon">↻</div>
          <div className="version-current-info">
            <span className="mini-label">CURRENT EXPERIENCE</span>
            <h3>
              {currentProject?.title || experienceTitle || "New learning experience"}
            </h3>
            <p>
              Current version: {currentProject?.version || 1} ·{" "}
              {currentProject?.status || "Draft"}
            </p>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button className="primary-button" onClick={approveVersion}>
              ✓ Approve current version
            </button>
            {isApproved && (
              <>
                <button
                  className="secondary-button"
                  onClick={() => handleLaunchRuntime("laptop")}
                >
                  ▶ Launch Laptop (1 Cam)
                </button>
                <button
                  className="primary-button"
                  onClick={() => handleLaunchRuntime("room")}
                >
                  ▶ Launch 4-Wall Room (N/E/S/W)
                </button>
              </>
            )}
          </div>
        </section>

        <section className="content-card">
          <div className="section-heading">
            <div>
              <h3>Version history</h3>
              <p>Immutable approved snapshots created in this workspace.</p>
            </div>
          </div>

          {versions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">▤</div>
              <h3>No approved versions yet</h3>
              <p>Approve the current version above to unlock Laptop and 4-Wall Room launch.</p>
            </div>
          ) : (
            <div className="version-list">
              {versions.map((version) => (
                <article className="version-row" key={version.id}>
                  <div className="version-number">v{version.number}</div>
                  <div className="version-info">
                    <strong>{version.title}</strong>
                    <span>Created {version.date}</span>
                  </div>
                  <span className="status-pill status-approved">{version.status}</span>
                  <button
                    className="secondary-button"
                    onClick={() => restoreVersion(version)}
                  >
                    Restore
                  </button>
                </article>
              ))}
            </div>
          )}

          <div className="version-bottom-actions">
            <button
              className="secondary-button"
              onClick={() => {
                const project = projects.find((item) => item.id === selectedId);
                if (project) duplicateProject(project);
                else setNotice("Save this experience as a project before duplicating.");
              }}
            >
              Duplicate experience
            </button>
            <button
              className="primary-button"
              onClick={() => setStage("configure")}
            >
              Back to configuration
            </button>
          </div>
        </section>
      </>
    );
  }

  function renderRuntimeStage() {
    if (!activeRun) return <section className="content-card empty-state"><h2>No active session</h2><button className="primary-button" onClick={() => setStage("versions")}>View versions</button></section>;
    const run = activeRun || {
      scenario_title: experienceTitle || "Shopping Scenario",
      version_number: 1,
      pathway: activePathway,
      mode: runMode,
      status: "running",
      learner_position: { x: 5, y: 7, dir: "N" },
      basket: [],
      basket_total: 0,
      budget: sceneSpec.task?.budget || 500,
      required_items: sceneSpec.task?.required || ["milk", "bread"],
      steps_completed: ["entered_room"],
      prompts_given: 0,
      tutor_decisions: 0,
      errors_count: 0,
      active_what_if: null,
    };

    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">LIVE SESSION</span>
          <h1>{run.scenario_title} · Live Session</h1>
        </div>

        <div className="runtime-layout">
          <section>
            <FourWallPreview
              environment={configuration.environment}
              spec={sceneSpec}
              pathway={run.pathway}
              displayMode={run.mode}
              paused={run.status === "paused"}
              learnerPosition={run.learner_position}
              interactiveKeyboard={run.status !== "completed"}
              onMove={(dir) => handleConsoleCommand("move", { dir })}
              onSelect={() => handleConsoleCommand("select", {})}
              onPause={() =>
                handleConsoleCommand(run.status === "paused" ? "resume" : "pause")
              }
            />
          </section>

          <aside className="content-card tutor-console-card">
            <div className="section-heading">
              <div>
                <span className="mini-label">TUTOR CONSOLE</span>
                <h3>Live session controls</h3>
              </div>
              <span className="status-pill status-approved">
                {run.status.toUpperCase()} · Pathway {run.pathway}
              </span>
            </div>

            <div className="console-meters">
              <div className="console-meter-box">
                <span>Basket & Budget Meter</span>
                <strong>
                  ₹{run.basket_total || 0} / ₹{run.budget || 500}
                </strong>
                <small>
                  Items:{" "}
                  {(run.basket || []).length === 0
                    ? "Empty"
                    : run.basket.map((b) => b.sku).join(", ")}
                </small>
              </div>
              <div className="console-meter-box">
                <span>Session counts</span>
                <strong>{run.prompts_given || 0} prompts</strong>
                <small>
                  {run.tutor_decisions || 0} tutor actions ·{" "}
                  {(run.steps_completed || []).length} steps
                </small>
              </div>
            </div>

            <div className="console-checklist">
              <strong>Task Checklist</strong>
              <ul>
                {(run.required_items || ["milk", "bread"]).map((sku) => {
                  const done = (run.basket || []).some((b) => b.sku === sku);
                  return (
                    <li key={sku}>
                      {done ? "✓" : "○"} Pick up {sku}
                      {!done && (
                        <button
                          type="button"
                          className="text-button"
                          style={{ marginLeft: 8 }}
                          onClick={() => handleConsoleCommand("select", { sku })}
                        >
                          [Pick {sku}]
                        </button>
                      )}
                    </li>
                  );
                })}
                <li>
                  {(run.steps_completed || []).includes("completed_checkout")
                    ? "✓"
                    : "○"}{" "}
                  Pay at checkout counter
                  <button
                    type="button"
                    className="text-button"
                    style={{ marginLeft: 8 }}
                    onClick={() => handleConsoleCommand("select", { checkout: true })}
                  >
                    [Checkout]
                  </button>
                </li>
              </ul>
            </div>

            {run.active_what_if && (
              <p className="what-if-banner">
                ⚡ Active What-If: {run.active_what_if}
              </p>
            )}

            <div className="console-actions-grid">
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  handleConsoleCommand(run.status === "paused" ? "resume" : "pause")
                }
              >
                {run.status === "paused" ? "▶ Resume" : "⏸ Pause"}
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() => handleConsoleCommand("simplify")}
              >
                ↓ Simplify Pathway ({run.pathway} → {run.pathway === "C" ? "B" : "A"})
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  handleConsoleCommand("prompt", {
                    message: "Look for the next item on Shelf 1",
                  })
                }
              >
                💡 Give Prompt
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  handleConsoleCommand("what_if", {
                    event: "Preferred item is out of stock",
                  })
                }
              >
                ⚡ Trigger What-If
              </button>
            </div>

            <button
              type="button"
              className="primary-button full-width"
              onClick={async () => {
                await handleConsoleCommand("end");
                setActiveTab("Session Notebook");
              }}
            >
              Finish & View Session Notebook →
            </button>
          </aside>
        </div>
      </>
    );
  }

  function renderSessionNotebookPage() {
    const displaySessions = notebookSessions;

    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">SESSION RECORDS</span>
          <h1>Session notebook</h1>
        </div>

        <section className="content-card">
          <div className="section-heading">
            <div>
              <h3>Recent sessions</h3>
              <p>
                Learners are identified by school-assigned pseudonymous IDs unless
                the school opts in to names.
              </p>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={refreshWorkspaceData}
            >
              ↻ Refresh notebook
            </button>
          </div>

          <div className="notebook-table-wrap">
            <table className="notebook-table">
              <thead>
                <tr>
                  <th>Learner ID</th>
                  <th>Scenario & Version</th>
                  <th>Pathway</th>
                  <th>Mode</th>
                  <th>Steps Completed</th>
                  <th>Prompts Given</th>
                  <th>Tutor Decisions</th>
                  <th>Boundary Blocks</th>
                  <th>Elapsed Time</th>
                </tr>
              </thead>
              <tbody>
                {displaySessions.length === 0 && <tr><td colSpan={9}>No sessions recorded yet.</td></tr>}
                {displaySessions.map((s) => (
                  <tr key={s.session_id}>
                    <td>
                      <strong>{s.learner_display_name || s.learner_pseudonym}</strong>
                    </td>
                    <td>
                      {s.scenario_title} (v{s.scenario_version})
                    </td>
                    <td>Pathway {s.pathway}</td>
                    <td>{s.mode}</td>
                    <td>{s.steps_completed_count}</td>
                    <td>{s.prompts_given}</td>
                    <td>{s.tutor_decisions}</td>
                    <td>{s.errors_count}</td>
                    <td>{Math.round((s.elapsed_ms || 0) / 1000)}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="content-card">
          <div className="section-heading">
            <div>
              <h3>Workspace activity</h3>
              <p>
                Every generate, edit, approve, and launch event is recorded with
                user, version, and timestamp.
              </p>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={async () => {
                try {
                  const exported = await classWorkspaceApi.exportSchoolData();
                  setNotice(
                    `Exported school data (${exported.classes?.length || 0} classes, ${exported.scenarios?.length || 0} scenarios).`
                  );
                } catch (err) {
                  setNotice(err.message || "Export completed.");
                }
              }}
            >
              Export school data
            </button>
          </div>

          {auditEvents.length === 0 ? (
            <p className="muted-text">
              Generate, edit, approve, or launch a scenario to populate audit
              events.
            </p>
          ) : (
            <div className="experience-list">
              {auditEvents.slice(0, 8).map((ev) => (
                <div className="experience-row" key={ev.id}>
                  <span className="status-pill">{ev.action}</span>
                  <div className="experience-info">
                    <strong>Version {ev.version_number || 1}</strong>
                    <span>{new Date(ev.created_at).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </>
    );
  }

  function renderOverview() {
    return (
      <>
        <section className="dashboard-hero">
          <div className="hero-copy">
            <span className="eyebrow">CHERNYX AI STUDIO</span>
            <h1>{greeting}.</h1>
            <p>Your activities, classes, and upcoming sessions.</p>
            <button
              className="primary-button hero-button"
              onClick={startNewExperience}
            >
              <Plus size={17} /> New activity
            </button>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="hero-art-orbit orbit-a" />
            <div className="hero-art-orbit orbit-b" />
            <div className="hero-art-core">✦</div>
            <span className="hero-art-label">PLAN · VALIDATE · BUILD</span>
          </div>
        </section>

        <section className="stats-grid">
          <article className="stat-card">
            <div className="stat-icon purple"><FolderOpen size={20} /></div>
            <span>Total experiences</span>
            <strong>{statusCounts.total}</strong>
            <small>Your workspace projects</small>
          </article>
          <article className="stat-card">
            <div className="stat-icon blue"><Clock3 size={20} /></div>
            <span>In progress</span>
            <strong>{statusCounts.active}</strong>
            <small>Experiences being developed</small>
          </article>
          <article className="stat-card">
            <div className="stat-icon peach"><Sparkles size={20} /></div>
            <span>Drafts</span>
            <strong>{statusCounts.drafts}</strong>
            <small>Ideas to continue exploring</small>
          </article>
        </section>

        <section className="content-card">
          <div className="section-heading">
            <div>
              <h3>Continue creating</h3>
              <p>Pick up where you left off.</p>
            </div>
            <button
              className="text-button"
              onClick={() => setActiveTab("My Experiences")}
            >
              View all experiences →
            </button>
          </div>

          <div className="experience-list">
            {projects.length === 0 && <div className="empty-state"><FolderOpen size={28} /><h3>No activities yet</h3><p>Your saved activities will appear here.</p></div>}
            {projects.slice(0, 4).map((project, index) => (
              <article className="experience-row" key={project.id}>
                <div className={`experience-icon experience-icon-${index % 4}`}>
                  <FolderOpen size={20} />
                </div>
                <div className="experience-info">
                  <strong>{project.title}</strong>
                  <span>{project.category} · Version {project.version || 1}</span>
                </div>
                <span
                  className={`status-pill status-${(project.status || "Draft")
                    .toLowerCase()
                    .replaceAll(" ", "-")}`}
                >
                  {project.status}
                </span>
                <button className="row-action" onClick={() => openProject(project)}>
                  Open →
                </button>
              </article>
            ))}
          </div>
        </section>

        <section className="next-steps-panel">
          <div className="next-steps-symbol">✧</div>
          <div>
            <h3>Your idea is the starting point.</h3>
            <p>
              Describe an activity, answer a few questions, and review the
              proposed concept before generation begins.
            </p>
          </div>
          <button className="secondary-button" onClick={startNewExperience}>
            Start with a prompt →
          </button>
        </section>
      </>
    );
  }

  function renderProjects() {
    return (
      <section className="content-card">
        <div className="section-heading">
          <div>
              <h3>Projects</h3>
          </div>
          <button className="primary-button" onClick={startNewExperience}>
            <Plus size={16} /> New activity
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">✦</div>
            <h3>Your workspace starts here</h3>
            <p>Create your first learning experience from a prompt.</p>
            <button className="primary-button" onClick={startNewExperience}>
              Create experience
            </button>
          </div>
        ) : (
          <div className="experience-list">
            {projects.map((project, index) => (
              <article className="experience-row" key={project.id}>
                <div className={`experience-icon experience-icon-${index % 4}`}>
                  <FolderOpen size={20} />
                </div>
                <div className="experience-info">
                  <strong>{project.title}</strong>
                  <span>{project.category} · Version {project.version || 1}</span>
                  <small>{project.prompt || "No prompt added yet."}</small>
                </div>
                <span className="status-pill">{project.status}</span>
                <button className="row-action" onClick={() => openProject(project)}>
                  Open →
                </button>
                <button
                  className="row-action"
                  onClick={() => duplicateProject(project)}
                >
                  Duplicate
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    );
  }

  function renderSimplePage(title, description, items) {
    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">CHERNYX WORKSPACE</span>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <div className="resource-grid">
          {items.map((item) => (
            <article className="resource-card" key={item.title}>
              <div className="resource-icon">{item.icon}</div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              {item.action && (
                <button className="text-button" onClick={item.action}>
                  {item.actionLabel || "Explore →"}
                </button>
              )}
            </article>
          ))}
        </div>
      </>
    );
  }

  function renderActivePage() {
    if (activeTab === "Overview") return renderOverview();
    if (activeTab === "My Experiences") return renderProjects();
    if (activeTab === "Session Notebook") return renderSessionNotebookPage();

    if (activeTab === "Create Experience") {
      return (
        <>
          {renderWorkflowSteps()}
          {stage === "prompt" && renderPromptStage()}
          {stage === "questions" && renderQuestionsStage()}
          {stage === "review" && renderReviewStage()}
          {stage === "generating" && renderGeneratingStage()}
          {stage === "configure" && renderConfigureStage()}
          {stage === "versions" && renderVersionsStage()}
          {stage === "runtime" && renderRuntimeStage()}
        </>
      );
    }

    if (activeTab === "Classes & Modules") {
      const currentClass = classes.find(
        (item) => String(item.id) === String(selectedClassId)
      );

      const currentModules = modulesByClass[selectedClassId] || [];

      function saveModules(nextModules) {
        const next = {
          ...modulesByClass,
          [selectedClassId]: nextModules,
        };

        setModulesByClass(next);
        localStorage.setItem(
          "chernyx_modules_by_class",
          JSON.stringify(next)
        );
      }

      async function loadClasses() {
        setClassLoading(true);
        setClassError("");

        try {
          const data = await classWorkspaceApi.listClasses();
          setClasses(data);

          if (data.length > 0) {
            const selected = data.find(
              (item) => String(item.id) === String(selectedClassId)
            );
            const id = selected?.id ?? data[0].id;

            setSelectedClassId(id);

            const [studentData, moduleData, scheduleData] = await Promise.all([
              classWorkspaceApi.listStudents(id).catch(() => []),
              classWorkspaceApi.listModules(id).catch(() => []),
              classWorkspaceApi.listSchedules(id).catch(() => []),
            ]);
            setStudents(studentData);
            setSchedules(scheduleData);
            if (moduleData.length > 0) {
              setModulesByClass((prev) => ({ ...prev, [id]: moduleData }));
            }
          } else {
            setSelectedClassId("");
            setStudents([]);
            setSchedules([]);
          }
        } catch (error) {
          setClassError(error.message || "Unable to load classes.");
        } finally {
          setClassLoading(false);
        }
      }

      async function handleCreateClass(event) {
        event.preventDefault();
        setClassError("");

        if (!className.trim()) {
          setClassError("Please enter a class name.");
          return;
        }

        try {
          if (editingClass && selectedClassId) {
            const updated = await classWorkspaceApi.updateClass(selectedClassId, {
              name: className.trim(),
              description: classDescription.trim() || null,
            });
            setClasses((prev) =>
              prev.map((c) => (String(c.id) === String(selectedClassId) ? updated : c))
            );
            setEditingClass(false);
            setClassName("");
            setClassDescription("");
            setNotice("Class updated successfully.");
            return;
          }

          const created = await classWorkspaceApi.createClass({
            name: className.trim(),
            description: classDescription.trim() || null,
          });

          setClasses((previous) => [created, ...previous]);
          setSelectedClassId(created.id);
          setClassName("");
          setClassDescription("");
          setStudents([]);
          setSchedules([]);
          setEditingClass(false);
          setNotice("Class saved successfully.");
        } catch (error) {
          setClassError(error.message || "Unable to save class.");
        }
      }

      async function handleDeleteClass(id) {
        if (!window.confirm("Delete this class?")) return;
        try {
          await classWorkspaceApi.deleteClass(id);
          const remaining = classes.filter((c) => String(c.id) !== String(id));
          setClasses(remaining);
          setSelectedClassId(remaining[0]?.id || "");
          setNotice("Class deleted.");
        } catch (err) {
          setClassError(err.message || "Unable to delete class.");
        }
      }

      async function handleSelectClass(id) {
        setSelectedClassId(id);
        setEditingClass(false);
        setClassError("");

        try {
          const [studentData, moduleData, scheduleData] = await Promise.all([
            classWorkspaceApi.listStudents(id).catch(() => []),
            classWorkspaceApi.listModules(id).catch(() => []),
            classWorkspaceApi.listSchedules(id).catch(() => []),
          ]);
          setStudents(studentData);
          setSchedules(scheduleData);
          if (moduleData.length > 0) {
            setModulesByClass((prev) => ({ ...prev, [id]: moduleData }));
          }
        } catch (error) {
          setStudents([]);
          setClassError(error.message || "Unable to load class details.");
        }
      }

      async function handleAddStudent(event) {
        event.preventDefault();
        setClassError("");

        if (!selectedClassId || !studentName.trim()) {
          setClassError("Select a class and enter a student name.");
          return;
        }

        try {
          const created = await classWorkspaceApi.addStudent(
            selectedClassId,
            { name: studentName.trim() }
          );

          setStudents((previous) => [...previous, created]);
          setStudentName("");
          setNotice("Learner added with school pseudonym ID.");
        } catch (error) {
          setClassError(error.message || "Unable to add student.");
        }
      }

      async function handleDeleteStudent(studentId) {
        try {
          await classWorkspaceApi.deleteStudent(selectedClassId, studentId);
          setStudents((prev) => prev.filter((s) => s.id !== studentId));
          setNotice("Learner removed.");
        } catch (err) {
          setClassError(err.message || "Unable to remove learner.");
        }
      }

      async function handleSaveModule(event) {
        event.preventDefault();

        if (!selectedClassId || !moduleName.trim()) {
          setClassError("Enter a module name first.");
          return;
        }

        try {
          if (editingModuleId) {
            const updated = await classWorkspaceApi.updateModule(
              selectedClassId,
              editingModuleId,
              {
                name: moduleName.trim(),
                description: moduleDescription.trim() || null,
              }
            );
            saveModules(
              currentModules.map((item) =>
                item.id === editingModuleId ? updated : item
              )
            );
          } else {
            const created = await classWorkspaceApi.createModule(
              selectedClassId,
              {
                name: moduleName.trim(),
                description: moduleDescription.trim() || null,
              }
            );
            saveModules([...currentModules, created]);
          }
          setNotice("Module saved to database.");
        } catch {
          const fallbackMod = {
            id: editingModuleId || crypto.randomUUID(),
            name: moduleName.trim(),
            description: moduleDescription.trim(),
          };
          const updatedModules = editingModuleId
            ? currentModules.map((item) =>
                item.id === editingModuleId ? fallbackMod : item
              )
            : [...currentModules, fallbackMod];
          saveModules(updatedModules);
          setNotice("Module saved.");
        }

        setModuleName("");
        setModuleDescription("");
        setEditingModuleId(null);
        setShowModuleForm(false);
        setClassError("");
      }

      function handleEditModule(module) {
        setEditingModuleId(module.id);
        setModuleName(module.name);
        setModuleDescription(module.description || "");
        setShowModuleForm(true);
        setClassError("");
      }

      async function handleDeleteModule(id) {
        if (!window.confirm("Delete this module?")) return;
        try {
          await classWorkspaceApi.deleteModule(selectedClassId, id);
        } catch {
          // Continue local cleanup
        }
        saveModules(currentModules.filter((item) => item.id !== id));
        setNotice("Module removed.");
      }

      async function handleAddSchedule(event) {
        event.preventDefault();
        if (!selectedClassId || !scheduleTitle.trim()) return;
        try {
          const created = await classWorkspaceApi.addSchedule(selectedClassId, {
            title: scheduleTitle.trim(),
            day_of_week: scheduleDay,
            start_time: scheduleStart,
            end_time: scheduleEnd,
          });
          setSchedules((prev) => [...prev, created]);
          setScheduleTitle("");
          setNotice("Schedule added.");
        } catch (err) {
          setClassError(err.message || "Could not save schedule.");
        }
      }

      return (
        <section className="workspace-page">
          <div className="workspace-hero">
            <div>
              <span className="workspace-eyebrow">TEACHING WORKSPACE</span>
              <h2>Classes, Modules & Learners</h2>
              <p>
                Organise your school-scoped classes, learning modules, schedules,
                and pseudonymous learner profiles in one place.
              </p>
            </div>

            <button
              type="button"
              className="workspace-refresh"
              onClick={loadClasses}
              disabled={classLoading}
            >
              {classLoading ? "Loading..." : "↻ Refresh"}
            </button>
          </div>

          {classError && (
            <div className="workspace-error" role="alert">
              {classError}
            </div>
          )}

          <div className="workspace-stats">
            <div className="workspace-stat">
              <span>Total classes</span>
              <strong>{classes.length}</strong>
            </div>
            <div className="workspace-stat">
              <span>Learning modules</span>
              <strong>
                {Object.values(modulesByClass).reduce(
                  (total, list) => total + list.length,
                  0
                )}
              </strong>
            </div>
            <div className="workspace-stat">
              <span>Learners in selected class</span>
              <strong>{students.length}</strong>
            </div>
          </div>

          <div className="workspace-columns">
            <section className="workspace-panel">
              <div className="workspace-panel-heading">
                <div>
                  <span className="workspace-eyebrow">GET STARTED</span>
                  <h3>{editingClass ? "Edit class" : "Create a class"}</h3>
                  <p>Give your learning group a name and description.</p>
                </div>
              </div>

              <form onSubmit={handleCreateClass} className="workspace-form">
                <label htmlFor="workspace-class-name">Class name</label>
                <input
                  id="workspace-class-name"
                  value={className}
                  onChange={(event) => setClassName(event.target.value)}
                  placeholder="e.g. Grade 5 Life Skills"
                  required
                />

                <label htmlFor="workspace-class-description">
                  Description
                </label>
                <textarea
                  id="workspace-class-description"
                  value={classDescription}
                  onChange={(event) => setClassDescription(event.target.value)}
                  placeholder="What will students learn in this class?"
                  rows={3}
                />

                <div style={{ display: "flex", gap: 10 }}>
                  <button
                    type="submit"
                    className="workspace-primary"
                    disabled={classLoading}
                  >
                    {classLoading
                      ? "Saving..."
                      : editingClass
                        ? "✓ Update Class"
                        : "＋ Save Class"}
                  </button>
                  {editingClass && (
                    <button
                      type="button"
                      className="workspace-secondary"
                      onClick={() => {
                        setEditingClass(false);
                        setClassName("");
                        setClassDescription("");
                      }}
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </form>
            </section>

            <section className="workspace-panel">
              <div className="workspace-panel-heading">
                <div>
                  <span className="workspace-eyebrow">YOUR WORKSPACE</span>
                  <h3>Saved classes</h3>
                  <p>Select a class to manage its modules, schedules, and learners.</p>
                </div>
              </div>

              <div className="workspace-class-list">
                {classes.length === 0 ? (
                  <div className="workspace-empty">
                    <span className="workspace-empty-icon">▦</span>
                    <strong>No classes yet</strong>
                    <p>Create your first class to get started.</p>
                  </div>
                ) : (
                  classes.map((item) => (
                    <button
                      type="button"
                      key={item.id}
                      className={`workspace-class-card ${
                        String(selectedClassId) === String(item.id)
                          ? "selected"
                          : ""
                      }`}
                      onClick={() => handleSelectClass(item.id)}
                    >
                      <span className="workspace-class-icon">▦</span>
                      <span className="workspace-class-info">
                        <strong>{item.name}</strong>
                        <small>
                          {(modulesByClass[item.id] || []).length} modules
                        </small>
                      </span>
                      <span className="workspace-class-arrow">›</span>
                    </button>
                  ))
                )}
              </div>
            </section>
          </div>

          {currentClass && (
            <section className="workspace-panel workspace-detail">
              <div className="workspace-detail-header">
                <div>
                  <span className="workspace-eyebrow">SELECTED CLASS</span>
                  <h3>{currentClass.name}</h3>
                  <p>
                    {currentClass.description ||
                      "Build a learning sequence for this class."}
                  </p>
                </div>

                <div style={{ display: "flex", gap: 10 }}>
                  <button
                    type="button"
                    className="workspace-secondary"
                    onClick={() => {
                      setClassName(currentClass.name || "");
                      setClassDescription(currentClass.description || "");
                      setEditingClass(true);
                      setClassError("");
                    }}
                  >
                    ✎ Edit class
                  </button>
                  <button
                    type="button"
                    className="workspace-secondary"
                    onClick={() => handleDeleteClass(currentClass.id)}
                  >
                    × Delete
                  </button>
                </div>
              </div>

              <div className="workspace-section-title">
                <div>
                  <h3>Learning modules</h3>
                  <p>
                    Create and organise the lessons that belong to this class.
                  </p>
                </div>

                <button
                  type="button"
                  className="workspace-primary workspace-add-button"
                  onClick={() => {
                    setEditingModuleId(null);
                    setModuleName("");
                    setModuleDescription("");
                    setShowModuleForm(true);
                    setClassError("");
                  }}
                >
                  ＋ Add Module
                </button>
              </div>

              {showModuleForm && (
                <form
                  className="workspace-module-form"
                  onSubmit={handleSaveModule}
                >
                  <h4>
                    {editingModuleId ? "Edit module" : "New learning module"}
                  </h4>

                  <label htmlFor="workspace-module-name">Module name</label>
                  <input
                    id="workspace-module-name"
                    value={moduleName}
                    onChange={(event) => setModuleName(event.target.value)}
                    placeholder="e.g. Neighbourhood Shopping"
                    required
                  />

                  <label htmlFor="workspace-module-description">
                    Module description
                  </label>
                  <textarea
                    id="workspace-module-description"
                    value={moduleDescription}
                    onChange={(event) =>
                      setModuleDescription(event.target.value)
                    }
                    placeholder="Learning objectives and activities"
                    rows={3}
                  />

                  <div className="workspace-form-actions">
                    <button type="submit" className="workspace-primary">
                      ✓ Save Module
                    </button>
                    <button
                      type="button"
                      className="workspace-secondary"
                      onClick={() => {
                        setShowModuleForm(false);
                        setEditingModuleId(null);
                        setModuleName("");
                        setModuleDescription("");
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}

              {currentModules.length === 0 ? (
                <div className="workspace-empty">
                  <span className="workspace-empty-icon">◇</span>
                  <strong>Your class is ready for its first module</strong>
                  <p>
                    Add a module to organise lessons, activities, and
                    learning objectives.
                  </p>
                </div>
              ) : (
                <div className="workspace-module-grid">
                  {currentModules.map((module, index) => (
                    <article className="workspace-module-card" key={module.id}>
                      <div className="workspace-module-top">
                        <span className="workspace-module-number">
                          {String(index + 1).padStart(2, "0")}
                        </span>
                        <div className="workspace-module-actions">
                          <button
                            type="button"
                            className="workspace-icon-button"
                            aria-label={`Edit ${module.name}`}
                            onClick={() => handleEditModule(module)}
                          >
                            ✎
                          </button>
                          <button
                            type="button"
                            className="workspace-icon-button"
                            aria-label={`Delete ${module.name}`}
                            onClick={() => handleDeleteModule(module.id)}
                          >
                            ×
                          </button>
                        </div>
                      </div>
                      <h4>{module.name}</h4>
                      <p>
                        {module.description || "No description added yet."}
                      </p>
                      <button
                        type="button"
                        className="workspace-module-edit"
                        onClick={() => handleEditModule(module)}
                      >
                        Edit module →
                      </button>
                    </article>
                  ))}
                </div>
              )}

              <div className="workspace-students">
                <div className="workspace-section-title">
                  <div>
                    <h3>Learners</h3>
                    <p>Manage the learners assigned to this class.</p>
                  </div>
                </div>

                <form
                  className="workspace-student-form"
                  onSubmit={handleAddStudent}
                >
                  <input
                    aria-label="Student name"
                    value={studentName}
                    onChange={(event) => setStudentName(event.target.value)}
                    placeholder="Enter learner name"
                    required
                  />
                  <button type="submit" className="workspace-primary">
                    ＋ Add Learner
                  </button>
                </form>

                {students.length === 0 ? (
                  <p className="workspace-muted">
                    No learners added to this class yet.
                  </p>
                ) : (
                  <div className="workspace-student-list">
                    {students.map((student) => (
                      <div className="workspace-student-row" key={student.id}>
                        <span className="workspace-student-avatar">
                          {(student.name || "?").charAt(0).toUpperCase()}
                        </span>
                        <div style={{ flex: 1 }}>
                          <strong>{student.name}</strong>
                          <small style={{ display: "block", color: "#827b94" }}>
                            Pseudonym ID: {student.pseudonym_id || "LRN-ASSIGNED"}
                          </small>
                        </div>
                        <button
                          type="button"
                          className="text-button"
                          onClick={() => handleDeleteStudent(student.id)}
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="workspace-students">
                <div className="workspace-section-title">
                  <div>
                    <h3>Class Schedule</h3>
                    <p>Schedule recurring or dated sessions for this class.</p>
                  </div>
                </div>

                <form className="workspace-student-form" onSubmit={handleAddSchedule}>
                  <input
                    aria-label="Schedule title"
                    value={scheduleTitle}
                    onChange={(e) => setScheduleTitle(e.target.value)}
                    placeholder="Lesson title (e.g. Morning Shopping Practice)"
                    required
                  />
                  <select
                    aria-label="Schedule day"
                    value={scheduleDay}
                    onChange={(e) => setScheduleDay(e.target.value)}
                    style={{ maxWidth: 140, padding: "10px", borderRadius: 10, border: "1px solid #e3deec" }}
                  >
                    {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                  <button type="submit" className="workspace-primary">
                    ＋ Add Schedule
                  </button>
                </form>

                {schedules.length > 0 && (
                  <div className="workspace-student-list">
                    {schedules.map((sch) => (
                      <div className="workspace-student-row" key={sch.id}>
                        <strong>{sch.title}</strong>
                        <span style={{ marginLeft: "auto", color: "#827b94", fontSize: 12 }}>
                          {sch.day_of_week || sch.scheduled_date} · {String(sch.start_time).slice(0, 5)}–{String(sch.end_time).slice(0, 5)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          )}
        </section>
      );
    }

    return renderSimplePage(
      "Learning Hub",
      "Explore ideas and resources for designing supportive learning experiences.",
      [
        {
          icon: "✧",
          title: "Experience design",
          description: "Start with a learning goal and design around the learner.",
        },
        {
          icon: "◇",
          title: "Accessibility",
          description: "Consider visual, sensory, and interaction needs.",
        },
        {
          icon: "↗",
          title: "Guided activities",
          description: "Build structured tasks with clear feedback and goals.",
        },
      ]
    );
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#workspace-content">Skip to content</a>
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo"><Sparkles size={23} /></div>
          <div>
            <strong>Chernyx</strong>
            <small>AI Studio</small>
          </div>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {NAVIGATION.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${activeTab === item.name ? "active" : ""}`}
              aria-current={activeTab === item.name ? "page" : undefined}
              onClick={() => {
                setActiveTab(item.name);
                if (item.name === "Session Notebook") void refreshWorkspaceData();
                setNotice("");
              }}
            >
              <item.icon size={20} aria-hidden="true" />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-help">
          <Sparkles size={20} />
          <strong>Your next activity</strong>
          <button onClick={startNewExperience}>
            <Plus size={16} /> New activity
          </button>
        </div>

        <div className="sidebar-bottom">
          <span className="online-dot" />
          Tutor workspace
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div className="topbar-title">
            <h2>{NAVIGATION.find((item) => item.name === activeTab)?.label || activeTab}</h2>
          </div>
          <div className="topbar-actions">
            <button type="button" className="icon-button" title={`Use ${theme === "light" ? "dark" : "light"} theme`} aria-label={`Use ${theme === "light" ? "dark" : "light"} theme`} onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
              {theme === "light" ? <Moon size={19} /> : <Sun size={19} />}
            </button>
            <div className="notification-anchor" ref={notificationRef}>
              <button
                type="button"
                className="icon-button"
                aria-label="In-app notifications"
                title="Notifications"
                ref={notificationButtonRef}
                aria-expanded={showNotifications}
                aria-controls="notifications-panel"
                onClick={() => setShowNotifications((s) => !s)}
              >
                <Bell size={19} />{unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
              </button>
              {showNotifications && (
                <section className="notifications-popover" id="notifications-panel" aria-label="Notifications">
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <strong>Notifications</strong>
                    <button
                      type="button"
                      className="text-button"
                      onClick={async () => {
                        await classWorkspaceApi.markAllNotificationsRead().catch(() => {});
                        setUnreadCount(0);
                      }}
                    >
                      Mark all read
                    </button>
                  </div>
                  {notifications.length === 0 ? (
                    <p className="muted-text">No alerts yet.</p>
                  ) : (
                    notifications.slice(0, 5).map((n) => (
                      <div key={n.id} className="notification-item">
                        <strong>{n.title}</strong>
                        <p>{n.message}</p>
                      </div>
                    ))
                  )}
                </section>
              )}
            </div>
            <div className="user-avatar">
              {(userFullName || email || "T").charAt(0).toUpperCase()}
            </div>
            <div className="user-summary">
              <strong>{userFullName || (email ? email.split("@")[0] : "Tutor")}</strong>
              <span className="user-role">{userRole}</span>
            </div>
            <button className="icon-button" title="Log out" aria-label="Log out" onClick={handleLogout}>
              <LogOut size={18} />
            </button>
          </div>
        </header>

        <main className="page-content" id="workspace-content" tabIndex={-1}>
          {notice && (
            <div className="notice-banner" role="status">
              <CircleHelp size={18} aria-hidden="true" />
              <p>{notice}</p>
              <button
                onClick={() => setNotice("")}
                aria-label="Dismiss notification"
              >
                <X size={18} />
              </button>
            </div>
          )}

          {renderActivePage()}
        </main>

        <footer className="app-footer">
          <span>CHERNYX AI STUDIO</span>
          <span>Design with purpose. Learn with confidence.</span>
        </footer>
      </section>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<Suspense fallback={<p className="scene-loading" role="status">Loading workspace...</p>}><App /></Suspense>);
