const main = document.querySelector("#main");
const topbarAction = document.querySelector("#topbar-action");
const toast = document.querySelector("#toast");

const SKILLS = ["Python 기초", "API·데이터 처리", "Git·GitHub", "LLM·AI Agent 활용", "코드 이해·오류 분석"];
const INTERESTS = ["Python", "HTML/CSS", "Git/GitHub", "JavaScript", "FastAPI", "LLM API", "RAG", "AI Agent"];
const state = { user: null, questions: [], assessmentId: null, answers: {}, assessmentResult: null, profile: null, plan: null, progress: null, progressView: "dashboard", selectedWeek: 1, selectedTask: null, taskDetail: null, progressStats: null, activityRows: [], coachFeedback: null, githubAnalyses: [], githubResult: null };

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof body.detail === "string"
      ? body.detail
      : body.detail?.errors?.join(" ") || body.detail?.message || "요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.";
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return body;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function setError(id, message) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = message;
    element.classList.add("show");
  } else showToast(message);
}

function setLoading(label = "불러오는 중...") {
  main.innerHTML = `<div class="loading"><div><div class="spinner"></div><p>${escapeHtml(label)}</p></div></div>`;
}

function setHeader(action = "") {
  topbarAction.innerHTML = action;
}

function renderAuth(mode = "signup", error = "") {
  const login = mode === "login";
  setHeader(`<button class="account-link" id="switch-auth">${login ? "계정 만들기" : "로그인"}</button>`);
  main.innerHTML = `
    <section class="narrow">
      <div class="center">
        <div class="eyebrow">나만의 AI 개발 학습 코치</div>
        <h1>${login ? "다시 만나 반가워요" : "나만의 학습을 시작해요"}</h1>
        <p class="subtitle">${login ? "계정에 로그인하고 이어서 학습하세요." : "실력을 진단하고 목표에 맞는 학습 경로를 만들어 보세요."}</p>
      </div>
      <form id="auth-form" class="card form-grid">
        <div id="auth-error" class="error ${error ? "show" : ""}">${escapeHtml(error)}</div>
        <div class="field"><label for="email">이메일 주소</label><input id="email" name="email" type="email" autocomplete="email" placeholder="you@example.com" required maxlength="254" /></div>
        <div class="field"><label for="password">비밀번호</label><input id="password" name="password" type="password" autocomplete="${login ? "current-password" : "new-password"}" placeholder="8자 이상 입력" required minlength="8" maxlength="128" /></div>
        ${login ? "" : `
          <div class="field"><label class="check-row"><input type="checkbox" name="terms_agreed" required /><span>서비스 이용약관에 동의합니다. (필수)</span></label></div>
          <div class="field"><label class="check-row"><input type="checkbox" name="privacy_agreed" required /><span>개인정보 수집·이용에 동의합니다. (필수)</span></label></div>
          <p class="hint">가입 시 이메일 인증은 아직 연결되어 있지 않습니다. 계정은 이 서비스에서 안전하게 관리됩니다.</p>
        `}
        <button class="btn full" type="submit">${login ? "로그인" : "회원가입하고 계속하기"}</button>
      </form>
      <p class="center tiny muted" style="margin-top:18px">진단 결과는 학습 추천을 위한 참고 정보이며, 공인된 기술 인증이 아닙니다.</p>
    </section>`;
  document.querySelector("#switch-auth").addEventListener("click", () => renderAuth(login ? "signup" : "login"));
  document.querySelector("#auth-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const button = event.currentTarget.querySelector("button[type=submit]");
    button.disabled = true;
    try {
      const payload = { email: form.get("email"), password: form.get("password") };
      if (!login) {
        payload.terms_agreed = form.has("terms_agreed");
        payload.privacy_agreed = form.has("privacy_agreed");
      }
      state.user = await api(`/api/auth/${login ? "login" : "signup"}`, { method: "POST", body: JSON.stringify(payload) });
      await continueUser();
    } catch (err) {
      button.disabled = false;
      setError("auth-error", err.message);
    }
  });
}

async function continueUser() {
  state.user = await api("/api/auth/me");
  if (!state.user.profile_completed) return renderProfile();
  state.profile = await api("/api/profiles/me");
  if (!state.user.assessment_completed) return renderAssessmentIntro();
  state.assessmentResult = await api("/api/assessments/latest");
  try {
    state.plan = await api("/api/plans/current");
    return renderDashboard();
  } catch (err) {
    if (err.status === 404) return renderResults();
    throw err;
  }
}

async function logout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
  } catch (err) {
    showToast(err.message);
    return;
  }
  state.user = null;
  state.questions = [];
  state.assessmentId = null;
  state.answers = {};
  state.assessmentResult = null;
  state.profile = null;
  state.plan = null;
  state.progress = null;
  state.selectedWeek = 1;
  state.selectedTask = null;
  state.taskDetail = null;
  state.progressStats = null;
  state.activityRows = [];
  state.coachFeedback = null;
  renderAuth("login");
}

function renderProfile(profile = null, editable = false) {
  state.profile = profile;
  setHeader(`<span class="pill">${editable ? "프로필 수정" : "STEP 2 / 3"}</span>`);
  const interest = profile?.interest_skills || ["Python"];
  const duration = profile?.duration_weeks || 4;
  main.innerHTML = `
    <section class="narrow">
      <div class="step-meta"><span>학습자 프로필</span><span>${editable ? "수정" : "2 / 3"}</span></div>
      <div class="progress-track"><div class="progress-fill" style="width:${editable ? 100 : 34}%"></div></div>
      <h1>어떤 개발자가 되고 싶나요?</h1>
      <p class="subtitle">목표와 현재 경험을 알려주시면 나에게 맞는 진단과 학습계획을 준비할게요.</p>
      <form id="profile-form" class="card form-grid">
        <div id="profile-error" class="error"></div>
        <div class="field"><label for="nickname">닉네임 <span class="muted">*</span></label><input id="nickname" name="nickname" required maxlength="50" value="${escapeHtml(profile?.nickname || "")}" placeholder="화면에 표시할 이름" /></div>
        <div class="field"><label for="goal">학습 목표 <span class="muted">*</span></label><select id="goal" name="learning_goal">
          ${["AI Agent 웹서비스 개발", "Python 백엔드 개발", "데이터 분석 자동화", "웹 프론트엔드 개발", "나만의 프로젝트 완성"].map((goal) => `<option ${profile?.learning_goal === goal ? "selected" : ""}>${goal}</option>`).join("")}
        </select></div>
        <fieldset class="field" style="border:0;padding:0;margin:0"><legend class="field-label">현재 개발 경험 <span class="muted">*</span></legend>
          ${[["beginner", "입문 — 처음 배우거나 간단한 실습 경험"], ["novice", "초급 — 작은 프로그램이나 프로젝트 구현 경험"], ["intermediate", "중급 이상 — API·배포 경험 보유"]].map(([value, label]) => `<label class="radio-row"><input type="radio" name="self_assessed_level" value="${value}" ${profile?.self_assessed_level === value || (!profile && value === "beginner") ? "checked" : ""} required /><span>${label}</span></label>`).join("")}
        </fieldset>
        <fieldset class="field" style="border:0;padding:0;margin:0"><legend class="field-label">관심 기술 (복수 선택)</legend>
          <div class="tag-list">${INTERESTS.map((item) => `<label class="tag-option"><input type="checkbox" name="interest_skills" value="${item}" ${interest.includes(item) ? "checked" : ""} /><span>${item}</span></label>`).join("")}</div>
        </fieldset>
        <div class="field"><label for="weekly">주당 학습 가능 시간 <strong id="hours-value">${profile?.weekly_hours || 8}시간</strong></label><input id="weekly" name="weekly_hours" type="range" min="2" max="40" value="${profile?.weekly_hours || 8}" /><div class="step-meta"><span>2시간</span><span>40시간</span></div></div>
        <div class="field"><span class="field-label">목표 학습 기간 <span class="muted">*</span></span><div class="choice-grid">${[4, 8, 12].map((weeks) => `<label class="answer-option"><input type="radio" name="duration_weeks" value="${weeks}" ${duration === weeks ? "checked" : ""} /><span>${weeks}주</span></label>`).join("")}</div></div>
        <div class="field"><label for="github">GitHub 사용자명 <span class="muted">(선택)</span></label><input id="github" name="github_username" value="${escapeHtml(profile?.github_username || "")}" maxlength="100" placeholder="예: my-github-id" /></div>
        <div class="field"><label for="notes">추가 학습 요청사항 <span class="muted">(선택)</span></label><textarea id="notes" name="learning_notes" maxlength="1000" placeholder="예: API 연동은 어렵고, 주말에 주로 학습합니다.">${escapeHtml(profile?.learning_notes || "")}</textarea></div>
        <button class="btn full" type="submit">${editable ? "프로필 저장" : "프로필 등록하고 진단 시작"}</button>
      </form>
    </section>`;
  document.querySelector("#weekly").addEventListener("input", (event) => {
    document.querySelector("#hours-value").textContent = `${event.target.value}시간`;
  });
  document.querySelector("#profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const button = event.currentTarget.querySelector("button[type=submit]");
    button.disabled = true;
    const payload = {
      nickname: form.get("nickname"),
      learning_goal: form.get("learning_goal"),
      self_assessed_level: form.get("self_assessed_level"),
      interest_skills: form.getAll("interest_skills"),
      weekly_hours: Number(form.get("weekly_hours")),
      duration_weeks: Number(form.get("duration_weeks")),
      github_username: form.get("github_username"),
      learning_notes: form.get("learning_notes"),
    };
    try {
      state.profile = await api(editable ? "/api/profiles/me" : "/api/profiles", { method: editable ? "PATCH" : "POST", body: JSON.stringify(payload) });
      if (editable) {
        showToast("학습 프로필을 저장했습니다.");
        await continueUser();
      } else renderAssessmentIntro();
    } catch (err) {
      button.disabled = false;
      setError("profile-error", err.message);
    }
  });
}

function renderAssessmentIntro() {
  const hasPlan = Boolean(state.plan);
  setHeader(hasPlan
    ? `<div><button class="account-link" id="show-results">진단 결과</button> <button class="account-link" id="show-dashboard">학습 현황</button> <button class="account-link" id="logout-action">로그아웃</button></div>`
    : `<span class="pill">STEP 3 / 3</span>`);
  main.innerHTML = `
    <section class="narrow">
      <div class="center"><div class="eyebrow">현재 역량을 확인해요</div><h1>AI 개발 역량 진단</h1><p class="subtitle">결과를 바탕으로 나에게 맞는 학습 경로를 설계합니다.</p></div>
      <div class="card">
        <div class="stats"><div class="stat"><strong>22문항</strong><span>진단 문제</span></div><div class="stat"><strong>약 30분</strong><span>예상 시간</span></div><div class="stat"><strong>5개</strong><span>평가 영역</span></div></div>
        <h3>평가 영역</h3><div class="tag-list">${SKILLS.map((skill) => `<span class="pill">${skill}</span>`).join("")}</div>
        <div class="notice">객관식 20문항과 코드 이해·오류 분석 서술형 2문항으로 구성됩니다. 답안은 자동 저장되어 나중에 이어 풀 수 있습니다.</div>
        <p class="tiny muted">객관식은 정답 기준으로 채점하고, 서술형 답변은 OpenAI에 전송해 평가 기준에 따라 AI가 의미를 평가합니다. OpenAI API 키가 없으면 서술형 답변을 채점할 수 없습니다. 진단 결과는 학습 추천용이며 공인된 자격이나 기술 인증을 의미하지 않습니다.</p>
        <div class="btn-row"><button class="btn secondary" id="edit-profile">프로필 확인</button><button class="btn" id="start-assessment">진단 시작 <span aria-hidden="true">→</span></button></div>
      </div>
    </section>`;
  document.querySelector("#edit-profile").addEventListener("click", async () => {
    try { renderProfile(await api("/api/profiles/me"), true); } catch (err) { showToast(err.message); }
  });
  document.querySelector("#show-results")?.addEventListener("click", openAssessmentResults);
  document.querySelector("#show-dashboard")?.addEventListener("click", renderDashboard);
  document.querySelector("#logout-action")?.addEventListener("click", logout);
  document.querySelector("#start-assessment").addEventListener("click", startAssessment);
}

async function startAssessment() {
  setLoading("진단 문항을 준비하고 있어요");
  try {
    const [session, questionData] = await Promise.all([
      api("/api/assessments/start", { method: "POST" }),
      api("/api/assessments/questions"),
    ]);
    state.assessmentId = session.id;
    state.answers = session.answers || {};
    state.questions = questionData.questions;
    renderQuestion(0);
  } catch (err) {
    renderAssessmentIntro();
    showToast(err.message);
  }
}

function renderQuestion(index) {
  const question = state.questions[index];
  const answered = Object.keys(state.answers).length;
  const progress = ((index + 1) / state.questions.length) * 100;
  setHeader(`<button class="account-link" id="save-exit">나중에 계속</button>`);
  main.innerHTML = `
    <section class="narrow">
      <div class="step-meta"><span>수준 진단</span><span>${index + 1} / ${state.questions.length} 문항</span></div>
      <div class="progress-track"><div class="progress-fill" style="width:${progress}%"></div></div>
      <div class="step-meta"><span>${escapeHtml(question.category)}</span><span>답변 ${answered} / ${state.questions.length}</span></div>
      <article class="card question-card">
        <span class="eyebrow">Q${index + 1} · ${question.type === "written" ? "코드 분석" : "객관식"}</span>
        <h2 style="margin-top:12px">${escapeHtml(question.prompt)}</h2>
        ${question.code ? `<pre class="code-block">${escapeHtml(question.code)}</pre>` : ""}
        <div id="answer-area"></div>
        <div id="answer-error" class="error" style="margin-top:12px"></div>
        <div class="btn-row">
          <button class="btn secondary" id="previous" ${index === 0 ? "disabled" : ""}>이전</button>
          ${index === state.questions.length - 1
            ? `<button class="btn" id="submit-assessment">답안 제출</button>`
            : `<button class="btn" id="next">다음 문제 <span aria-hidden="true">→</span></button>`}
        </div>
      </article>
    </section>`;
  const area = document.querySelector("#answer-area");
  const currentAnswer = state.answers[question.id] || "";
  if (question.type === "written") {
    area.innerHTML = `<div class="field"><label for="written-answer">답변</label><textarea id="written-answer" maxlength="5000" placeholder="문제 원인과 해결 방법을 설명해 주세요.">${escapeHtml(currentAnswer)}</textarea></div>`;
    document.querySelector("#written-answer").addEventListener("blur", () => saveCurrentAnswer(question));
  } else {
    area.innerHTML = `<div class="answer-list">${question.options.map((option) => `<label class="answer-option"><input type="radio" name="answer" value="${escapeHtml(option.id)}" ${currentAnswer === option.id ? "checked" : ""} /><span>${escapeHtml(option.text)}</span></label>`).join("")}</div>`;
    area.querySelectorAll("input").forEach((input) => input.addEventListener("change", () => saveCurrentAnswer(question)));
  }
  document.querySelector("#save-exit").addEventListener("click", renderAssessmentIntro);
  document.querySelector("#previous").addEventListener("click", () => renderQuestion(index - 1));
  if (index < state.questions.length - 1) {
    document.querySelector("#next").addEventListener("click", async () => {
      try {
        await saveCurrentAnswer(question);
        renderQuestion(index + 1);
      } catch (err) { setError("answer-error", err.message); }
    });
  } else {
    document.querySelector("#submit-assessment").addEventListener("click", async () => {
      try {
        await saveCurrentAnswer(question);
        const unanswered = state.questions.length - Object.keys(state.answers).length;
        if (unanswered && !window.confirm(`${unanswered}개 문항에 답하지 않았습니다. 답안이 없는 문항은 0점으로 제출할까요?`)) return;
        const result = await api(`/api/assessments/${state.assessmentId}/submit`, { method: "POST" });
        state.assessmentResult = { id: state.assessmentId, ...result };
        renderResults();
      } catch (err) { setError("answer-error", err.message); }
    });
  }
}

async function saveCurrentAnswer(question) {
  const answer = question.type === "written"
    ? document.querySelector("#written-answer")?.value || ""
    : document.querySelector('input[name="answer"]:checked')?.value || "";
  if (!answer && question.type === "objective") return;
  state.answers[question.id] = answer;
  await api(`/api/assessments/${state.assessmentId}/answers`, {
    method: "PATCH",
    body: JSON.stringify({ question_id: question.id, answer }),
  });
}

function renderResults() {
  const result = state.assessmentResult;
  const hasPlan = Boolean(state.plan);
  const hasApprovedPlan = state.plan?.status === "approved";
  setHeader(`<div>${hasPlan ? `<button class="account-link" id="assessment-intro-action">수준 진단</button> <button class="account-link" id="dashboard-action">학습 현황</button> ` : ""}<button class="account-link" id="profile-action">프로필</button> <button class="account-link" id="logout-action">로그아웃</button></div>`);
  main.innerHTML = `
    <section>
      <div class="eyebrow">AI DevCoach · 역량 진단 결과</div><h1>나의 다음 성장을 확인해요</h1>
      <div class="card">
        <div class="step-meta"><span>종합 진단 점수</span><span class="pill">${escapeHtml(result.level)}</span></div>
        <div class="result-score"><div class="score-ring" style="--score:${result.total_score}%"><strong>${result.total_score}</strong></div><div><h2>${result.level} 단계</h2><p class="muted" style="margin:0">${escapeHtml(result.feedback)}</p></div></div>
        <div class="notice">${escapeHtml(result.grading_method || "객관식은 정답 기준, 서술형은 OpenAI 루브릭 기반으로 채점했습니다.")}</div>
        <h3>영역별 역량 점수</h3>
        ${Object.entries(result.skill_scores).map(([skill, score]) => `<div class="skill-row"><header><span>${escapeHtml(skill)}</span><strong>${score}점</strong></header><div class="bar"><span style="width:${score}%"></span></div></div>`).join("")}
        <div class="notice"><strong>먼저 보완할 영역</strong><br />${(result.focus_areas || []).map(escapeHtml).join(" · ")}<br /><span class="tiny">강점 영역: ${(result.strengths || []).map(escapeHtml).join(" · ") || "진단 후속 학습으로 확인해 보세요."}</span></div>
        <div class="btn-row"><button class="btn secondary" id="retake">다시 진단</button><button class="btn" id="result-next">${hasApprovedPlan ? "학습 진도 보기" : state.plan ? "계획 검토" : "나만의 학습계획 만들기"} <span aria-hidden="true">→</span></button></div>
      </div>
    </section>`;
  document.querySelector("#profile-action").addEventListener("click", async () => {
    try { renderProfile(await api("/api/profiles/me"), true); } catch (err) { showToast(err.message); }
  });
  document.querySelector("#logout-action").addEventListener("click", logout);
  document.querySelector("#assessment-intro-action")?.addEventListener("click", renderAssessmentIntro);
  document.querySelector("#dashboard-action")?.addEventListener("click", renderDashboard);
  document.querySelector("#retake").addEventListener("click", renderAssessmentIntro);
  document.querySelector("#result-next").addEventListener("click", () => {
    if (hasApprovedPlan) renderDashboard();
    else if (state.plan) renderPlanReview();
    else renderPlanSetup();
  });
}

async function openAssessmentResults() {
  try {
    state.assessmentResult = await api("/api/assessments/latest");
    renderResults();
  } catch (err) {
    showToast(err.message);
  }
}

async function renderPlanSetup() {
  setLoading("프로필과 진단 결과를 불러오고 있어요");
  try {
    const context = await api("/api/plans/context");
    state.profile = context.profile;
    state.assessmentResult = { id: context.assessment_id, ...context.assessment };
  } catch (err) {
    renderResults();
    showToast(err.message);
    return;
  }
  const profile = state.profile;
  const result = state.assessmentResult;
  const selected = result.focus_areas?.length ? result.focus_areas : [];
  setHeader(`<span class="pill">FR-03 학습계획</span>`);
  main.innerHTML = `
    <section class="narrow">
      <div class="eyebrow">진단 결과를 바탕으로 설계합니다</div><h1>나만의 학습계획 만들기</h1><p class="subtitle">진단 결과와 목표를 확인하고 학습 조건을 설정해 주세요.</p>
      <div class="card">
        <div class="step-meta"><span>나의 진단 결과</span><span class="pill">${escapeHtml(result.level)}</span></div>
        <p style="font-size:24px;font-weight:700;margin:10px 0">${result.total_score}<span class="muted" style="font-size:14px"> / 100점</span></p>
        <p class="tiny muted">${Object.entries(result.skill_scores).map(([skill, score]) => `${escapeHtml(skill)} ${score}점`).join("　·　")}</p>
      </div>
      <form id="plan-form" class="card form-grid">
        <div id="plan-error" class="error"></div>
        <div class="field"><label for="plan-goal">학습 목표 *</label><input id="plan-goal" name="goal" required maxlength="100" value="${escapeHtml(profile.learning_goal)}" /></div>
        <div class="field"><span class="field-label">학습 기간 *</span><div class="choice-grid">${[4, 8, 12].map((weeks) => `<label class="answer-option"><input type="radio" name="duration_weeks" value="${weeks}" ${profile.duration_weeks === weeks ? "checked" : ""} /><span>${weeks}주</span></label>`).join("")}</div></div>
        <div class="field"><label for="plan-hours">주당 학습 가능 시간 <strong id="plan-hours-value">${profile.weekly_hours}시간</strong></label><input id="plan-hours" name="weekly_hours" type="range" min="2" max="40" value="${profile.weekly_hours}" /><div class="step-meta"><span>2시간</span><span>40시간</span></div></div>
        <fieldset class="field" style="border:0;padding:0;margin:0"><legend class="field-label">우선 보완 기술 (선택)</legend><div class="tag-list">${SKILLS.map((skill) => `<label class="tag-option"><input type="checkbox" name="focus_skills" value="${skill}" ${selected.includes(skill) ? "checked" : ""} /><span>${skill}</span></label>`).join("")}</div></fieldset>
        <div class="field"><label for="difficulty">학습 난이도</label><select id="difficulty" name="difficulty"><option value="foundation">기초 중심 — 개념과 작은 실습 위주</option><option value="balanced" selected>균형형 — 개념 학습과 실습 병행</option><option value="challenge">도전형 — 프로젝트와 문제 해결 중심</option></select></div>
        <fieldset class="field" style="border:0;padding:0;margin:0"><legend class="field-label">선호 학습 방식</legend>
          <label class="radio-row"><input type="radio" name="learning_style" value="project" checked /><span>프로젝트 기반 실습</span></label>
          <label class="radio-row"><input type="radio" name="learning_style" value="examples" /><span>예제 따라 하기</span></label>
          <label class="radio-row"><input type="radio" name="learning_style" value="self_paced" /><span>자기주도 탐구</span></label>
        </fieldset>
        <div class="field"><label for="requirements">추가 요청사항 <span class="muted">(선택)</span></label><textarea id="requirements" name="additional_requirements" maxlength="500" placeholder="예: GitHub는 처음이므로 기초부터 학습하고 싶습니다.">${escapeHtml(profile.learning_notes || "")}</textarea></div>
        <div id="plan-total" class="notice"></div>
        <button class="btn full" type="submit">✧ 샘플 학습계획 생성</button>
        <p class="tiny muted">계획은 프로필과 진단 점수를 반영한 규칙 기반 초안입니다. 실제 AI 호출이 아니며 승인 전 검토·수정할 수 있습니다.</p>
      </form>
    </section>`;
  const updateTotal = () => {
    const hours = Number(document.querySelector("#plan-hours").value);
    const weeks = Number(document.querySelector('input[name="duration_weeks"]:checked').value);
    document.querySelector("#plan-hours-value").textContent = `${hours}시간`;
    document.querySelector("#plan-total").innerHTML = `<strong>계획 학습 가능 시간</strong><br />${weeks * hours}시간 <span class="tiny">(${weeks}주 × 주 ${hours}시간)</span>`;
  };
  document.querySelector("#plan-hours").addEventListener("input", updateTotal);
  document.querySelectorAll('input[name="duration_weeks"]').forEach((input) => input.addEventListener("change", updateTotal));
  updateTotal();
  document.querySelector("#plan-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const button = event.currentTarget.querySelector("button[type=submit]");
    button.disabled = true;
    button.textContent = "계획을 구성하고 검증하고 있어요...";
    try {
      state.plan = await api("/api/plans/generate", {
        method: "POST",
        body: JSON.stringify({
          goal: form.get("goal"),
          duration_weeks: Number(form.get("duration_weeks")),
          weekly_hours: Number(form.get("weekly_hours")),
          difficulty: form.get("difficulty"),
          learning_style: form.get("learning_style"),
          focus_skills: form.getAll("focus_skills"),
          additional_requirements: form.get("additional_requirements"),
        }),
      });
      renderPlanReview();
    } catch (err) {
      button.disabled = false;
      button.textContent = "✧ 샘플 학습계획 생성";
      setError("plan-error", err.message);
    }
  });
}

function renderPlanReview() {
  const plan = state.plan;
  setHeader(`<span class="pill">${plan.status === "approved" ? "확정된 계획" : "계획 검토 중"}</span>`);
  main.innerHTML = `
    <section>
      <div class="eyebrow">개인별 계획 초안 · v${plan.version}</div><h1>주차별 계획을 검토해요</h1>
      <p class="subtitle">${escapeHtml(plan.goal)} · ${plan.duration_weeks}주 · 주 ${plan.weekly_hours}시간</p>
      <div class="notice">${escapeHtml(plan.difficulty_note)} 우선 보완: ${plan.focus_skills.map(escapeHtml).join(" · ")}</div>
      <div id="plan-review-error" class="error"></div>
      <div id="weeks">${plan.weeks.map((week, wi) => `
        <article class="week">
          <header class="week-summary"><div><span class="pill">WEEK ${week.week_no}</span><p>${escapeHtml(week.weekly_goal)}</p></div><span class="tiny muted">${week.tasks.reduce((sum, task) => sum + Number(task.estimated_hours), 0)} / ${plan.weekly_hours}시간</span></header>
          ${week.tasks.map((task, ti) => `
            <div class="task">
              <div class="task-top"><strong>${ti + 1}. ${escapeHtml(task.title)}</strong><span class="pill">${escapeHtml(task.priority)} priority</span></div>
              <div class="task-fields">
                <div class="field"><label>과제명</label><input data-week="${wi}" data-task="${ti}" data-key="title" value="${escapeHtml(task.title)}" ${plan.status === "approved" ? "disabled" : ""} /></div>
                <div class="field"><label>예상 시간</label><input data-week="${wi}" data-task="${ti}" data-key="estimated_hours" type="number" min="1" max="${plan.weekly_hours}" value="${escapeHtml(task.estimated_hours)}" ${plan.status === "approved" ? "disabled" : ""} /></div>
              </div>
              <div class="task-fields">
                <div class="field"><label>결과물</label><input data-week="${wi}" data-task="${ti}" data-key="deliverable" value="${escapeHtml(task.deliverable)}" ${plan.status === "approved" ? "disabled" : ""} /></div>
                <div class="field"><label>완료 기준</label><input data-week="${wi}" data-task="${ti}" data-key="completion_criteria" value="${escapeHtml(task.completion_criteria)}" ${plan.status === "approved" ? "disabled" : ""} /></div>
              </div>
              <p class="tiny muted" style="margin:9px 0 0">학습 자료: ${task.learning_resources.map(escapeHtml).join(" · ")}</p>
            </div>`).join("")}
        </article>`).join("")}</div>
      <div class="card" style="margin-top:18px">
        <div class="step-meta"><span>시간·구조 검증</span><span id="validation-status" class="pill">확인 중</span></div>
        <p class="tiny muted" id="validation-message" style="margin:10px 0 0">모든 주차의 과제 시간과 필수 항목을 확인합니다.</p>
        <div class="btn-row">
          <button class="btn secondary" id="back-to-setup">조건 수정</button>
          ${plan.status === "approved" ? `<button class="btn" id="finish-plan">완료</button>` : `<button class="btn" id="save-plan">수정 저장</button><button class="btn" id="approve-plan">계획 승인</button>`}
        </div>
      </div>
    </section>`;
  document.querySelector("#back-to-setup").addEventListener("click", renderPlanSetup);
  if (plan.status === "approved") {
    document.querySelector("#finish-plan").addEventListener("click", renderDashboard);
  } else {
    document.querySelector("#save-plan").addEventListener("click", savePlanEdits);
    document.querySelector("#approve-plan").addEventListener("click", approvePlan);
  }
  validateCurrentPlan();
}

function readPlanEdits() {
  document.querySelectorAll("[data-week][data-task][data-key]").forEach((input) => {
    const week = state.plan.weeks[Number(input.dataset.week)];
    const task = week.tasks[Number(input.dataset.task)];
    task[input.dataset.key] = input.dataset.key === "estimated_hours" ? Number(input.value) : input.value;
  });
}

async function savePlanEdits() {
  readPlanEdits();
  try {
    state.plan = await api(`/api/plans/${state.plan.id}`, { method: "PATCH", body: JSON.stringify({ plan: state.plan }) });
    showToast("수정한 계획을 저장했습니다.");
    renderPlanReview();
  } catch (err) { setError("plan-review-error", err.message); }
}

async function validateCurrentPlan() {
  try {
    const result = await api(`/api/plans/${state.plan.id}/validate`, { method: "POST" });
    const status = document.querySelector("#validation-status");
    if (status) {
      status.textContent = result.valid ? "검증 통과" : "수정 필요";
      status.style.color = result.valid ? "var(--green)" : "var(--red)";
      document.querySelector("#validation-message").textContent = result.valid ? "주차별 과제, 필수 결과물 및 가용 학습 시간이 모두 확인되었습니다." : result.errors.join(" ");
      const approve = document.querySelector("#approve-plan");
      if (approve) approve.disabled = !result.valid;
    }
  } catch (err) { setError("plan-review-error", err.message); }
}

async function approvePlan() {
  readPlanEdits();
  try {
    const updated = await api(`/api/plans/${state.plan.id}`, { method: "PATCH", body: JSON.stringify({ plan: state.plan }) });
    state.plan = await api(`/api/plans/${updated.id}/approve`, { method: "POST" });
    showToast("학습계획을 확정했습니다.");
    renderPlanReview();
  } catch (err) { setError("plan-review-error", err.message); }
}

async function renderDashboard() {
  const plan = state.plan;
  if (plan?.status === "approved") return openProgressView("dashboard");
  setHeader(`<div>${plan ? `<button class="account-link" id="dashboard-assessment-intro">수준 진단</button> <button class="account-link" id="dashboard-assessment-results">진단 결과</button> ` : ""}<button class="account-link" id="logout-action">로그아웃</button></div>`);
  main.innerHTML = `
    <section>
      <div class="eyebrow">학습자 대시보드</div><h1>${escapeHtml(state.profile?.nickname || "학습자")}님, 좋은 학습을 시작해요</h1>
      <p class="subtitle">진단과 학습계획을 확인하고 다음 단계를 준비해 보세요.</p>
      <div class="stats"><div class="stat"><strong>${state.assessmentResult?.total_score ?? "—"}점</strong><span>최근 진단 결과</span></div><div class="stat"><strong>${plan?.duration_weeks ?? "—"}주</strong><span>학습계획</span></div><div class="stat"><strong>${plan?.weekly_hours ?? "—"}시간</strong><span>주당 학습 목표</span></div></div>
      ${plan ? `<div class="card"><div class="step-meta"><span>나의 학습계획</span><span class="pill">초안</span></div><h2 style="margin-top:14px">${escapeHtml(plan.goal)}</h2><p class="muted">총 ${plan.weeks.length}주 · 계획을 승인하면 과제별 진도 기록을 시작할 수 있습니다.</p><div class="btn-row"><button class="btn secondary" id="edit-profile">프로필 수정</button><button class="btn" id="review-plan">계획 다시 보기</button></div></div>` : `<div class="card"><h2>학습계획이 아직 없습니다</h2><p class="muted">진단 결과와 학습 목표에 맞춰 주차별 계획을 만들어 보세요.</p><button class="btn" id="create-plan">학습계획 만들기</button></div>`}
    </section>`;
  document.querySelector("#logout-action").addEventListener("click", logout);
  document.querySelector("#dashboard-assessment-intro")?.addEventListener("click", renderAssessmentIntro);
  document.querySelector("#dashboard-assessment-results")?.addEventListener("click", openAssessmentResults);
  document.querySelector("#edit-profile")?.addEventListener("click", async () => renderProfile(await api("/api/profiles/me"), true));
  document.querySelector("#review-plan")?.addEventListener("click", renderPlanReview);
  document.querySelector("#create-plan")?.addEventListener("click", renderPlanSetup);
}

function progressNavigation(activeView) {
  setHeader(`<nav class="progress-nav" aria-label="학습 메뉴">${[["dashboard", "대시보드"], ["tasks", "과제 관리"], ["history", "학습 통계"], ["coach", "학습 코칭"], ["github", "GitHub 분석"]].map(([view, label]) => `<button class="${view === activeView ? "active" : ""}" data-progress-view="${view}" aria-current="${view === activeView ? "page" : "false"}">${label}</button>`).join("")}<button class="account-link" id="assessment-intro">수준 진단</button><button class="account-link" id="assessment-results">진단 결과</button><button class="account-link" id="logout-action">로그아웃</button></nav>`);
  document.querySelectorAll("[data-progress-view]").forEach((button) => button.addEventListener("click", () => openProgressView(button.dataset.progressView)));
  document.querySelector("#assessment-intro").addEventListener("click", renderAssessmentIntro);
  document.querySelector("#assessment-results").addEventListener("click", openAssessmentResults);
  document.querySelector("#logout-action").addEventListener("click", logout);
}

async function openProgressView(view) {
  state.progressView = view;
  state.taskDetail = null;
  if (view === "github") {
    setLoading("GitHub 분석 이력을 불러오고 있어요");
    try {
      state.githubAnalyses = await api("/api/github/analyses");
      renderGithubAnalysis();
    } catch (err) {
      main.innerHTML = `<section class="narrow card center"><h2>GitHub 분석을 불러오지 못했습니다</h2><p class="muted">${escapeHtml(err.message)}</p><button id="retry-github" class="btn">다시 시도</button></section>`;
      document.querySelector("#retry-github").addEventListener("click", () => openProgressView("github"));
    }
    return;
  }
  setLoading("학습 진도를 불러오고 있어요");
  try {
    state.progress = await api("/api/progress/dashboard");
    if (view === "history") {
      [state.progressStats, state.activityRows] = await Promise.all([
        api("/api/progress/statistics"), api("/api/progress/activities"),
      ]);
    } else if (view === "coach") {
      state.coachFeedback = await api("/api/coach/progress-feedback", { method: "POST" });
    } else if (view === "tasks" && state.selectedTask) {
      state.taskDetail = await api(`/api/tasks/${encodeURIComponent(state.selectedTask)}`);
    }
    if (view === "tasks") return renderProgressTasks();
    if (view === "history") return renderProgressHistory();
    if (view === "coach") return renderProgressCoach();
    renderProgressDashboard();
  } catch (err) {
    main.innerHTML = `<section class="narrow card center"><h2>진도를 불러오지 못했습니다</h2><p class="muted">${escapeHtml(err.message)}</p><button id="retry-progress" class="btn">다시 시도</button></section>`;
    document.querySelector("#retry-progress").addEventListener("click", () => openProgressView(view));
  }
}

function renderGithubAnalysis() {
  progressNavigation("github");
  const result = state.githubResult;
  const history = state.githubAnalyses;
  const review = result?.review;
  const statusLabels = {
    fulfilled: "충족 가능", partially_fulfilled: "일부 충족", needs_review: "추가 검증 필요", cannot_assess: "확인 불가",
  };
  main.innerHTML = `
    <section class="progress-page github-page">
      <div class="eyebrow">프로젝트 증거 기반 분석</div><h1>GitHub 프로젝트 분석</h1>
      <p class="subtitle">공개 저장소의 구조, 문서, 최근 커밋을 확인합니다. 정적 분석은 실행 동작이나 과제 완료를 확정하지 않습니다.</p>
      <form id="github-analysis-form" class="github-form">
        <div id="github-analysis-error" class="error"></div>
        <div class="field"><label for="github-repo-url">GitHub 저장소 URL</label><input id="github-repo-url" name="repo_url" type="url" placeholder="https://github.com/owner/repository" required maxlength="500" /></div>
        <div class="form-columns">
          <div class="field"><label for="github-branch">Branch <span class="muted">(비우면 기본 Branch)</span></label><input id="github-branch" name="branch" maxlength="255" placeholder="main" /></div>
          <div class="field"><label for="github-task-criteria">연계 과제 완료 기준 <span class="muted">(선택)</span></label><input id="github-task-criteria" name="task_criteria" maxlength="2000" placeholder="예: GET·POST API 구현" /></div>
        </div>
        <button class="btn" type="submit">저장소 분석</button>
        <p class="tiny muted">MVP는 공개 저장소를 대상으로 합니다. 분석 시 README와 최대 3개의 핵심 소스 파일만 선택하며, 탐지된 비밀정보 포함 파일은 AI 입력에서 제외합니다.</p>
      </form>
      ${result ? `
        <section class="github-report" aria-live="polite">
          <div class="github-report-heading"><div><div class="eyebrow">${result.analysis_source === "openai" ? "AI 분석" : "규칙 기반 분석"}</div><h2><a href="${escapeHtml(result.repository.html_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(result.repository.full_name)}</a></h2><p class="muted">${escapeHtml(result.repository.description || "저장소 설명이 없습니다.")}</p></div><button class="text-button" id="clear-github-result">결과 닫기</button></div>
          <div class="github-meta"><span>${escapeHtml(result.repository.branch)} Branch</span><span>기준 SHA <code>${escapeHtml(result.commit_sha.slice(0, 12))}</code></span><span>${new Date(result.created_at).toLocaleString("ko-KR")}</span></div>
          <div class="progress-kpis github-kpis"><div class="progress-kpi"><span>파일</span><strong>${result.file_count}</strong><small>${result.tree_truncated ? "목록 일부" : "수집 완료"}</small></div><div class="progress-kpi"><span>기술 스택</span><strong>${result.tech_stack.length}</strong><small>${result.tech_stack.map(escapeHtml).join(" · ") || "확인 불가"}</small></div><div class="progress-kpi"><span>최근 커밋</span><strong>${result.commits.length}</strong><small>최근 최대 10건 · 품질 점수 아님</small></div><div class="progress-kpi"><span>과제 검증</span><strong class="github-status">${escapeHtml(statusLabels[review.task_verification])}</strong><small>${escapeHtml(review.task_feedback)}</small></div></div>
          <section class="github-section"><div class="step-meta"><h3>프로젝트 진단</h3><span>${escapeHtml(review.summary)}</span></div>${review.strengths.length ? `<ul class="github-list">${review.strengths.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}${review.implemented_features.length ? `<h4>확인된 구현 단서</h4><ul class="github-list">${review.implemented_features.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}${review.findings.length ? `<h4>개선 제안</h4><div class="github-findings">${review.findings.map((item) => `<article class="github-finding"><div class="step-meta"><strong>${escapeHtml(item.category)}</strong><span class="finding-severity severity-${item.severity}">${escapeHtml(item.severity)}</span></div><p>${escapeHtml(item.description)}</p><p class="muted">${escapeHtml(item.recommendation)}</p>${item.evidence_files.length ? `<small>근거 파일: ${item.evidence_files.map(escapeHtml).join(", ")}</small>` : `<small>파일 근거를 특정하지 못했습니다.</small>`}</article>`).join("")}</div>` : `<p class="muted">수집한 정적 증거에서 등록된 개선 항목이 없습니다.</p>`}</section>
          <section class="github-section"><div class="step-meta"><h3>README 평가</h3><strong>${result.readme.present ? `${result.readme.score} / 100` : "README 없음"}</strong></div>${result.readme.present ? `<div class="readme-checks">${result.readme.sections.map((item) => `<div><span class="${item.met ? "check-met" : "check-missing"}" aria-label="${item.met ? "확인됨" : "보완 필요"}">${item.met ? "✓" : "!"}</span><span>${escapeHtml(item.name)}</span><small>${item.points}점</small></div>`).join("")}</div><details><summary>README 발췌</summary><pre class="code-block">${escapeHtml(result.readme.excerpt)}</pre></details>` : `<p class="muted">README 파일을 찾지 못했습니다. 기능 및 실행 안내를 추가해 보세요.</p>`}</section>
          <section class="github-section"><div class="step-meta"><h3>기술 스택</h3><span>저장소 파일 및 GitHub 언어 데이터</span></div><div class="tag-list github-tags">${Object.entries(result.languages).map(([name, bytes]) => `<span class="pill">${escapeHtml(name)} · ${Number(bytes).toLocaleString()} B</span>`).join("")}${result.tech_stack.map((name) => `<span class="pill">${escapeHtml(name)}</span>`).join("")}</div></section>
          <section class="github-section"><div class="step-meta"><h3>프로젝트 구조</h3><span>${result.files.length}개 경로 표시${result.tree_truncated ? " · 결과 제한됨" : ""}</span></div><div class="github-file-list">${result.files.slice(0, 100).map((path) => `<code>${escapeHtml(path)}</code>`).join("")}</div><p class="tiny muted">분석 대상 Commit: ${escapeHtml(result.commit_sha)} · AI 입력 파일: ${result.analyzed_source_files.map(escapeHtml).join(", ") || "없음"}</p></section>
          <section class="github-section"><div class="step-meta"><h3>최근 커밋</h3><span>최대 10건 · 개발 활동 참고 지표</span></div><div class="github-commits">${result.commits.map((item) => `<div><span><strong>${escapeHtml(item.message)}</strong><small>${escapeHtml(item.author)} · ${item.committed_at ? new Date(item.committed_at).toLocaleDateString("ko-KR") : "날짜 확인 불가"}</small></span><code>${escapeHtml((item.sha || "").slice(0, 8))}</code></div>`).join("") || `<p class="muted">커밋을 확인할 수 없습니다.</p>`}</div></section>
        </section>` : ""}
      <section class="github-history"><div class="step-meta"><h2>분석 이력</h2><span>최신 20건</span></div>${history.length ? `<div class="github-history-list">${history.map((item) => `<button data-github-analysis-id="${escapeHtml(item.id)}"><span><strong>${escapeHtml(item.owner)}/${escapeHtml(item.repo_name)}</strong><small>${escapeHtml(item.branch)} · ${new Date(item.created_at).toLocaleString("ko-KR")}</small><small>${escapeHtml(item.summary)}</small></span><span aria-hidden="true">›</span></button>`).join("")}</div>` : `<p class="muted">저장된 분석이 없습니다.</p>`}</section>
    </section>`;
  document.querySelector("#clear-github-result")?.addEventListener("click", () => { state.githubResult = null; renderGithubAnalysis(); });
  document.querySelectorAll("[data-github-analysis-id]").forEach((button) => button.addEventListener("click", async () => {
    try {
      state.githubResult = await api(`/api/github/analyses/${encodeURIComponent(button.dataset.githubAnalysisId)}`);
      renderGithubAnalysis();
    } catch (err) { showToast(err.message); }
  }));
  document.querySelector("#github-analysis-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const button = event.currentTarget.querySelector("button[type=submit]");
    button.disabled = true;
    button.textContent = "GitHub 데이터 수집 및 분석 중...";
    try {
      state.githubResult = await api("/api/github/analyses", {
        method: "POST",
        body: JSON.stringify({
          repo_url: form.get("repo_url"),
          branch: form.get("branch"),
          task_criteria: form.get("task_criteria"),
        }),
      });
      state.githubAnalyses = await api("/api/github/analyses");
      renderGithubAnalysis();
    } catch (err) {
      button.disabled = false;
      button.textContent = "저장소 분석";
      setError("github-analysis-error", err.message);
    }
  });
}

function renderProgressDashboard() {
  const progress = state.progress;
  progressNavigation("dashboard");
  main.innerHTML = `
    <section class="progress-page">
      <div class="eyebrow">개인별 학습진도</div><h1>나의 학습 현황</h1>
      <p class="subtitle">${escapeHtml(progress.goal)} · ${state.plan.duration_weeks}주 학습계획</p>
      <div class="progress-kpis">
        <div class="progress-kpi"><span>전체 과제 완료율</span><strong>${progress.completion_rate}%</strong><small>${progress.completed_tasks}/${progress.total_tasks}개 완료</small></div>
        <div class="progress-kpi"><span>누적 학습시간</span><strong>${(progress.actual_minutes / 60).toFixed(1)}h</strong><small>계획 ${(progress.planned_minutes / 60).toFixed(1)}h</small></div>
        <div class="progress-kpi"><span>진행 중 과제</span><strong>${progress.in_progress_tasks}개</strong><small>현재 수행 상태</small></div>
        <div class="progress-kpi"><span>보류 과제</span><strong>${progress.blocked_tasks}개</strong><small>도움이 필요한 과제</small></div>
      </div>
      <div class="progress-overview"><div class="step-meta"><strong>전체 학습 진도</strong><span>${progress.completed_tasks}/${progress.total_tasks} 과제</span></div><div class="progress-track"><div class="progress-fill" style="width:${progress.completion_rate}%"></div></div><p class="tiny muted">완료율은 완료로 확정한 과제만 반영합니다. 학습시간 달성률과는 별도로 계산됩니다.</p></div>
      <div class="progress-section-heading"><div><div class="eyebrow">주차별 계획</div><h2>이번 계획의 흐름</h2></div><button class="text-button" id="open-tasks">과제 관리 보기</button></div>
      <div class="week-progress-list">${progress.weeks.map((week) => `<button class="week-progress-row" data-week-no="${week.week_no}"><span class="week-progress-title"><strong>${week.week_no}주차</strong><small>${escapeHtml(week.weekly_goal)}</small></span><span class="week-progress-value">${week.completed_tasks}/${week.total_tasks} 완료 · ${week.completion_rate}%</span><span class="week-progress-track"><i style="width:${week.completion_rate}%"></i></span></button>`).join("")}</div>
      <div class="coach-strip"><div><span class="eyebrow">학습 코칭</span><p>${progress.blocked_tasks ? `보류 과제 ${progress.blocked_tasks}개가 있습니다. 막힌 지점을 정리해 다음 행동을 정해 보세요.` : progress.in_progress_tasks ? `진행 중인 과제 ${progress.in_progress_tasks}개를 완료 기준에 맞춰 이어가 보세요.` : "가장 앞선 미완료 과제부터 작게 시작해 보세요."}</p></div><button class="btn secondary" id="open-coach">진도 분석 보기</button></div>
    </section>`;
  document.querySelector("#open-tasks").addEventListener("click", () => openProgressView("tasks"));
  document.querySelector("#open-coach").addEventListener("click", () => openProgressView("coach"));
  document.querySelectorAll("[data-week-no]").forEach((button) => button.addEventListener("click", () => {
    state.selectedWeek = Number(button.dataset.weekNo);
    state.selectedTask = null;
    openProgressView("tasks");
  }));
}

function renderProgressTasks() {
  progressNavigation("tasks");
  const week = state.progress.weeks.find((item) => item.week_no === state.selectedWeek) || state.progress.weeks[0];
  state.selectedWeek = week.week_no;
  const statusNames = { todo: "시작 전", in_progress: "진행 중", completed: "완료", blocked: "보류" };
  main.innerHTML = `
    <section class="progress-page">
      <div class="eyebrow">과제 관리</div><h1>주차별 학습 현황</h1><p class="subtitle">주차를 선택하고 과제별 수행 내용과 실제 학습시간을 기록합니다.</p>
      <div class="week-tabs" role="tablist" aria-label="학습 주차">${state.progress.weeks.map((item) => `<button role="tab" aria-selected="${item.week_no === week.week_no}" data-select-week="${item.week_no}">${item.week_no}주차</button>`).join("")}</div>
      <div class="week-progress-heading"><div><span class="eyebrow">${week.week_no}주차 목표</span><h2>${escapeHtml(week.weekly_goal)}</h2></div><span class="pill">${week.completed_tasks}/${week.total_tasks} 완료</span></div>
      <p class="tiny muted">계획 ${(week.planned_minutes / 60).toFixed(1)}시간 · 실제 ${(week.actual_minutes / 60).toFixed(1)}시간</p>
      <div class="task-progress-list">${week.tasks.map((task) => `<button class="task-progress-row ${task.id === state.selectedTask ? "selected" : ""}" data-task-id="${escapeHtml(task.id)}"><span class="task-state state-${task.status}">${statusNames[task.status]}</span><span class="task-progress-copy"><strong>${escapeHtml(task.title)}</strong><small>계획 ${(task.planned_minutes / 60).toFixed(1)}h · 실제 ${(task.actual_minutes / 60).toFixed(1)}h</small></span><span class="task-progress-arrow" aria-hidden="true">›</span></button>`).join("")}</div>
      ${state.taskDetail ? renderTaskDetailMarkup(state.taskDetail, statusNames) : `<div class="empty-progress">과제를 선택하면 상세 기록과 완료 기준을 확인할 수 있습니다.</div>`}
    </section>`;
  document.querySelectorAll("[data-select-week]").forEach((button) => button.addEventListener("click", () => {
    state.selectedWeek = Number(button.dataset.selectWeek);
    state.selectedTask = null;
    openProgressView("tasks");
  }));
  document.querySelectorAll("[data-task-id]").forEach((button) => button.addEventListener("click", async () => {
    state.selectedTask = button.dataset.taskId;
    await openProgressView("tasks");
  }));
  bindTaskForms();
}

function renderTaskDetailMarkup(task, statusNames) {
  const latest = task.submissions[0];
  return `<article class="task-detail" id="task-detail">
    <div class="task-detail-heading"><div><span class="eyebrow">${task.week_no}주차 과제</span><h2>${escapeHtml(task.title)}</h2></div><span class="task-state state-${task.status}">${statusNames[task.status]}</span></div>
    <div class="completion-criteria"><strong>완료 기준</strong><p>${escapeHtml(task.completion_criteria)}</p><span class="tiny muted">결과물: ${escapeHtml(task.deliverable)}</span></div>
    <form id="task-progress-form" class="progress-form">
      <div class="field"><label for="task-status">과제 상태</label><select id="task-status" name="status" ${task.status === "completed" ? "disabled" : ""}><option value="todo" ${task.status === "todo" ? "selected" : ""}>시작 전</option><option value="in_progress" ${task.status === "in_progress" ? "selected" : ""}>진행 중</option><option value="blocked" ${task.status === "blocked" ? "selected" : ""}>보류</option></select></div>
      <div class="field"><label for="learning-start-date">학습 시작일</label><input id="learning-start-date" name="learning_start_date" type="date" value="${escapeHtml(task.learning_start_date || "")}" /></div>
      <div class="field"><label for="learning-notes">학습 내용</label><textarea id="learning-notes" name="learning_notes" maxlength="2000">${escapeHtml(task.learning_notes)}</textarea></div>
      <div class="field"><label for="difficulty-notes">어려웠던 점</label><textarea id="difficulty-notes" name="difficulty_notes" maxlength="2000">${escapeHtml(task.difficulty_notes)}</textarea></div>
      <div class="field"><label for="learner-memo">학습자 메모</label><textarea id="learner-memo" name="learner_memo" maxlength="2000">${escapeHtml(task.learner_memo)}</textarea></div>
      <button class="btn secondary" type="submit">과제 기록 저장</button>
    </form>
    <form id="time-log-form" class="progress-form compact-form"><h3>학습시간 기록</h3><input type="hidden" name="log_id" /><div class="form-columns"><div class="field"><label for="time-date">학습 날짜</label><input id="time-date" name="learning_date" type="date" value="${new Date().toISOString().slice(0, 10)}" required /></div><div class="field"><label for="time-minutes">실제 학습시간 (분)</label><input id="time-minutes" name="duration_minutes" type="number" min="1" max="1440" step="1" required /></div></div><div class="field"><label for="time-notes">학습 메모</label><input id="time-notes" name="notes" maxlength="2000" /></div><button class="btn secondary" type="submit">시간 추가</button><p class="tiny muted">누적 실제 학습시간: ${(task.actual_minutes / 60).toFixed(1)}시간</p><div class="time-log-list">${task.time_logs.map((log) => `<div class="time-log-row"><span><strong>${escapeHtml(log.learning_date)} · ${log.duration_minutes}분</strong><small>${escapeHtml(log.notes || "메모 없음")}</small></span><button type="button" class="text-button" data-edit-time-log="${escapeHtml(log.id)}">수정</button></div>`).join("") || `<p class="tiny muted">아직 기록된 학습시간이 없습니다.</p>`}</div></form>
    <form id="submission-form" class="progress-form compact-form"><h3>결과물 제출</h3><div class="field"><label for="submission-url">GitHub URL <span class="muted">(선택)</span></label><input id="submission-url" name="github_url" type="url" placeholder="https://github.com/username/repository" maxlength="500" /></div><div class="field"><label for="submission-explanation">학습 결과 설명</label><textarea id="submission-explanation" name="explanation" maxlength="2000" placeholder="구현한 내용이나 결과를 기록해 주세요."></textarea></div><button class="btn secondary" type="submit">결과물 제출</button>${latest ? `<p class="tiny muted">최근 제출 ${new Date(latest.submitted_at).toLocaleString("ko-KR")} · ${latest.github_url ? `<a href="${escapeHtml(latest.github_url)}" target="_blank" rel="noopener noreferrer">GitHub 열기</a>` : "설명 기록"}</p>` : ""}</form>
    <form id="completion-form" class="completion-form"><label class="check-row"><input type="checkbox" name="completion_criteria_confirmed" ${task.status === "completed" ? "checked disabled" : ""} /><span>위 완료 기준을 확인했고 과제를 완료했습니다.</span></label><button class="btn" type="submit" ${task.status === "completed" ? "disabled" : ""}>${task.status === "completed" ? "과제 완료" : "완료 요청"}</button></form>
  </article>`;
}

function bindTaskForms() {
  const taskId = state.selectedTask;
  if (!taskId || !state.taskDetail) return;
  document.querySelector("#task-progress-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    payload.status = document.querySelector("#task-status").value;
    try {
      await api(`/api/tasks/${encodeURIComponent(taskId)}`, { method: "PATCH", body: JSON.stringify(payload) });
      showToast("과제 기록을 저장했습니다.");
      await openProgressView("tasks");
    } catch (err) { showToast(err.message); }
  });
  document.querySelector("#time-log-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const logId = form.get("log_id");
    try {
      await api(`/api/tasks/${encodeURIComponent(taskId)}/time-logs${logId ? `/${encodeURIComponent(logId)}` : ""}`, { method: logId ? "PATCH" : "POST", body: JSON.stringify({
        learning_date: form.get("learning_date"), duration_minutes: Number(form.get("duration_minutes")), notes: form.get("notes"),
      }) });
      showToast(logId ? "학습시간 기록을 수정했습니다." : "학습시간을 기록했습니다.");
      await openProgressView("tasks");
    } catch (err) { showToast(err.message); }
  });
  document.querySelectorAll("[data-edit-time-log]").forEach((button) => button.addEventListener("click", () => {
    const log = state.taskDetail.time_logs.find((item) => item.id === button.dataset.editTimeLog);
    if (!log) return;
    const form = document.querySelector("#time-log-form");
    form.elements.log_id.value = log.id;
    form.elements.learning_date.value = log.learning_date;
    form.elements.duration_minutes.value = log.duration_minutes;
    form.elements.notes.value = log.notes;
    form.querySelector("button[type=submit]").textContent = "시간 수정 저장";
    form.scrollIntoView({ behavior: "smooth", block: "center" });
    form.elements.duration_minutes.focus();
  }));
  document.querySelector("#submission-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await api(`/api/tasks/${encodeURIComponent(taskId)}/submissions`, { method: "POST", body: JSON.stringify({
        github_url: form.get("github_url") || null, explanation: form.get("explanation") || null,
      }) });
      showToast("결과물을 제출했습니다.");
      await openProgressView("tasks");
    } catch (err) { showToast(err.message); }
  });
  document.querySelector("#completion-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await api(`/api/tasks/${encodeURIComponent(taskId)}/completion-request`, { method: "POST", body: JSON.stringify({
        completion_criteria_confirmed: form.has("completion_criteria_confirmed"),
      }) });
      showToast("과제를 완료 처리했습니다.");
      await openProgressView("tasks");
    } catch (err) { showToast(err.message); }
  });
}

function renderProgressHistory() {
  progressNavigation("history");
  const stats = state.progressStats;
  const eventNames = { status_changed: "과제 상태 변경", time_logged: "학습시간 기록", submission_created: "결과물 제출", task_completed: "과제 완료" };
  main.innerHTML = `<section class="progress-page"><div class="eyebrow">학습 통계</div><h1>학습 기록과 통계</h1><p class="subtitle">${escapeHtml(state.progress.goal)}의 실적을 누적 기록 기준으로 확인합니다.</p>
    <div class="progress-kpis stats-kpis"><div class="progress-kpi"><span>과제 완료율</span><strong>${stats.completion_rate}%</strong><small>${state.progress.completed_tasks}/${state.progress.total_tasks}개 완료</small></div><div class="progress-kpi"><span>학습시간 달성률</span><strong>${stats.learning_time_rate}%</strong><small>실제 ${(state.progress.actual_minutes / 60).toFixed(1)}h / 계획 ${(state.progress.planned_minutes / 60).toFixed(1)}h</small></div><div class="progress-kpi"><span>결과물 제출률</span><strong>${stats.submission_rate}%</strong><small>${state.progress.submitted_tasks}/${state.progress.submission_tasks}개 제출</small></div><div class="progress-kpi"><span>학습 연속일</span><strong>${stats.learning_streak_days}일</strong><small>학습시간 기록 기준</small></div></div>
    <div class="progress-overview"><div class="step-meta"><strong>주차별 실적</strong><span>계획 대비 실제</span></div>${state.progress.weeks.map((week) => `<div class="history-week"><div class="step-meta"><span>${week.week_no}주차 · ${week.completed_tasks}/${week.total_tasks} 완료</span><span>${(week.actual_minutes / 60).toFixed(1)}h / ${(week.planned_minutes / 60).toFixed(1)}h</span></div><div class="week-progress-track"><i style="width:${week.completion_rate}%"></i></div></div>`).join("")}<p class="tiny muted">완료 과제 평균 수행시간: ${(stats.average_completed_task_minutes / 60).toFixed(1)}시간</p></div>
    <div class="progress-section-heading"><div><div class="eyebrow">최근 활동</div><h2>학습 이력</h2></div></div><div class="activity-list">${state.activityRows.length ? state.activityRows.map((activity) => `<article class="activity-row"><span class="activity-mark"></span><div><strong>${escapeHtml(eventNames[activity.event_type] || activity.event_type)}</strong><p>${activity.week_no}주차 · ${escapeHtml(activity.title)}</p><small>${new Date(activity.created_at).toLocaleString("ko-KR")}</small></div></article>`).join("") : `<p class="empty-progress">아직 기록된 학습 활동이 없습니다.</p>`}</div>
    <div class="coach-strip"><div><span class="eyebrow">다음 행동</span><p>현재 기록을 바탕으로 다음 학습 행동을 확인해 보세요.</p></div><button class="btn secondary" id="open-coach">학습 코칭 보기</button></div></section>`;
  document.querySelector("#open-coach").addEventListener("click", () => openProgressView("coach"));
}

function renderProgressCoach() {
  progressNavigation("coach");
  const coach = state.coachFeedback;
  main.innerHTML = `<section class="progress-page"><div class="eyebrow">학습 코칭</div><h1>다음 학습 행동</h1><p class="subtitle">저장된 과제 상태와 학습시간 기록으로 만든 추천입니다. 기록되지 않은 학습은 추정하지 않습니다.</p>
    <div class="coach-panel"><span class="coach-label">현재 진도 ${coach.completion_rate}% · 보류 ${coach.blocked_tasks}개</span><h2>${escapeHtml(coach.summary)}</h2><ul>${coach.actions.map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ul><small>기록 기반 규칙 추천 · ${new Date(coach.generated_at).toLocaleString("ko-KR")}</small></div>
    <form id="revision-request-form" class="progress-form"><div class="eyebrow">FR-03 계획 조정 요청</div><h2>계획 조정이 필요하신가요?</h2><p class="tiny muted">요청은 기록으로 저장됩니다. 현재 계획은 자동으로 변경되지 않습니다.</p><div class="field"><label for="revision-reason">조정이 필요한 이유</label><textarea id="revision-reason" name="reason" maxlength="2000" required placeholder="예: 이번 주 학습 가능 시간이 줄어들어 남은 과제 일정을 조정하고 싶습니다."></textarea></div><button class="btn" type="submit">재계획 요청 제출</button></form>
    <button class="text-button" id="back-progress">진도 대시보드로 돌아가기</button></section>`;
  document.querySelector("#revision-request-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const reason = new FormData(event.currentTarget).get("reason");
    try {
      await api(`/api/plans/${encodeURIComponent(state.progress.plan_id)}/revision-request`, { method: "POST", body: JSON.stringify({ reason }) });
      showToast("재계획 요청을 저장했습니다.");
      event.currentTarget.reset();
    } catch (err) { showToast(err.message); }
  });
  document.querySelector("#back-progress").addEventListener("click", () => openProgressView("dashboard"));
}

async function bootstrap() {
  setLoading("AI DevCoach를 준비하고 있어요");
  try {
    state.user = await api("/api/auth/me");
    if (!state.user.profile_completed) return renderProfile();
    state.profile = await api("/api/profiles/me");
    if (!state.user.assessment_completed) return renderAssessmentIntro();
    state.assessmentResult = await api("/api/assessments/latest");
    try {
      state.plan = await api("/api/plans/current");
      return renderDashboard();
    } catch (err) {
      if (err.status === 404) return renderResults();
      throw err;
    }
  } catch (err) {
    if (err.status === 401) return renderAuth("signup");
    main.innerHTML = `<section class="narrow card center"><h2>서비스에 연결할 수 없습니다</h2><p class="muted">${escapeHtml(err.message)}</p><button id="retry" class="btn">다시 시도</button></section>`;
    document.querySelector("#retry").addEventListener("click", bootstrap);
  }
}

bootstrap();
