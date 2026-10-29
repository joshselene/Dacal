
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "./style.css";
import FourWallPreview from "./components/FourWallPreview";
import { classWorkspaceApi } from "./classWorkspaceApi.js";
const API_URL = "http://127.0.0.1:8000/api/v1/auth";

const INITIAL_PROJECTS = [
  {
    id: 1,
    title: "Introduction to Immersive Learning",
    category: "Social Skills",
    status: "In Progress",
    stage: "configure",
    prompt:
      "Create an immersive classroom where students can practise greeting others.",
    version: 2,
  },
  {
    id: 2,
    title: "Interactive Learning Environment",
    category: "Life Skills",
    status: "Draft",
    stage: "prompt",
    prompt: "",
    version: 1,
  },
];

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
  { name: "Overview", icon: "⌂" },
  { name: "My Experiences", icon: "▤" },
  { name: "Create Experience", icon: "＋" },
  { name: "Classes & Modules", icon: "▦" },
  { name: "Learning Hub", icon: "◇" },
];

function App() {
  // Authentication: login and signup live in this same file.
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authPage, setAuthPage] = useState("login");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [signupForm, setSignupForm] = useState({
    full_name: "",
    email: "",
    organisation_name: "",
    password: "",
    confirm_password: "",
  });
  const [signupError, setSignupError] = useState("");
  const [signupSuccess, setSignupSuccess] = useState("");
  const [signupLoading, setSignupLoading] = useState(false);

  // Workspace navigation
  const [activeTab, setActiveTab] = useState("Overview");
  const [projects, setProjects] = useState(INITIAL_PROJECTS);
  const [selectedId, setSelectedId] = useState(null);

  // Experience creation workflow
  const [stage, setStage] = useState("prompt");
  const [prompt, setPrompt] = useState("");
  const [experienceTitle, setExperienceTitle] = useState("");
  const [category, setCategory] = useState("Social Skills");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [customAnswers, setCustomAnswers] = useState({});
  const [concept, setConcept] = useState("guided");
  const [generationStarted, setGenerationStarted] = useState(false);

  const [configuration, setConfiguration] = useState({
    environment: "Classroom",
    duration: "5–10 minutes",
    guidance: "Step-by-step",
    visualStyle: "Soft 3D",
    accessibility: "Visual prompts",
    comfort: "Low stimulation",
  });

  const [versions, setVersions] = useState([]);
  const [notice, setNotice] = useState("");
  const [classes, setClasses] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState("");
  const [className, setClassName] = useState("");
  const [classDescription, setClassDescription] = useState("");
  const [studentName, setStudentName] = useState("");
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
  async function handleLogin(event) {
    event.preventDefault();
    setLoginError("");
    setIsLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/login`,
        { email: email.trim(), password },
        { withCredentials: true }
      );

      if (response.data.access_token) {
        sessionStorage.setItem("access_token", response.data.access_token);
        setIsLoggedIn(true);
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
          password: signupForm.password,
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
    setIsLoggedIn(false);
    setPassword("");
    setAuthPage("login");
  }

  function startNewExperience() {
    setSelectedId(null);
    setPrompt("");
    setExperienceTitle("");
    setCategory("Social Skills");
    setQuestionIndex(0);
    setAnswers({});
    setCustomAnswers({});
    setConcept("guided");
    setGenerationStarted(false);
    setStage("prompt");
    setNotice("");
    setActiveTab("Create Experience");
  }

  function openProject(project) {
    setSelectedId(project.id);
    setPrompt(project.prompt || "");
    setExperienceTitle(project.title);
    setCategory(project.category || "Social Skills");
    setStage(project.stage || "prompt");
    setGenerationStarted(project.stage === "generating");
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

  function saveDraft(nextStage = stage) {
    const title =
      experienceTitle.trim() ||
      prompt.trim().split(/[.!?\n]/)[0].slice(0, 55) ||
      "Untitled learning experience";

    if (!selectedId) {
      const newProject = {
        id: Date.now(),
        title,
        category,
        prompt,
        status: "Draft",
        stage: nextStage,
        version: 1,
      };

      setProjects((current) => [newProject, ...current]);
      setSelectedId(newProject.id);
      setExperienceTitle(title);
    } else {
      updateProject({
        title,
        category,
        prompt,
        stage: nextStage,
      });
    }

    return title;
  }

  function continueToQuestions(event) {
    event.preventDefault();
    if (!prompt.trim()) return;

    saveDraft("questions");
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

  function finishQuestions() {
    saveDraft("review");
    setStage("review");
    setNotice("");
  }

  function approveConcept() {
    saveDraft("generating");
    setGenerationStarted(true);
    updateProject({ status: "Generation queued", stage: "generating" });
    setStage("generating");
    setNotice("");
  }

  function markReadyToConfigure() {
    setStage("configure");
    setGenerationStarted(false);
    updateProject({ status: "Ready to configure", stage: "configure" });
    setNotice(
      "Demo state updated. Real scene generation is not connected yet."
    );
  }

  function saveConfiguration() {
    saveDraft("configure");
    updateProject({ status: "Configured", stage: "configure" });
    setNotice("Configuration saved in this prototype.");
  }

  function approveVersion() {
    const current = projects.find((project) => project.id === selectedId);
    const nextVersion = (current?.version || 1) + 1;

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
    setNotice(`Version ${nextVersion} approved in this prototype.`);
  }

  function duplicateProject(project) {
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

  function restoreVersion(version) {
    setConfiguration(version.snapshot);
    setNotice(
      `Version ${version.number} configuration restored in this prototype.`
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

  // Authentication screens share this file and switch using authPage.
  if (!isLoggedIn) {
    return (
      <main className="login-page">
        <section className="login-card">
          <div className="brand-logo">C</div>
          <p className="login-eyebrow">CHERNYX AI STUDIO</p>

          {authPage === "login" ? (
            <>
              <h1>Welcome back</h1>
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
              <h1>Create your account</h1>
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
    ];

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

              const allowed = {
                prompt: true,
                questions: !!prompt.trim(),
                review: !!prompt.trim(),
                generating: generationStarted || !!selectedId,
                configure: !!selectedId,
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

  function renderPromptStage() {
    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">STEP 01 · DESCRIBE</span>
          <h1>What would you like your learners to experience?</h1>
          <p>
            Start with your idea. Describe the skill, setting, or challenge.
            Your answers will help shape the proposed learning experience.
          </p>
        </div>

        <form className="prompt-panel" onSubmit={continueToQuestions}>
          <label htmlFor="experience-prompt">
            Describe your learning experience
          </label>
          <textarea
            id="experience-prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Example: Create a calm, interactive 3D classroom where learners can practise introducing themselves, greeting classmates, and taking turns in a conversation..."
            rows={7}
            required
          />

          <div className="prompt-meta">
            <span>Be as detailed or as simple as you like.</span>
            <span>{prompt.length} characters</span>
          </div>

          <div className="form-grid">
            <div>
              <label htmlFor="experience-title">Experience name (optional)</label>
              <input
                id="experience-title"
                value={experienceTitle}
                onChange={(event) => setExperienceTitle(event.target.value)}
                placeholder="e.g. Practising everyday conversations"
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

          <div className="prompt-footer">
            <span className="helper-note">Next: up to 20 guided questions</span>
            <button type="submit" className="primary-button">
              Continue to questions <span>→</span>
            </button>
          </div>
        </form>

        <div className="tip-panel">
          <span className="tip-icon">✦</span>
          <div>
            <strong>Not sure where to start?</strong>
            <p>
              Tell us what learners need to practise, what environment might
              help, and what a successful session would look like.
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
          <span className="eyebrow">STEP 02 · CLARIFY</span>
          <h1>Let’s shape your idea</h1>
          <p>
            These questions help define the experience. Answer what you can
            and skip anything you haven't decided yet.
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
              You can skip questions and review your choices later.
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
              Finish questions and review my idea
            </button>
          </section>
        </div>
      </>
    );
  }

  function renderReviewStage() {
    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">STEP 03 · REVIEW</span>
          <h1>Your idea, brought into focus</h1>
          <p>
            Review the brief and proposed direction before starting generation.
            You stay in control of what gets created.
          </p>
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
            <span className="eyebrow">PROPOSED DIRECTIONS</span>
            <h2>Choose a concept to develop</h2>
            <p>These are illustrative concepts for the frontend prototype.</p>
          </div>
        </div>

        <div className="concept-grid">
          <button
            className={`concept-card ${concept === "guided" ? "selected" : ""}`}
            onClick={() => setConcept("guided")}
          >
            <div className="concept-art art-guided">
              <span className="art-orb orb-one" />
              <span className="art-orb orb-two" />
              <span className="art-room">GUIDED SPACE</span>
            </div>
            <div className="concept-content">
              <div className="concept-title">
                <h3>Guided learning space</h3>
                <span>{concept === "guided" ? "✓ Selected" : "Select"}</span>
              </div>
              <p>
                A structured environment with clear steps, visual cues, and
                gentle feedback.
              </p>
              <div className="concept-tags">
                <span>Structured</span><span>Supportive</span>
              </div>
            </div>
          </button>

          <button
            className={`concept-card ${concept === "explore" ? "selected" : ""}`}
            onClick={() => setConcept("explore")}
          >
            <div className="concept-art art-explore">
              <span className="art-orb orb-three" />
              <span className="art-orb orb-four" />
              <span className="art-room">OPEN EXPLORATION</span>
            </div>
            <div className="concept-content">
              <div className="concept-title">
                <h3>Explore and discover</h3>
                <span>{concept === "explore" ? "✓ Selected" : "Select"}</span>
              </div>
              <p>
                A more open environment where learners explore objects and
                discover tasks.
              </p>
              <div className="concept-tags">
                <span>Exploration</span><span>Flexible</span>
              </div>
            </div>
          </button>
        </div>

        <div className="approval-banner">
          <div className="approval-mark">✓</div>
          <div>
            <strong>Review before generation</strong>
            <p>
              Generation should only begin after you approve the proposed
              direction.
            </p>
          </div>
          <button className="primary-button" onClick={approveConcept}>
            Approve & start generation →
          </button>
        </div>
      </>
    );
  }

  function renderGeneratingStage() {
    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">STEP 04 · GENERATE</span>
          <h1>Your experience is taking shape</h1>
          <p>
            This screen represents the background-generation stage. In the
            current prototype, the generation process is simulated.
          </p>
        </div>

        <section className="generation-card">
          <div className="generation-visual">
            <div className="generation-ring ring-one" />
            <div className="generation-ring ring-two" />
            <div className="generation-center">✦</div>
          </div>

          <span className="generation-status">
            {generationStarted ? "DEMO · GENERATION QUEUED" : "GENERATION"}
          </span>
          <h2>{experienceTitle || "Your learning experience"}</h2>
          <p>
            Your approved concept is ready for the next stage of the workflow.
            Real AI planning and 3D scene generation still need to be connected.
          </p>

          <div className="generation-tasks">
            <div><span className="task-check">✓</span><span>Learning brief prepared</span><span className="task-state">Ready</span></div>
            <div><span className="task-check">✓</span><span>Concept direction approved</span><span className="task-state">Approved</span></div>
            <div><span className="task-pending">3</span><span>Scene generation and validation</span><span className="task-state">Not connected</span></div>
          </div>

          <button className="primary-button" onClick={markReadyToConfigure}>
            Demo: mark ready to configure →
          </button>
          <p className="muted-text">
            This button simulates a completed job; it does not generate a real
            3D scene.
          </p>
        </section>
      </>
    );
  }

  function renderConfigureStage() {
    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">STEP 05 · CONFIGURE</span>
          <h1>Make this experience yours</h1>
          <p>
            Adjust the proposed environment and learning settings. These
            controls currently save local prototype state.
          </p>
        </div>

        <div className="configure-layout">
          <section className="configuration-panel content-card">
            <div className="section-heading">
              <div>
                <h3>Experience settings</h3>
                <p>Adapt the experience to your learners.</p>
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
            <FourWallPreview environment={configuration.environment} />
            <button
              className="secondary-button full-width"
              onClick={() => setStage("versions")}
            >
              Manage versions →
            </button>
          </aside>
        </div>
      </>
    );
  }

  function renderVersionsStage() {
    const currentProject = projects.find((project) => project.id === selectedId);

    return (
      <>
        <div className="studio-intro">
          <span className="eyebrow">STEP 06 · VERSIONS</span>
          <h1>Keep track of every iteration</h1>
          <p>
            Approve a version, restore a previous configuration, or duplicate
            an experience to try a different direction.
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
          <button className="primary-button" onClick={approveVersion}>
            ✓ Approve current version
          </button>
        </section>

        <section className="content-card">
          <div className="section-heading">
            <div>
              <h3>Version history</h3>
              <p>Approved snapshots created in this session.</p>
            </div>
          </div>

          {versions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">▤</div>
              <h3>No approved versions yet</h3>
              <p>Save an approved snapshot to start tracking changes.</p>
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
                  <span className="status-pill">{version.status}</span>
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

  function renderOverview() {
    return (
      <>
        <section className="dashboard-hero">
          <div className="hero-copy">
            <span className="eyebrow">YOUR CREATIVE WORKSPACE</span>
            <h1>Learning experiences, <span>reimagined.</span></h1>
            <p>
              Turn your teaching ideas into structured immersive learning
              experiences, one step at a time.
            </p>
            <button
              className="primary-button hero-button"
              onClick={startNewExperience}
            >
              <span>＋</span> Create an experience
            </button>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="hero-art-orbit orbit-a" />
            <div className="hero-art-orbit orbit-b" />
            <div className="hero-art-core">✦</div>
            <span className="hero-art-label">IMAGINE · DESIGN · LEARN</span>
          </div>
        </section>

        <section className="stats-grid">
          <article className="stat-card">
            <div className="stat-icon purple">▤</div>
            <span>Total experiences</span>
            <strong>{statusCounts.total}</strong>
            <small>Your workspace projects</small>
          </article>
          <article className="stat-card">
            <div className="stat-icon blue">◷</div>
            <span>In progress</span>
            <strong>{statusCounts.active}</strong>
            <small>Experiences being developed</small>
          </article>
          <article className="stat-card">
            <div className="stat-icon peach">✎</div>
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
            {projects.slice(0, 4).map((project, index) => (
              <article className="experience-row" key={project.id}>
                <div className={`experience-icon experience-icon-${index % 4}`}>
                  {["✦", "◇", "▧", "✎"][index % 4]}
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
            <h3>My experiences</h3>
            <p>Manage your ideas, concepts, and configured experiences.</p>
          </div>
          <button className="primary-button" onClick={startNewExperience}>
            ＋ New experience
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
                  {["✦", "◇", "▧", "✎"][index % 4]}
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

        const studentData =
          await classWorkspaceApi.listStudents(id);
        setStudents(studentData);
      } else {
        setSelectedClassId("");
        setStudents([]);
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
      const created = await classWorkspaceApi.createClass({
        name: className.trim(),
        description: classDescription.trim() || null,
      });

      setClasses((previous) => [created, ...previous]);
      setSelectedClassId(created.id);
      setClassName("");
      setClassDescription("");
      setStudents([]);
      setEditingClass(false);
      setNotice("Class saved successfully.");
    } catch (error) {
      setClassError(error.message || "Unable to save class.");
    }
  }

  async function handleSelectClass(id) {
    setSelectedClassId(id);
    setEditingClass(false);
    setClassError("");

    try {
      const data = await classWorkspaceApi.listStudents(id);
      setStudents(data);
    } catch (error) {
      setStudents([]);
      setClassError(error.message || "Unable to load students.");
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
      setNotice("Student added successfully.");
    } catch (error) {
      setClassError(error.message || "Unable to add student.");
    }
  }

  function handleSaveModule(event) {
    event.preventDefault();

    if (!selectedClassId || !moduleName.trim()) {
      setClassError("Enter a module name first.");
      return;
    }

    const module = {
      id: editingModuleId || crypto.randomUUID(),
      name: moduleName.trim(),
      description: moduleDescription.trim(),
    };

    const updatedModules = editingModuleId
      ? currentModules.map((item) =>
          item.id === editingModuleId ? module : item
        )
      : [...currentModules, module];

    saveModules(updatedModules);
    setModuleName("");
    setModuleDescription("");
    setEditingModuleId(null);
    setShowModuleForm(false);
    setNotice("Module saved in this browser.");
    setClassError("");
  }

  function handleEditModule(module) {
    setEditingModuleId(module.id);
    setModuleName(module.name);
    setModuleDescription(module.description || "");
    setShowModuleForm(true);
    setClassError("");
  }

  function handleDeleteModule(id) {
    if (!window.confirm("Delete this module?")) return;

    saveModules(currentModules.filter((item) => item.id !== id));
    setNotice("Module removed.");
  }

  return (
    <section className="workspace-page">
      <div className="workspace-hero">
        <div>
          <span className="workspace-eyebrow">TEACHING WORKSPACE</span>
          <h2>Classes & Modules</h2>
          <p>
            Organise your classes, build learning modules, and manage
            your students in one place.
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
          <span>Students in selected class</span>
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
              placeholder="e.g. Grade 5 Mathematics"
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

            <button
              type="submit"
              className="workspace-primary"
              disabled={classLoading}
            >
              {classLoading ? "Saving..." : "＋ Save Class"}
            </button>
          </form>
        </section>

        <section className="workspace-panel">
          <div className="workspace-panel-heading">
            <div>
              <span className="workspace-eyebrow">YOUR WORKSPACE</span>
              <h3>Saved classes</h3>
              <p>Select a class to manage its modules and students.</p>
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

            <button
              type="button"
              className="workspace-secondary"
              onClick={() => {
                setClassName(currentClass.name || "");
                setClassDescription(currentClass.description || "");
                setEditingClass(true);
                setClassError(
                  "Editing an existing class requires an update-class API endpoint. Your changes have not been saved."
                );
              }}
            >
              ✎ Edit class
            </button>
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
                placeholder="e.g. Introduction to fractions"
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

          <div className="workspace-save-footer">
            <div>
              <strong>{currentModules.length} learning modules</strong>
              <p>Modules are currently stored in this browser only.</p>
            </div>
            <button
              type="button"
              className="workspace-primary"
              onClick={() => {
                setClassError(
                  "Your modules are saved in this browser. Connect the backend module endpoints to save them to the database."
                );
              }}
            >
              ✓ Save Class & Modules
            </button>
          </div>

          <div className="workspace-students">
            <div className="workspace-section-title">
              <div>
                <h3>Students</h3>
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
                placeholder="Enter student name"
                required
              />
              <button type="submit" className="workspace-primary">
                ＋ Add Student
              </button>
            </form>

            {students.length === 0 ? (
              <p className="workspace-muted">
                No students added to this class yet.
              </p>
            ) : (
              <div className="workspace-student-list">
                {students.map((student) => (
                  <div className="workspace-student-row" key={student.id}>
                    <span className="workspace-student-avatar">
                      {(student.name || "?").charAt(0).toUpperCase()}
                    </span>
                    <strong>{student.name}</strong>
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
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">C</div>
          <div>
            <strong>Chernyx</strong>
            <small>AI Studio</small>
          </div>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>
        <nav className="sidebar-nav">
          {NAVIGATION.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${activeTab === item.name ? "active" : ""}`}
              onClick={() => {
                setActiveTab(item.name);
                setNotice("");
              }}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.name}
              {item.name === "Create Experience" && (
                <span className="nav-plus">+</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-help">
          <div className="help-sparkle">✦</div>
          <strong>Have an idea?</strong>
          <p>Start with a simple description. Refine it as you go.</p>
          <button onClick={startNewExperience}>
            Create an experience →
          </button>
        </div>

        <div className="sidebar-bottom">
          <span className="online-dot" />
          Prototype workspace
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div className="topbar-title">
            <span className="breadcrumb">Chernyx / Workspace</span>
            <h2>{activeTab}</h2>
          </div>
          <div className="topbar-actions">
            <span className="environment-label">
              <span className="online-dot" /> Development
            </span>
            <div className="user-avatar">
              {email ? email.charAt(0).toUpperCase() : "T"}
            </div>
            <div className="user-summary">
              <strong>{email ? email.split("@")[0] : "Tutor"}</strong>
              <span>Tutor workspace</span>
            </div>
            <button className="logout-button" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </header>

        <div className="page-content">
          {notice && (
            <div className="notice-banner">
              <span>✓</span>
              <p>{notice}</p>
              <button
                onClick={() => setNotice("")}
                aria-label="Dismiss notification"
              >
                ×
              </button>
            </div>
          )}

          {renderActivePage()}
        </div>

        <footer className="app-footer">
          <span>CHERNYX AI STUDIO</span>
          <span>Design with purpose. Learn with confidence.</span>
        </footer>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
