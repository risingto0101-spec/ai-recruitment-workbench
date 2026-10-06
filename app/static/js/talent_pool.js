let talentData = [];
let jobsList = [];
let loadTimer = null;

const STATUS_LABELS = {
    new: '未联系',
    contacted: '已联系',
    interviewing: '面试中',
    offered: '已发 offer',
    hired: '已入职',
    rejected: '已拒绝'
};

const SOURCE_LABELS = {
    manual: '手动',
    upload: '上传',
    plugin: '插件'
};

function statusBadge(status) {
    const map = {
        new: '<span class="badge badge-new">未联系</span>',
        contacted: '<span class="badge badge-contacted">已联系</span>',
        interviewing: '<span class="badge badge-interviewing">面试中</span>',
        offered: '<span class="badge badge-offered">已发 offer</span>',
        hired: '<span class="badge badge-hired">已入职</span>',
        rejected: '<span class="badge badge-rejected">已拒绝</span>'
    };
    return map[status] || status;
}

function scoreClass(score) {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-mid';
    return 'score-low';
}

function daysSince(iso) {
    if (!iso) return 999;
    const then = new Date(iso);
    const now = new Date();
    return Math.floor((now - then) / (1000 * 60 * 60 * 24));
}

function rowHighlight(updatedAt) {
    const d = daysSince(updatedAt);
    if (d <= 7) return 'row-highlight-green';
    if (d <= 14) return 'row-highlight-yellow';
    return 'row-highlight-red';
}

async function loadJobs() {
    try {
        const data = await getJSON('/api/jobs');
        jobsList = data.items || [];
        const sel = document.getElementById('filter-job');
        sel.innerHTML = '<option value="">全部岗位</option>' + jobsList.map(j => `<option value="${j.id}">${escapeHtml(j.title)}</option>`).join('');
    } catch (e) {
        console.error('加载岗位失败', e);
    }
}

function buildQuery() {
    const params = new URLSearchParams();
    const status = document.getElementById('filter-status').value;
    const job = document.getElementById('filter-job').value;
    const source = document.getElementById('filter-source').value;
    const score = document.getElementById('filter-score-min').value;
    const q = document.getElementById('filter-q').value.trim();
    if (status) params.set('status', status);
    if (job) params.set('job_id', job);
    if (source) params.set('source', source);
    if (score) params.set('min_score', score);
    if (q) params.set('q', q);
    return params.toString();
}

function debounceLoadTalentPool() {
    clearTimeout(loadTimer);
    loadTimer = setTimeout(loadTalentPool, 300);
}

async function loadTalentPool() {
    const query = buildQuery();
    const url = '/api/candidates' + (query ? '?' + query : '');
    try {
        const data = await getJSON(url);
        talentData = data.items || [];
        renderTalentPool();
    } catch (e) {
        showToast('加载人才库失败：' + e.message, 'error');
    }
}

function renderTalentPool() {
    const container = document.getElementById('talent-table-container');
    if (!talentData.length) {
        container.innerHTML = '<div class="empty-state">暂无候选人</div>';
        return;
    }
    let html = `<table>
        <thead>
            <tr>
                <th>姓名</th>
                <th>当前公司/职位</th>
                <th>技能</th>
                <th>来源</th>
                <th>最高匹配岗位</th>
                <th>综合分</th>
                <th>状态</th>
                <th>更新时间</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>`;
    for (const c of talentData) {
        const score = c.best_score || 0;
        const scoreHtml = score > 0 ? `<span class="score-badge ${scoreClass(score)}">${score.toFixed(1)}</span>` : '-';
        const hlClass = rowHighlight(c.status_updated_at || c.updated_at);
        const updateDays = daysSince(c.status_updated_at || c.updated_at);
        const daysLabel = updateDays === 0 ? '今天' : `${updateDays}天前`;
        html += `<tr class="${hlClass}">
            <td><a href="/candidates/${c.id}"><strong>${escapeHtml(c.name)}</strong></a></td>
            <td>${escapeHtml(c.current_company || '-')}<br><span class="text-secondary">${escapeHtml(c.current_title || '-')}</span></td>
            <td><span class="text-secondary">${escapeHtml((c.skills || []).slice(0, 5).join(' · '))}</span></td>
            <td>${SOURCE_LABELS[c.source] || c.source}</td>
            <td>${escapeHtml(c.best_job_title || '暂无')}</td>
            <td>${scoreHtml}</td>
            <td>${statusSelect(c.id, c.status)}</td>
            <td><span class="text-secondary">${daysLabel}</span></td>
            <td>
                <a class="btn btn-sm btn-secondary" href="/candidates/${c.id}">详情</a>
                <button class="btn btn-sm btn-danger" onclick="deleteCandidate(${c.id})">删除</button>
            </td>
        </tr>`;
    }
    html += '</tbody></table>';
    container.innerHTML = html;
    // 绑定状态选择事件
    document.querySelectorAll('.status-select').forEach(sel => {
        sel.addEventListener('change', async () => {
            const id = sel.dataset.id;
            const status = sel.value;
            try {
                await fetch(`/api/candidates/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status })
                });
                showToast('状态已更新', 'success');
                loadTalentPool();
            } catch (e) {
                showToast('状态更新失败：' + e.message, 'error');
            }
        });
    });
}

function statusSelect(id, status) {
    let html = `<select class="form-select status-select" data-id="${id}">`;
    for (const [k, v] of Object.entries(STATUS_LABELS)) {
        html += `<option value="${k}" ${k === status ? 'selected' : ''}>${v}</option>`;
    }
    html += '</select>';
    return html;
}

async function deleteCandidate(id) {
    if (!confirm('确定删除该候选人？')) return;
    try {
        await deleteReq(`/api/candidates/${id}`);
        showToast('已删除', 'success');
        loadTalentPool();
    } catch (e) {
        showToast('删除失败：' + e.message, 'error');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
    loadJobs().then(loadTalentPool);
});
