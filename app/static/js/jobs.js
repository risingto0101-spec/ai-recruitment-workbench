let jobsData = [];

function statusBadge(status) {
    const map = {
        open: '<span class="badge badge-open">开放</span>',
        paused: '<span class="badge badge-paused">暂停</span>',
        closed: '<span class="badge badge-closed">关闭</span>'
    };
    return map[status] || status;
}

function fmtSalary(min, max) {
    if (!min && !max) return '面议';
    const a = min ? (min / 1000) + 'K' : '0';
    const b = max ? (max / 1000) + 'K' : '不限';
    return `${a}-${b}`;
}

async function loadJobs() {
    const status = document.getElementById('filter-status').value;
    const url = status ? `/api/jobs?status=${status}` : '/api/jobs';
    try {
        const data = await getJSON(url);
        jobsData = data.items || [];
        renderJobs();
    } catch (e) {
        showToast('加载岗位失败：' + e.message, 'error');
    }
}

function renderJobs() {
    const container = document.getElementById('jobs-table-container');
    if (!jobsData.length) {
        container.innerHTML = '<div class="empty-state">暂无岗位，点击右上角新增岗位</div>';
        return;
    }
    let html = `<table>
        <thead>
            <tr>
                <th>岗位</th>
                <th>部门</th>
                <th>地点</th>
                <th>薪资</th>
                <th>年限</th>
                <th>必需技能</th>
                <th>状态</th>
                <th style="text-align:right">操作</th>
            </tr>
        </thead>
        <tbody>`;
    for (const job of jobsData) {
        const skills = (job.required_skills || []).slice(0, 4).join(' · ');
        const years = job.max_years ? `${job.min_years}-${job.max_years}年` : (job.min_years ? `${job.min_years}年以上` : '不限');
        html += `<tr>
            <td><strong>${escapeHtml(job.title)}</strong></td>
            <td>${escapeHtml(job.department || '-')}</td>
            <td>${escapeHtml(job.location || '-')}</td>
            <td>${fmtSalary(job.salary_min, job.salary_max)}</td>
            <td>${years}</td>
            <td><span class="text-secondary">${escapeHtml(skills || '-')}</span></td>
            <td>${statusBadge(job.status)}</td>
            <td style="text-align:right">
                <button class="btn btn-sm btn-secondary" onclick="editJob(${job.id})">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deleteJob(${job.id})">删除</button>
            </td>
        </tr>`;
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function openJobModal(job = null) {
    document.getElementById('job-id').value = job ? job.id : '';
    document.getElementById('job-modal-title').textContent = job ? '编辑岗位' : '新增岗位';
    document.getElementById('job-title').value = job ? job.title : '';
    document.getElementById('job-department').value = job ? job.department || '' : '';
    document.getElementById('job-location').value = job ? job.location || '' : '';
    document.getElementById('job-salary-min').value = job ? job.salary_min || '' : '';
    document.getElementById('job-salary-max').value = job ? job.salary_max || '' : '';
    document.getElementById('job-min-years').value = job ? job.min_years || '' : '';
    document.getElementById('job-max-years').value = job ? job.max_years || '' : '';
    document.getElementById('job-status').value = job ? job.status : 'open';
    document.getElementById('job-required-skills').value = job ? (job.required_skills || []).join(', ') : '';
    document.getElementById('job-preferred-skills').value = job ? (job.preferred_skills || []).join(', ') : '';
    document.getElementById('job-description').value = job ? job.description || '' : '';
    document.getElementById('job-requirements').value = job ? job.requirements || '' : '';
    document.getElementById('job-modal').classList.add('show');
}

function closeJobModal() {
    document.getElementById('job-modal').classList.remove('show');
}

function parseSkills(input) {
    return input.split(/[,，、]/).map(s => s.trim()).filter(Boolean);
}

async function saveJob() {
    const id = document.getElementById('job-id').value;
    const payload = {
        title: document.getElementById('job-title').value.trim(),
        department: document.getElementById('job-department').value.trim(),
        location: document.getElementById('job-location').value.trim(),
        salary_min: parseInt(document.getElementById('job-salary-min').value) || 0,
        salary_max: parseInt(document.getElementById('job-salary-max').value) || 0,
        min_years: parseInt(document.getElementById('job-min-years').value) || 0,
        max_years: parseInt(document.getElementById('job-max-years').value) || 0,
        status: document.getElementById('job-status').value,
        required_skills: parseSkills(document.getElementById('job-required-skills').value),
        preferred_skills: parseSkills(document.getElementById('job-preferred-skills').value),
        description: document.getElementById('job-description').value.trim(),
        requirements: document.getElementById('job-requirements').value.trim(),
    };
    if (!payload.title) {
        showToast('请填写岗位标题', 'error');
        return;
    }
    try {
        const url = id ? `/api/jobs/${id}` : '/api/jobs';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('保存失败');
        showToast(id ? '岗位已更新' : '岗位已创建', 'success');
        closeJobModal();
        loadJobs();
    } catch (e) {
        showToast('保存失败：' + e.message, 'error');
    }
}

function editJob(id) {
    const job = jobsData.find(j => j.id === id);
    if (job) openJobModal(job);
}

async function deleteJob(id) {
    if (!confirm('确定删除该岗位？关联的匹配记录也会被清除。')) return;
    try {
        await deleteReq(`/api/jobs/${id}`);
        showToast('岗位已删除', 'success');
        loadJobs();
    } catch (e) {
        showToast('删除失败：' + e.message, 'error');
    }
}

function openParseModal() {
    document.getElementById('parse-modal').classList.add('show');
}

function closeParseModal() {
    document.getElementById('parse-modal').classList.remove('show');
}

async function parseJD() {
    const text = document.getElementById('parse-text').value.trim();
    if (!text) {
        showToast('请粘贴 JD 文本', 'error');
        return;
    }
    try {
        const data = await postJSON('/api/jobs/parse', { text });
        const p = data.parsed;
        document.getElementById('job-title').value = p.title || '';
        document.getElementById('job-department').value = p.department || '';
        document.getElementById('job-location').value = p.location || '';
        document.getElementById('job-salary-min').value = p.salary_min || '';
        document.getElementById('job-salary-max').value = p.salary_max || '';
        document.getElementById('job-min-years').value = p.min_years || '';
        document.getElementById('job-max-years').value = p.max_years || '';
        document.getElementById('job-required-skills').value = (p.required_skills || []).join(', ');
        document.getElementById('job-preferred-skills').value = (p.preferred_skills || []).join(', ');
        document.getElementById('job-description').value = p.description || '';
        document.getElementById('job-requirements').value = p.requirements || '';
        closeParseModal();
        document.getElementById('job-modal').classList.add('show');
        showToast('JD 解析完成，请核对后保存', 'success');
    } catch (e) {
        showToast('解析失败：' + e.message, 'error');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadJobs();
    // 在页面头部右侧新增"解析 JD"按钮
    const header = document.querySelector('.page-header');
    if (header && !document.getElementById('btn-parse-jd')) {
        const btn = document.createElement('button');
        btn.id = 'btn-parse-jd';
        btn.className = 'btn btn-secondary';
        btn.textContent = 'AI 解析 JD';
        btn.onclick = openParseModal;
        header.insertBefore(btn, header.children[1]);
    }
});
