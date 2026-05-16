const BASE_URL = "http://localhost:8000";
  let currentToken = null, currentRole = null, currentUser = null;
  let currentTeacherCourseId = null, currentTeacherCourseName = null;

  function getEl(id) {
    const el = document.getElementById(id);
    if (!el) console.warn(`Элемент с id="${id}" не найден`);
    return el;
  }

  function safeClass(el, action, className) {
    if (el) {
      if (action === 'add') el.classList.add(className);
      else if (action === 'remove') el.classList.remove(className);
    } else {
      console.warn('Попытка изменить класс у несуществующего элемента');
    }
  }

  const authScreen = getEl("auth-screen");
  const studentDashboard = getEl("student-dashboard");
  const teacherDashboard = getEl("teacher-dashboard");
  const authError = getEl("auth-error");
  const headerLogoutBtn = getEl("header-logout-btn");

  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      document.querySelectorAll("form").forEach(f => f.classList.remove("active"));
      const targetForm = getEl(tab.dataset.form);
      if (targetForm) targetForm.classList.add("active");
    });
  });

  async function apiRequest(url, method, body = null, isPublic = false) {
    const headers = { "Content-Type": "application/json" };
    if (!isPublic && currentToken) {
      headers["Authorization"] = `Bearer ${currentToken}`;
    }
    const resp = await fetch(`${BASE_URL}${url}`, { method, headers, body: body ? JSON.stringify(body) : null });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || JSON.stringify(data));
    return data;
  }

  function saveSession(token, role, user) {
    currentToken = token; currentRole = role; currentUser = user;
    localStorage.setItem("token", token);
    localStorage.setItem("role", role);
    localStorage.setItem("user", JSON.stringify(user));
    safeClass(headerLogoutBtn, 'add', 'visible');
    console.log('Сессия сохранена, роль:', role);
  }
  function clearSession() {
    currentToken = null; currentRole = null; currentUser = null;
    localStorage.clear();
    safeClass(headerLogoutBtn, 'remove', 'visible');
  }

  function showDashboard(role, user) {
    console.log('showDashboard вызвана, роль:', role, 'пользователь:', user);
    safeClass(authScreen, 'add', 'hidden');
    safeClass(studentDashboard, 'add', 'hidden');
    safeClass(teacherDashboard, 'add', 'hidden');

    if (role === "student") {
      safeClass(studentDashboard, 'remove', 'hidden');
      const nameSpan = getEl("s-name");
      if (nameSpan) nameSpan.textContent = `${user.last_name} ${user.first_name}`;
      loadStudentCourses();
    } else if (role === "teacher") {
      safeClass(teacherDashboard, 'remove', 'hidden');
      const nameSpan = getEl("t-name");
      if (nameSpan) nameSpan.textContent = `${user.last_name} ${user.first_name}`;
      loadTeacherGroups();
    } else {
      console.error('Неизвестная роль:', role);
    }
  }

  async function loadStudentCourses() {
    console.log('Загрузка курсов студента');
    safeClass(getEl("s-courses-container"), 'remove', 'hidden');
    safeClass(getEl("s-exercises-container"), 'add', 'hidden');
    try {
      const courses = await apiRequest("/student/courses", "GET");
      const tbody = document.querySelector("#s-courses-table tbody");
      if (!tbody) return;
      tbody.innerHTML = "";
      if (!courses.length) {
        tbody.innerHTML = "<tr><td colspan='5'>Нет назначенных курсов</td></tr>";
        return;
      }
      courses.forEach(c => {
        const tr = document.createElement("tr");
        tr.className = "clickable";
        tr.innerHTML = `<td>${c.course_name}</td><td>${c.teacher_name||""}</td><td>${c.start_date}</td><td>${c.end_date}</td><td>${c.status}</td>`;
        tr.addEventListener("click", () => showStudentExercises(c.course_id, c.course_name));
        tbody.appendChild(tr);
      });
    } catch (err) {
      const errEl = getEl("s-error");
      if (errEl) { errEl.textContent = "Ошибка загрузки курсов: " + err.message; safeClass(errEl, 'remove', 'hidden'); }
      console.error(err);
    }
  }

  async function showStudentExercises(courseId, courseName) {
    safeClass(getEl("s-courses-container"), 'add', 'hidden');
    safeClass(getEl("s-exercises-container"), 'remove', 'hidden');
    const heading = getEl("s-exercise-course-name");
    if (heading) heading.textContent = `Задания курса «${courseName}»`;
    try {
      const exercises = await apiRequest(`/student/courses/${courseId}/exercises`, "GET");
      const tbody = document.querySelector("#s-exercises-table tbody");
      if (!tbody) return;
      tbody.innerHTML = "";
      if (!exercises.length) {
        tbody.innerHTML = "<tr><td colspan='4'>Нет заданий</td></tr>";
        return;
      }
      exercises.forEach(ex => {
        const tr = document.createElement("tr");
        tr.className = "clickable";
        tr.innerHTML = `<td>${ex.exercise_name}</td><td>${ex.expires_on}</td><td>${ex.max_score}</td><td>${ex.status}</td>`;
        tr.addEventListener("click", () => openExerciseModal(ex.exercise_id, "student"));
        tbody.appendChild(tr);
      });
    } catch (err) {
      const errEl = getEl("s-error");
      if (errEl) { errEl.textContent = "Ошибка: " + err.message; safeClass(errEl, 'remove', 'hidden'); }
    }
  }

  const sBackBtn = getEl("s-back-to-courses");
  if (sBackBtn) sBackBtn.addEventListener("click", loadStudentCourses);

  async function loadTeacherGroups() {
    console.log('Загрузка групп преподавателя');
    safeClass(getEl("t-groups-container"), 'remove', 'hidden');
    safeClass(getEl("t-courses-container"), 'add', 'hidden');
    safeClass(getEl("t-exercises-container"), 'add', 'hidden');
    try {
      const groups = await apiRequest("/teacher/groups", "GET");
      const tbody = document.querySelector("#t-groups-table tbody");
      if (!tbody) return;
      tbody.innerHTML = "";
      if (!groups.length) {
        tbody.innerHTML = "<tr><td colspan='3'>Нет курируемых групп</td></tr>";
        return;
      }
      groups.forEach(g => {
        const tr = document.createElement("tr");
        tr.className = "clickable";
        tr.innerHTML = `<td>${g.group_name}</td><td>${g.prof}</td><td>${g.student_count}</td>`;
        tr.addEventListener("click", () => showTeacherGroupCourses(g.group_id, g.group_name));
        tbody.appendChild(tr);
      });
    } catch (err) {
      const errEl = getEl("t-error");
      if (errEl) { errEl.textContent = "Ошибка: " + err.message; safeClass(errEl, 'remove', 'hidden'); }
      console.error(err);
    }
  }

  async function showTeacherGroupCourses(groupId, groupName) {
    safeClass(getEl("t-groups-container"), 'add', 'hidden');
    safeClass(getEl("t-courses-container"), 'remove', 'hidden');
    safeClass(getEl("t-exercises-container"), 'add', 'hidden');
    const heading = getEl("t-courses-group-name");
    if (heading) heading.textContent = `Активные курсы группы ${groupName}`;
    try {
      const courses = await apiRequest(`/teacher/groups/${groupId}/courses`, "GET");
      const tbody = document.querySelector("#t-group-courses-table tbody");
      if (!tbody) return;
      tbody.innerHTML = "";
      if (!courses.length) {
        tbody.innerHTML = "<tr><td colspan='4'>Нет активных курсов</td></tr>";
        return;
      }
      courses.forEach(c => {
        const tr = document.createElement("tr");
        tr.className = "clickable";
        tr.innerHTML = `<td>${c.course_name}</td><td>${c.teacher_name||""}</td><td>${c.start_date}</td><td>${c.end_date}</td>`;
        tr.addEventListener("click", () => showTeacherCourseExercises(c.course_id, c.course_name));
        tbody.appendChild(tr);
      });
    } catch (err) {
      const errEl = getEl("t-error");
      if (errEl) { errEl.textContent = "Ошибка: " + err.message; safeClass(errEl, 'remove', 'hidden'); }
    }
  }

  async function showTeacherCourseExercises(courseId, courseName) {
    currentTeacherCourseId = courseId;
    currentTeacherCourseName = courseName;
    safeClass(getEl("t-courses-container"), 'add', 'hidden');
    safeClass(getEl("t-exercises-container"), 'remove', 'hidden');
    const heading = getEl("t-exercise-course-name");
    if (heading) heading.textContent = `Задания курса «${courseName}»`;
    try {
      const exercises = await apiRequest(`/teacher/courses/${courseId}/exercises`, "GET");
      const tbody = document.querySelector("#t-exercises-table tbody");
      if (!tbody) return;
      tbody.innerHTML = "";
      if (!exercises.length) {
        tbody.innerHTML = "<tr><td colspan='4'>Нет заданий</td></tr>";
        return;
      }
      exercises.forEach(ex => {
        const tr = document.createElement("tr");
        tr.className = "clickable";
        tr.innerHTML = `<td>${ex.exercise_name}</td><td>${ex.expires_on}</td><td>${ex.max_score}</td><td>${ex.status}</td>`;
        tr.addEventListener("click", () => openExerciseModal(ex.exercise_id, "teacher"));
        tbody.appendChild(tr);
      });
    } catch (err) {
      const errEl = getEl("t-error");
      if (errEl) { errEl.textContent = "Ошибка: " + err.message; safeClass(errEl, 'remove', 'hidden'); }
    }
  }

  const tBackGroups = getEl("t-back-to-groups");
  if (tBackGroups) tBackGroups.addEventListener("click", loadTeacherGroups);
  const tBackCourses = getEl("t-back-to-courses");
  if (tBackCourses) tBackCourses.addEventListener("click", () => {
    safeClass(getEl("t-exercises-container"), 'add', 'hidden');
    safeClass(getEl("t-courses-container"), 'remove', 'hidden');
  });

  async function openExerciseModal(exerciseId, role) {
    const url = role === "student" ? `/student/exercises/${exerciseId}` : `/teacher/exercises/${exerciseId}`;
    try {
      const ex = await apiRequest(url, "GET");
      getEl("modal-title").textContent = ex.exercise_name;
      getEl("modal-course").textContent = ex.course_name || "—";
      getEl("modal-teacher").textContent = ex.teacher_name || "—";
      getEl("modal-deadline").textContent = ex.expires_on;
      getEl("modal-maxscore").textContent = ex.max_score;
      getEl("modal-status").textContent = ex.status;
      getEl("modal-description").textContent = ex.exercise_desc || "Нет описания";
      safeClass(getEl("exercise-modal"), 'add', 'active');
    } catch (err) {
      alert("Ошибка загрузки описания: " + err.message);
    }
  }
  function closeModal() { safeClass(getEl("exercise-modal"), 'remove', 'active'); }

  function openCreateModal() {
    safeClass(getEl("create-exercise-modal"), 'add', 'active');
    getEl("ce-name").value = "";
    getEl("ce-desc").value = "";
    getEl("ce-expires").value = "";
    getEl("ce-maxscore").value = "";
  }
  function closeCreateModal() { safeClass(getEl("create-exercise-modal"), 'remove', 'active'); }

  const createBtn = getEl("t-create-exercise-btn");
  if (createBtn) createBtn.addEventListener("click", openCreateModal);

  const createForm = getEl("create-exercise-form");
  if (createForm) {
    createForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!currentTeacherCourseId) { alert("Курс не выбран"); return; }
      const body = {
        exercise_name: getEl("ce-name").value.trim(),
        exercise_desc: getEl("ce-desc").value.trim() || null,
        expires_on: getEl("ce-expires").value,
        max_score: parseFloat(getEl("ce-maxscore").value),
      };
      try {
        await apiRequest(`/teacher/courses/${currentTeacherCourseId}/exercises`, "POST", body);
        closeCreateModal();
        showTeacherCourseExercises(currentTeacherCourseId, currentTeacherCourseName);
      } catch (err) {
        alert("Ошибка создания задания: " + err.message);
      }
    });
  }

  window.addEventListener("click", (e) => {
    if (e.target === getEl("exercise-modal")) closeModal();
    if (e.target === getEl("create-exercise-modal")) closeCreateModal();
  });

  async function handleAuthSuccess(token, role) {
    console.log('handleAuthSuccess, token:', token, 'role:', role);
    currentToken = token;
    try {
      const user = await apiRequest("/auth/me", "GET");
      console.log('Получен пользователь:', user);
      saveSession(token, role || user.role, user);
      showDashboard(role || user.role, user);
    } catch (err) {
      currentToken = null;
      if (authError) {
        authError.textContent = "Ошибка получения профиля: " + err.message;
        safeClass(authError, 'remove', 'hidden');
      }
      console.error(err);
    }
  }

  getEl("login").addEventListener("submit", async (e) => {
    e.preventDefault();
    safeClass(authError, 'add', 'hidden');
    try {
      const data = await apiRequest("/auth/login", "POST", {
        email: getEl("login-email").value.trim(),
        password: getEl("login-password").value
      }, true);
      await handleAuthSuccess(data.access_token, null);
    } catch (err) {
      if (authError) {
        authError.textContent = err.message;
        safeClass(authError, 'remove', 'hidden');
      }
    }
  });

  getEl("student").addEventListener("submit", async (e) => {
    e.preventDefault();
    safeClass(authError, 'add', 'hidden');
    try {
      const data = await apiRequest("/auth/register/student", "POST", {
        first_name: getEl("s-first").value.trim(),
        last_name: getEl("s-last").value.trim(),
        patronymic: getEl("s-patr").value.trim() || null,
        email: getEl("s-email").value.trim(),
        password: getEl("s-password").value,
        group_id: getEl("s-group").value ? parseInt(getEl("s-group").value) : null
      }, true);
      await handleAuthSuccess(data.access_token, "student");
    } catch (err) {
      if (authError) {
        authError.textContent = err.message;
        safeClass(authError, 'remove', 'hidden');
      }
    }
  });

  getEl("teacher").addEventListener("submit", async (e) => {
    e.preventDefault();
    safeClass(authError, 'add', 'hidden');
    try {
      const data = await apiRequest("/auth/register/teacher", "POST", {
        first_name: getEl("t-first").value.trim(),
        last_name: getEl("t-last").value.trim(),
        patronymic: getEl("t-patr").value.trim() || null,
        job_title: getEl("t-job").value.trim(),
        email: getEl("t-email").value.trim(),
        password: getEl("t-password").value
      }, true);
      await handleAuthSuccess(data.access_token, "teacher");
    } catch (err) {
      if (authError) {
        authError.textContent = err.message;
        safeClass(authError, 'remove', 'hidden');
      }
    }
  });

  function logout() {
    clearSession();
    safeClass(authScreen, 'remove', 'hidden');
    safeClass(studentDashboard, 'add', 'hidden');
    safeClass(teacherDashboard, 'add', 'hidden');
    document.querySelectorAll("input").forEach(i => i.value = "");
  }

  window.addEventListener("load", async () => {
    const savedToken = localStorage.getItem("token");
    const savedRole = localStorage.getItem("role");
    console.log('Восстановление сессии, токен:', savedToken, 'роль:', savedRole);
    if (savedToken && savedRole) {
      try {
        currentToken = savedToken;
        currentRole = savedRole;
        const user = await apiRequest("/auth/me", "GET");
        saveSession(savedToken, savedRole, user);
        showDashboard(savedRole, user);
      } catch (err) {
        console.error('Ошибка восстановления:', err);
        clearSession();
        safeClass(authScreen, 'remove', 'hidden');
      }
    } else {
      safeClass(authScreen, 'remove', 'hidden');
    }
  });