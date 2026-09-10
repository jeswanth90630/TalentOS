const API_BASE = '/api/v1';
let currentVacancies = [];
let activeRoleCategory = 'All';
let isRecruiterAuth = false;
let allCandidatesCache = [];
let autoRefreshTimer = null;

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  loadPublicVacancies();
  updateAuthUI();

  // Start background auto-refresh every 3 seconds to keep recruiter views strictly in sync
  autoRefreshTimer = setInterval(() => {
    if (isRecruiterAuth) {
      refreshAllRecruiterViews(false);
    }
  }, 3000);
});

// Helper to refresh all recruiter screens simultaneously
async function refreshAllRecruiterViews(showLoading = true) {
  try {
    await Promise.all([
      loadDashboardData(),
      loadJobs(),
      loadCandidates(),
      populateMatchingJobDropdown(true)
    ]);
  } catch (e) {
    console.error("Auto refresh error:", e);
  }
}

// Navigation Setup
function setupNavigation() {
  const navBtns = document.querySelectorAll('.nav-btn');
  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    if (btn.getAttribute('data-tab') === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  const isProtectedTab = ['dashboard', 'jobs', 'candidates', 'matching'].includes(tabId);
  const lockOverlay = document.getElementById('recruiter-lock-overlay');

  document.querySelectorAll('.tab-view').forEach(view => {
    if (view.id === `view-${tabId}`) {
      if (isProtectedTab && !isRecruiterAuth) {
        view.style.display = 'none';
        lockOverlay.style.display = 'block';
      } else {
        view.style.display = 'block';
        lockOverlay.style.display = 'none';
      }
    } else {
      view.style.display = 'none';
    }
  });

  if (isRecruiterAuth) {
    refreshAllRecruiterViews();
  }
}

// Recruiter Auth Handling
async function handleRecruiterLogin(event) {
  event.preventDefault();
  const passcode = document.getElementById('login-passcode').value;

  try {
    const formData = new FormData();
    formData.append('passcode', passcode);

    const res = await fetch(`${API_BASE}/auth/recruiter-login`, {
      method: 'POST',
      body: formData
    });

    if (res.ok) {
      isRecruiterAuth = true;
      closeModal('modal-login');
      document.getElementById('form-login').reset();
      updateAuthUI();
      switchTab('dashboard');
      refreshAllRecruiterViews();
    } else {
      alert('Invalid recruiter access passcode. Try: admin123');
    }
  } catch (err) {
    console.error(err);
    alert('Authentication request failed.');
  }
}

function logoutRecruiter() {
  isRecruiterAuth = false;
  updateAuthUI();
  switchTab('vacancies');
}

function updateAuthUI() {
  const loginBtn = document.getElementById('btn-login-modal');
  const recruiterBadge = document.getElementById('badge-recruiter-active');
  const recruiterNavs = document.querySelectorAll('.recruiter-only-nav');

  if (isRecruiterAuth) {
    if (loginBtn) loginBtn.style.display = 'none';
    if (recruiterBadge) recruiterBadge.style.display = 'flex';
    recruiterNavs.forEach(nav => {
      nav.style.display = 'flex';
    });
  } else {
    if (loginBtn) loginBtn.style.display = 'inline-flex';
    if (recruiterBadge) recruiterBadge.style.display = 'none';
    recruiterNavs.forEach(nav => {
      nav.style.display = 'none';
    });
  }
}

// PUBLIC CAREERS & VACANCIES PORTAL
async function loadPublicVacancies() {
  try {
    const res = await fetch(`${API_BASE}/jobs?status=Published`);
    if (!res.ok) return;
    currentVacancies = await res.json();
    renderPublicVacancies(currentVacancies);
  } catch (err) {
    console.error(err);
  }
}

function filterVacancies(category) {
  activeRoleCategory = category;

  document.querySelectorAll('.role-filter-btn').forEach(btn => {
    if (btn.innerText.includes(category) || (category === 'All' && btn.innerText.includes('All'))) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  if (category === 'All') {
    renderPublicVacancies(currentVacancies);
  } else {
    const filtered = currentVacancies.filter(j => 
      j.department.toLowerCase().includes(category.toLowerCase()) || 
      j.title.toLowerCase().includes(category.toLowerCase())
    );
    renderPublicVacancies(filtered);
  }
}

function renderPublicVacancies(jobs) {
  const container = document.getElementById('public-vacancies-grid');
  if (!jobs.length) {
    container.innerHTML = `<p style="color: var(--text-muted); padding: 2rem; grid-column: 1/-1; text-align: center;">No active vacancies found for this category.</p>`;
    return;
  }

  container.innerHTML = jobs.map(j => `
    <div class="metric-card" style="display: flex; flex-direction: column; justify-content: space-between;">
      <div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
          <h3 style="font-size: 1.15rem; font-weight: 700;">${j.title}</h3>
          <span class="badge badge-published">${j.department}</span>
        </div>
        <div style="font-size: 0.85rem; color: var(--accent-primary); margin-bottom: 0.8rem;">
          <i class="fa-solid fa-location-dot"></i> ${j.location} • <i class="fa-solid fa-business-time"></i> ${j.min_experience}+ Yrs Exp
        </div>
        <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1rem;">${j.description}</p>
        <div style="margin-bottom: 1.25rem;">
          <strong style="font-size: 0.75rem; color: var(--text-dim); display: block; margin-bottom: 0.3rem;">SKILLS REQUIRED:</strong>
          ${(j.required_skills || []).map(s => `<span class="skill-pill matched">${s}</span>`).join('')}
        </div>
      </div>
      <div>
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 0.85rem;">
          <span style="font-size: 0.85rem; color: var(--accent-emerald); font-weight: 600;">${j.salary_range || '$90k - $130k'}</span>
          <button class="btn btn-primary" onclick="openApplyModal(${j.id}, '${j.title.replace(/'/g, "\\'")}', '${j.department}')" style="padding: 0.45rem 1rem; font-size: 0.85rem;">
            <i class="fa-solid fa-paper-plane"></i> Apply Now
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

function openApplyModal(jobId, jobTitle, jobDept) {
  document.getElementById('apply-job-id').value = jobId;
  document.getElementById('apply-modal-job-title').innerText = `Apply for: ${jobTitle}`;
  document.getElementById('apply-modal-job-dept').innerText = `${jobDept} Department`;
  document.getElementById('apply-success-alert').style.display = 'none';
  document.getElementById('form-apply-job').style.display = 'block';
  openModal('modal-apply-job');
}

async function handlePublicJobApplication(event) {
  event.preventDefault();
  const jobId = document.getElementById('apply-job-id').value;
  const name = document.getElementById('app-name').value;
  const email = document.getElementById('app-email').value;
  const phone = document.getElementById('app-phone').value;
  const experience_years = document.getElementById('app-exp').value;
  const location = document.getElementById('app-location').value;
  const skills = document.getElementById('app-skills').value;
  const fileInput = document.getElementById('app-resume-file');

  if (!fileInput.files.length) {
    alert('Please select your PDF or DOCX resume file to submit application.');
    return;
  }

  const formData = new FormData();
  formData.append('name', name);
  formData.append('email', email);
  formData.append('phone', phone);
  formData.append('experience_years', experience_years);
  formData.append('location', location);
  formData.append('skills', skills);
  formData.append('resume_file', fileInput.files[0]);

  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/apply`, {
      method: 'POST',
      body: formData
    });

    if (res.ok) {
      document.getElementById('form-apply-job').style.display = 'none';
      document.getElementById('apply-success-alert').style.display = 'block';
      document.getElementById('form-apply-job').reset();
      refreshAllRecruiterViews();
    } else {
      alert('Application failed. Please try again.');
    }
  } catch (err) {
    console.error(err);
    alert('Failed to submit application.');
  }
}

// Modal Helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

// RECRUITER DASHBOARD
async function loadDashboardData() {
  try {
    const res = await fetch(`${API_BASE}/analytics/dashboard`);
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById('metric-candidates').innerText = data.total_candidates || 0;
    document.getElementById('metric-jobs').innerText = data.active_jobs || 0;
    document.getElementById('metric-applications').innerText = data.total_applications || 0;
    document.getElementById('metric-matches').innerText = data.ai_matches_performed || 0;

    const pipelineContainer = document.getElementById('pipeline-bars');
    const counts = data.pipeline_counts || {};
    const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;

    const stages = [
      { name: 'Applied', color: '#60a5fa' },
      { name: 'Screening', color: '#fbbf24' },
      { name: 'Interviewing', color: '#a78bfa' },
      { name: 'Offered', color: '#34d399' },
      { name: 'Hired', color: '#22d3ee' }
    ];

    pipelineContainer.innerHTML = stages.map(s => {
      const count = counts[s.name] || 0;
      const pct = Math.round((count / total) * 100);
      return `
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.3rem;">
            <span><strong style="color: ${s.color};">${s.name}</strong></span>
            <span style="color: var(--text-muted);">${count} Candidates (${pct}%)</span>
          </div>
          <div style="height: 8px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden;">
            <div style="width: ${Math.max(pct, 4)}%; height: 100%; background: ${s.color}; border-radius: 999px; transition: width 0.4s ease;"></div>
          </div>
        </div>
      `;
    }).join('');

    await loadDashboardRecentMatches();
  } catch (err) {
    console.error(err);
  }
}

async function loadDashboardRecentMatches() {
  try {
    const res = await fetch(`${API_BASE}/candidates`);
    if (!res.ok) return;
    const candidates = await res.json();

    const container = document.getElementById('dashboard-recent-matches');
    container.innerHTML = candidates.slice(0, 5).map(c => `
      <div class="item-card" style="padding: 0.85rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong style="font-size: 0.95rem;">${c.name}</strong>
            <p style="font-size: 0.8rem; color: var(--text-muted);">${c.current_role || 'Applicant'}</p>
          </div>
          <span class="badge badge-${c.status.toLowerCase()}">${c.status}</span>
        </div>
        <div style="margin-top: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
          <div>
            ${(c.skills || []).slice(0, 3).map(s => `<span class="skill-pill">${s}</span>`).join('')}
          </div>
          <button class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;" onclick="viewCandidateDetail(${c.id})">
            <i class="fa-solid fa-eye"></i> View
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

// JOB MANAGEMENT PIPELINE
async function loadJobs() {
  try {
    const res = await fetch(`${API_BASE}/jobs`);
    if (!res.ok) return;
    const jobs = await res.json();

    const container = document.getElementById('jobs-list');
    if (!jobs.length) {
      container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No job openings found. Click "Post New Job Opening" to create one.</p>`;
      return;
    }

    container.innerHTML = jobs.map(j => `
      <div class="item-card">
        <div class="card-top">
          <div>
            <h3 class="card-title">${j.title}</h3>
            <p style="font-size: 0.85rem; color: var(--accent-primary); margin-top: 0.1rem;">${j.department} • ${j.location}</p>
          </div>
          <span class="badge badge-published">${j.status}</span>
        </div>

        <div class="card-meta">
          <span><i class="fa-solid fa-briefcase"></i> ${j.job_type}</span>
          <span><i class="fa-solid fa-user-clock"></i> ${j.min_experience}+ Years Exp</span>
          <span><i class="fa-solid fa-money-bill-wave"></i> ${j.salary_range || 'Competitive'}</span>
          <span><i class="fa-solid fa-users"></i> <strong>${j.applicant_count}</strong> Applicants</span>
        </div>

        <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.8rem;">${j.description}</p>

        <div>
          <strong style="font-size: 0.8rem; color: var(--text-dim); display: block; margin-bottom: 0.3rem;">REQUIRED SKILLS:</strong>
          ${(j.required_skills || []).map(s => `<span class="skill-pill matched">${s}</span>`).join('')}
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

async function handleCreateJob(event) {
  event.preventDefault();
  const title = document.getElementById('job-title').value;
  const department = document.getElementById('job-dept').value;
  const location = document.getElementById('job-loc').value;
  const min_experience = parseInt(document.getElementById('job-exp').value) || 0;
  const salary_range = document.getElementById('job-salary').value;
  const rawSkills = document.getElementById('job-skills').value;
  const description = document.getElementById('job-desc').value;

  const required_skills = rawSkills.split(',').map(s => s.trim()).filter(Boolean);

  try {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title, department, location, min_experience, salary_range, required_skills, description, status: 'Published'
      })
    });

    if (res.ok) {
      closeModal('modal-job');
      document.getElementById('form-job').reset();
      loadJobs();
      loadPublicVacancies();
      loadDashboardData();
    }
  } catch (err) {
    console.error(err);
  }
}

// CANDIDATE MANAGEMENT
function toggleCandidateView(viewType) {
  const dirView = document.getElementById('candidates-directory-view');
  const kanbanView = document.getElementById('candidates-kanban-view');
  const btnList = document.getElementById('btn-view-list');
  const btnKanban = document.getElementById('btn-view-kanban');

  if (viewType === 'list') {
    dirView.style.display = 'block';
    kanbanView.style.display = 'none';
    btnList.className = 'btn btn-primary';
    btnKanban.className = 'btn btn-secondary';
  } else {
    dirView.style.display = 'none';
    kanbanView.style.display = 'block';
    btnList.className = 'btn btn-secondary';
    btnKanban.className = 'btn btn-primary';
  }
}

async function loadCandidates() {
  try {
    const res = await fetch(`${API_BASE}/candidates`);
    if (!res.ok) return;
    allCandidatesCache = await res.json();

    renderCandidatesDirectoryList(allCandidatesCache);
    renderCandidatesKanbanBoard(allCandidatesCache);
  } catch (err) {
    console.error(err);
  }
}

function renderCandidatesDirectoryList(candidates) {
  const container = document.getElementById('candidates-list');
  if (!candidates.length) {
    container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No candidates registered yet.</p>`;
    return;
  }

  const statuses = ['Applied', 'Screening', 'Interviewing', 'Offered', 'Hired', 'Rejected'];

  container.innerHTML = candidates.map(c => `
    <div class="item-card">
      <div class="card-top">
        <div>
          <h3 class="card-title">${c.name}</h3>
          <p style="font-size: 0.85rem; color: var(--text-muted);">${c.current_role || 'Software Developer'} • ${c.location || 'Remote'}</p>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
          <button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="viewCandidateDetail(${c.id})" title="View Resume & Details">
            <i class="fa-solid fa-eye"></i> View Profile
          </button>
          <select class="form-select" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onchange="updateCandidateStatus(${c.id}, this.value)">
            ${statuses.map(st => `<option value="${st}" ${c.status === st ? 'selected' : ''}>Status: ${st}</option>`).join('')}
          </select>
          <button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem; background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: rgba(16, 185, 129, 0.4);" onclick="updateCandidateStatus(${c.id}, 'Hired')" title="Select / Hire Candidate">
            <i class="fa-solid fa-user-check"></i> Hire
          </button>
          <button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem; background: rgba(244, 63, 94, 0.2); color: #fb7185; border-color: rgba(244, 63, 94, 0.4);" onclick="updateCandidateStatus(${c.id}, 'Rejected')" title="Reject Candidate">
            <i class="fa-solid fa-user-xmark"></i> Reject
          </button>
          <button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem; color: var(--text-muted);" onclick="deleteCandidate(${c.id})" title="Delete Profile">
            <i class="fa-solid fa-trash-can"></i>
          </button>
        </div>
      </div>

      <div class="card-meta">
        <span><i class="fa-solid fa-envelope"></i> ${c.email}</span>
        <span><i class="fa-solid fa-phone"></i> ${c.phone || 'N/A'}</span>
        <span><i class="fa-solid fa-user-graduate"></i> ${c.education || 'Degree Holder'}</span>
        <span><i class="fa-solid fa-business-time"></i> ${c.experience_years} Yrs Exp</span>
      </div>

      <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.8rem;">${c.summary || 'Experienced technical applicant.'}</p>

      <div style="margin-bottom: 1rem;">
        ${(c.skills || []).map(s => `<span class="skill-pill">${s}</span>`).join('')}
      </div>

      <div style="background: #f8fafc; padding: 0.75rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
        <strong style="font-size: 0.8rem; color: var(--text-dim);">RECRUITER NOTES (${(c.notes || []).length}):</strong>
        <div style="margin: 0.4rem 0;">
          ${(c.notes || []).map(n => `
            <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.2rem;">
              <strong style="color: var(--accent-primary);">${n.author}:</strong> ${n.note}
            </div>
          `).join('')}
        </div>
        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
          <input type="text" id="note-input-${c.id}" class="form-input" placeholder="Add recruiter evaluation note..." style="padding: 0.3rem 0.6rem; font-size: 0.8rem;">
          <button class="btn btn-secondary" onclick="addNote(${c.id})" style="padding: 0.3rem 0.7rem; font-size: 0.8rem;">Add</button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderCandidatesKanbanBoard(candidates) {
  const container = document.getElementById('kanban-board-container');
  const stages = [
    { key: 'Applied', name: 'Applied', color: '#60a5fa' },
    { key: 'Screening', name: 'Screening', color: '#fbbf24' },
    { key: 'Interviewing', name: 'Interviewing', color: '#a78bfa' },
    { key: 'Offered', name: 'Offered', color: '#34d399' },
    { key: 'Hired', name: 'Hired', color: '#22d3ee' }
  ];

  container.innerHTML = stages.map(st => {
    const list = candidates.filter(c => c.status === st.key);
    return `
      <div class="kanban-column">
        <div class="kanban-column-header">
          <span style="color: ${st.color}; font-weight: 700;">${st.name}</span>
          <span class="badge" style="background: rgba(255,255,255,0.08);">${list.length}</span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
          ${list.map(c => `
            <div class="kanban-card">
              <strong style="display: block; font-size: 0.9rem; margin-bottom: 0.2rem;">${c.name}</strong>
              <p style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 0.4rem;">${c.current_role || 'Applicant'}</p>
              <div style="margin-bottom: 0.5rem;">
                ${(c.skills || []).slice(0, 2).map(s => `<span class="skill-pill" style="font-size: 0.7rem;">${s}</span>`).join('')}
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; border-top: 1px solid var(--border-color); padding-top: 0.4rem;">
                <span>${c.experience_years} yrs exp</span>
                <select style="background: #ffffff; color: var(--text-main); border: 1px solid var(--border-color); border-radius: 4px; font-size: 0.72rem; padding: 2px 4px;" onchange="updateCandidateStatus(${c.id}, this.value)">
                  ${stages.map(s => `<option value="${s.key}" ${s.key === c.status ? 'selected' : ''}>Move: ${s.name}</option>`).join('')}
                  <option value="Rejected">Move: Reject</option>
                </select>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');
}

async function viewCandidateDetail(candId) {
  try {
    const res = await fetch(`${API_BASE}/candidates/${candId}`);
    if (!res.ok) return;
    const c = await res.json();

    document.getElementById('detail-candidate-name').innerText = c.name;
    document.getElementById('detail-role').innerText = `${c.current_role || 'Applicant'} (${c.status})`;
    document.getElementById('detail-contact').innerText = `${c.email} • ${c.phone || 'No phone'}`;
    document.getElementById('detail-meta').innerText = `${c.location || 'Remote'} • ${c.experience_years} Years Exp • ${c.education || 'Degree'}`;
    document.getElementById('detail-summary').innerText = c.resume_text || c.summary || 'No resume text logged.';

    const skillsBox = document.getElementById('detail-skills');
    skillsBox.innerHTML = (c.skills || []).map(s => `<span class="skill-pill matched">${s}</span>`).join('');

    openModal('modal-candidate-detail');
  } catch (err) {
    console.error(err);
  }
}

async function updateCandidateStatus(candId, newStatus) {
  try {
    await fetch(`${API_BASE}/candidates/${candId}/status?status=${encodeURIComponent(newStatus)}`, { method: 'PATCH' });
    await refreshAllRecruiterViews();
  } catch (err) {
    console.error(err);
  }
}

async function deleteCandidate(candId) {
  if (!confirm('Are you sure you want to delete this candidate profile?')) return;

  try {
    const res = await fetch(`${API_BASE}/candidates/${candId}`, { method: 'DELETE' });
    if (res.ok) {
      await refreshAllRecruiterViews();
    }
  } catch (err) {
    console.error(err);
  }
}

async function addNote(candId) {
  const input = document.getElementById(`note-input-${candId}`);
  if (!input || !input.value.trim()) return;

  try {
    await fetch(`${API_BASE}/candidates/${candId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: input.value.trim(), author: 'Recruiter' })
    });
    input.value = '';
    await loadCandidates();
  } catch (err) {
    console.error(err);
  }
}

async function handleCreateCandidate(event) {
  event.preventDefault();
  const name = document.getElementById('cand-name').value;
  const email = document.getElementById('cand-email').value;
  const current_role = document.getElementById('cand-role').value;
  const experience_years = parseFloat(document.getElementById('cand-exp').value) || 0;
  const education = document.getElementById('cand-edu').value;
  const rawSkills = document.getElementById('cand-skills').value;
  const summary = document.getElementById('cand-summary').value;

  const skills = rawSkills.split(',').map(s => s.trim()).filter(Boolean);

  try {
    const res = await fetch(`${API_BASE}/candidates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name, email, current_role, experience_years, education, skills, summary, status: 'Applied'
      })
    });

    if (res.ok) {
      closeModal('modal-candidate');
      document.getElementById('form-candidate').reset();
      await refreshAllRecruiterViews();
    }
  } catch (err) {
    console.error(err);
  }
}

// MATCHING ENGINE WITH HIGH CONTRAST DROPDOWN & AUTO LOAD RANKINGS
async function populateMatchingJobDropdown(preserveSelection = true) {
  try {
    const res = await fetch(`${API_BASE}/jobs`);
    if (!res.ok) return;
    const jobs = await res.json();

    const select = document.getElementById('matching-job-select');
    if (!select) return;

    if (!jobs.length) {
      select.innerHTML = `<option value="">No active job openings available</option>`;
      const container = document.getElementById('matching-results-container');
      if (container) container.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No active job openings found.</p>`;
      return;
    }

    const currentVal = select.value;
    select.innerHTML = jobs.map(j => `<option value="${j.id}">${j.title} (${j.department})</option>`).join('');

    if (preserveSelection && currentVal && jobs.some(j => String(j.id) === String(currentVal))) {
      select.value = currentVal;
    } else {
      select.value = jobs[0].id;
    }

    await loadJobMatchingRankings();
  } catch (err) {
    console.error(err);
  }
}

async function loadJobMatchingRankings() {
  const select = document.getElementById('matching-job-select');
  if (!select || !select.value) return;
  const jobId = select.value;

  try {
    const [resJob, resRank, resCands] = await Promise.all([
      fetch(`${API_BASE}/jobs/${jobId}`),
      fetch(`${API_BASE}/matching/job/${jobId}/rankings`),
      fetch(`${API_BASE}/candidates`)
    ]);

    if (!resRank.ok || !resCands.ok) return;

    const targetJob = resJob.ok ? await resJob.json() : null;
    const rankings = await resRank.json();
    const candsList = await resCands.json();
    const candsMap = {};
    candsList.forEach(c => candsMap[c.id] = c);

    const container = document.getElementById('matching-results-container');
    if (!container) return;

    let htmlContent = '';

    // Render Target Job Requirement Banner at the top of ATS Matching Engine
    if (targetJob) {
      htmlContent += `
        <div class="panel" style="margin-bottom: 1.5rem; background: #eff6ff; border: 1px solid #dbeafe;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
              <div style="display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;">
                <h2 style="font-size: 1.2rem; font-weight: 700; color: #0f172a; margin: 0;">Evaluating Requirements For: ${targetJob.title}</h2>
                <span class="badge badge-published">${targetJob.department}</span>
              </div>
              <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.3rem;">
                <i class="fa-solid fa-location-dot"></i> ${targetJob.location} • 
                <i class="fa-solid fa-business-time"></i> Min Experience: <strong>${targetJob.min_experience}+ Yrs</strong> • 
                <i class="fa-solid fa-money-bill-wave"></i> ${targetJob.salary_range || 'Competitive'}
              </p>
            </div>
            <div style="background: #ffffff; border: 1px solid #cbd5e1; padding: 0.5rem 1rem; border-radius: var(--radius-sm); text-align: right;">
              <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">Total Evaluated Candidates</span>
              <strong style="font-size: 1.15rem; color: var(--accent-primary);">${rankings.length} Candidates</strong>
            </div>
          </div>
          <div style="margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid #dbeafe;">
            <strong style="font-size: 0.8rem; color: var(--accent-primary); display: block; margin-bottom: 0.35rem;">TARGET JOB REQUIRED SKILLS:</strong>
            ${(targetJob.required_skills || []).map(s => `<span class="skill-pill matched" style="font-size: 0.8rem;"><i class="fa-solid fa-check-double"></i> ${s}</span>`).join('')}
          </div>
        </div>
      `;
    }

    if (!rankings.length) {
      htmlContent += `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No candidates currently evaluated for this job requirement.</p>`;
      container.innerHTML = htmlContent;
      return;
    }

    const statuses = ['Applied', 'Screening', 'Interviewing', 'Offered', 'Hired', 'Rejected'];

    const cardsHtml = rankings.map((r, index) => {
      const fullCand = candsMap[r.candidate_id] || {};
      const currentStatus = fullCand.status || 'Applied';
      const isTopMatch = (index === 0 && r.match_percentage >= 60.0);

      return `
        <div class="item-card" style="border-left: 4px solid ${r.match_percentage >= 80 ? 'var(--accent-emerald)' : 'var(--accent-amber)'}; ${isTopMatch ? 'background: #f0fdf4; border: 1px solid #86efac;' : ''}">
          <div class="card-top">
            <div>
              <div style="display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;">
                <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-dim);">#${index + 1}</span>
                <h3 class="card-title">${r.candidate_name}</h3>
                ${isTopMatch ? `<span class="badge" style="background: #16a34a; color: #ffffff; font-weight: 700; padding: 0.3rem 0.6rem; box-shadow: 0 2px 8px rgba(22, 163, 74, 0.3);"><i class="fa-solid fa-trophy"></i> BEST MATCH FOR THIS JOB</span>` : ''}
                <span class="badge badge-${currentStatus.toLowerCase()}">${currentStatus}</span>
              </div>
              <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.1rem;">${r.current_role || 'Candidate Profile'}</p>
            </div>

            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem;">
              <div style="text-align: right;">
                <div style="font-size: 1.6rem; font-weight: 800; color: ${r.match_percentage >= 80 ? 'var(--accent-emerald)' : 'var(--accent-amber)'};">
                  ${r.match_percentage}%
                </div>
                <span style="font-size: 0.72rem; color: var(--text-muted);">ATS Match Fit Score</span>
              </div>

              <!-- Recruiter Action Controls directly inside ATS Match card -->
              <div style="display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;">
                <button class="btn btn-secondary" style="padding: 0.3rem 0.55rem; font-size: 0.78rem;" onclick="viewCandidateDetail(${r.candidate_id})" title="View Candidate Profile & Resume">
                  <i class="fa-solid fa-eye"></i> View Profile
                </button>
                <select class="form-select" style="padding: 0.3rem 0.55rem; font-size: 0.78rem; width: auto;" onchange="updateCandidateStatus(${r.candidate_id}, this.value)">
                  ${statuses.map(st => `<option value="${st}" ${currentStatus === st ? 'selected' : ''}>Status: ${st}</option>`).join('')}
                </select>
                <button class="btn btn-secondary" style="padding: 0.3rem 0.55rem; font-size: 0.78rem; background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: rgba(16, 185, 129, 0.4);" onclick="updateCandidateStatus(${r.candidate_id}, 'Hired')" title="Hire / Select Candidate">
                  <i class="fa-solid fa-user-check"></i> Hire
                </button>
                <button class="btn btn-secondary" style="padding: 0.3rem 0.55rem; font-size: 0.78rem; background: rgba(244, 63, 94, 0.2); color: #fb7185; border-color: rgba(244, 63, 94, 0.4);" onclick="updateCandidateStatus(${r.candidate_id}, 'Rejected')" title="Reject Candidate">
                  <i class="fa-solid fa-user-xmark"></i> Reject
                </button>
                <button class="btn btn-secondary" style="padding: 0.3rem 0.55rem; font-size: 0.78rem; color: var(--text-muted);" onclick="deleteCandidate(${r.candidate_id})" title="Delete Candidate">
                  <i class="fa-solid fa-trash-can"></i>
                </button>
              </div>

            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.75rem;">
            <div>
              <strong style="font-size: 0.78rem; color: var(--accent-emerald); display: block; margin-bottom: 0.2rem;">MATCHING SKILLS:</strong>
              ${(r.matching_skills || []).map(s => `<span class="skill-pill matched"><i class="fa-solid fa-check"></i> ${s}</span>`).join('')}
            </div>
            <div>
              <strong style="font-size: 0.78rem; color: var(--accent-rose); display: block; margin-bottom: 0.2rem;">SKILL GAPS / MISSING:</strong>
              ${(r.missing_skills || []).length ? (r.missing_skills.map(s => `<span class="skill-pill missing"><i class="fa-solid fa-xmark"></i> ${s}</span>`).join('')) : '<span style="font-size: 0.8rem; color: var(--accent-emerald);">No skill gaps detected!</span>'}
            </div>
          </div>
        </div>
      `;
    }).join('');

    container.innerHTML = htmlContent + cardsHtml;
  } catch (err) {
    console.error(err);
  }
}
