const STATUS_LABELS = {
    new: '未联系',
    contacted: '已联系',
    interviewing: '面试中',
    offered: '已发 offer',
    hired: '已入职',
    rejected: '已拒绝'
};

let candidate = null;
let jobsList = [];
const candidateId = document.body.dataset.candidateId || window.location.pathname.split('/').pop();

async function loadCandidate() {
    try {
        candidate = await getJSON(`/api/candidates/${candidateId}`);
        fillForm(candidate);
        document.getElementById('detail-title').textContent = candidate.name + ' - 候选人详情';
        loadMatches();
    } catch (e) {
        showToast('加载详情失败：' + e.message, 'error');
    }
}

function fillForm(c) {
    document.getElementById('c-id').value = c.id;
    document.getElementById('c-name').value = c.name || '';
    document.getElementById('c-phone').value = c.phone || '';
    document.getElementById('c-email').value = c.email || '';
    document.getElementById('c-current-company').value = c.current_company || '';
    document.getElementById('c-current-title').value = c.current_title || '';
    document.getElementById('c-years').value = c.years_of_experience || '';
    document.getElementById('c-salary-min').value = c.expected_salary_min || '';
    document.getElementById('c-salary-max').value = c.expected_salary_max || '';
    document.getElementById('c-expected-location').value = c.expected_location || '';
    document.getElementById('c-skills').value = (c.skills || []).join(', ');
    document.getElementById('c-notes').value = c.notes || '';
    document.getElementById('c-source').value = c.source || '';
    document.getElementById('c-created').value = new Date(c.created_at).toLocaleString('zh-CN');

    const statusSel = document.getElementById('c-status');
    statusSel.innerHTML = Object.entries(STATUS_LABELS).map(([k, v]) =>
        `<option value="${k}" ${c.status === k ? 'selected' : ''}>${v}</option>`
    ).join('');
}

async function loadMatches() {
    try {
        const data = await getJSON(`/api/matches/candidate/${candidateId}`);
        renderMatches(data.items || []);
    } catch (e) {
        showToast('加载匹配失败：' + e.message, 'error');
    }
}

function scoreClass(score) {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-mid';
    return 'score-low';
}

function renderMatches(items) {
    const container = document.getElementById('matches-container');
    if (!items.length) {
        container.innerHTML = '<div class="empty-state">暂无匹配岗位</div>';
        return;
    }
    let html = `<table>
        <thead>
            <tr>
                <th>岗位</th>
                <th>技能分</th>
                <th>经验分</th>
                <th>薪资分</th>
                <th>地点分</th>
                <th>综合分</th>
                <th>匹配理由</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>`;
    for (const m of items) {
        html += `<tr>
            <td><strong>${escapeHtml(m.job_title)}</strong><br><span class="text-secondary">${escapeHtml(m.job_location || '-')}</span></td>
            <td>${m.skill_score.toFixed(1)}</td>
            <td>${m.experience_score.toFixed(1)}</td>
            <td>${m.salary_score.toFixed(1)}</td>
            <td>${m.location_score.toFixed(1)}</td>
            <td><span class="score-badge ${scoreClass(m.overall_score)}">${m.overall_score.toFixed(1)}</span></td>
            <td>${escapeHtml(m.reason)}</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="useForMessage(${m.job_id})">生成话术</button>
            </td>
        </tr>`;
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function saveCandidateChanges() {
    const payload = {
        name: document.getElementById('c-name').value.trim(),
        phone: document.getElementById('c-phone').value.trim(),
        email: document.getElementById('c-email').value.trim(),
        current_company: document.getElementById('c-current-company').value.trim(),
        current_title: document.getElementById('c-current-title').value.trim(),
        years_of_experience: parseFloat(document.getElementById('c-years').value) || 0,
        expected_salary_min: parseInt(document.getElementById('c-salary-min').value) || 0,
        expected_salary_max: parseInt(document.getElementById('c-salary-max').value) || 0,
        expected_location: document.getElementById('c-expected-location').value.trim(),
        skills: document.getElementById('c-skills').value.split(/[,，、]/).map(s => s.trim()).filter(Boolean),
        status: document.getElementById('c-status').value,
        notes: document.getElementById('c-notes').value.trim(),
    };
    try {
        await fetch(`/api/candidates/${candidateId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        showToast('已保存', 'success');
        loadCandidate();
    } catch (e) {
        showToast('保存失败：' + e.message, 'error');
    }
}

async function loadJobsForMessage() {
    try {
        const data = await getJSON('/api/jobs');
        jobsList = data.items || [];
        const sel = document.getElementById('msg-job');
        sel.innerHTML = '<option value="">选择岗位</option>' + jobsList.map(j =>
            `<option value="${j.id}">${escapeHtml(j.title)}</option>`
        ).join('');
    } catch (e) {
        console.error('加载岗位失败', e);
    }
}

function useForMessage(jobId) {
    document.getElementById('msg-job').value = jobId;
}

async function generateMessage() {
    const jobId = document.getElementById('msg-job').value;
    const category = document.getElementById('msg-category').value;
    if (!jobId) {
        showToast('请选择岗位', 'error');
        return;
    }
    try {
        const data = await postJSON('/api/messages/generate', {
            candidate_id: parseInt(candidateId),
            job_id: parseInt(jobId),
            category: category
        });
        document.getElementById('msg-result').value = data.message;
    } catch (e) {
        showToast('生成失败：' + e.message, 'error');
    }
}

function copyMessage() {
    const el = document.getElementById('msg-result');
    el.select();
    document.execCommand('copy');
    showToast('已复制', 'success');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
    loadJobsForMessage();
    loadCandidate();
});
