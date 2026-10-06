const STATUS_COLORS = {
    new: '#dbeafe',
    contacted: '#fef3c7',
    interviewing: '#e0e7ff',
    offered: '#dcfce7',
    hired: '#d1fae5',
    rejected: '#fee2e2'
};

const STATUS_TEXT_COLORS = {
    new: '#1e40af',
    contacted: '#92400e',
    interviewing: '#3730a3',
    offered: '#166534',
    hired: '#065f46',
    rejected: '#991b1b'
};

const STATUS_LABELS = {
    new: '未联系',
    contacted: '已联系',
    interviewing: '面试中',
    offered: '已发 offer',
    hired: '已入职',
    rejected: '已拒绝'
};

async function loadDashboard() {
    try {
        const data = await getJSON('/api/dashboard');
        document.getElementById('stat-total-jobs').textContent = data.total_jobs;
        document.getElementById('stat-open-jobs').textContent = data.open_jobs;
        document.getElementById('stat-total-candidates').textContent = data.total_candidates;
        document.getElementById('stat-avg-score').textContent = data.avg_match_score.toFixed(1);
        document.getElementById('stat-recent-candidates').textContent = data.recent_candidates;
        document.getElementById('stat-follow-up').textContent = data.follow_up;
        renderStatusChart(data.status_counts || {});
    } catch (e) {
        showToast('加载看板失败：' + e.message, 'error');
    }
}

function renderStatusChart(counts) {
    const container = document.getElementById('status-chart-container');
    const entries = Object.entries(counts).filter(([k, v]) => v > 0);
    if (!entries.length) {
        container.innerHTML = '<div class="empty-state">暂无数据</div>';
        return;
    }
    const total = entries.reduce((sum, [, v]) => sum + v, 0);
    let html = '<div style="display:flex; flex-direction:column; gap:12px">';
    for (const [status, count] of entries) {
        const pct = (count / total) * 100;
        html += `<div style="display:flex; align-items:center; gap:12px">
            <div style="width:80px; font-size:13px; color:var(--text-secondary)">${STATUS_LABELS[status] || status}</div>
            <div style="flex:1; background:#f1f5f9; border-radius:8px; height:24px; overflow:hidden">
                <div style="width:${pct}%; background:${STATUS_COLORS[status] || '#e2e8f0'}; height:100%; border-radius:8px"></div>
            </div>
            <div style="width:60px; text-align:right; font-weight:600; font-size:14px; color:${STATUS_TEXT_COLORS[status] || 'var(--text)'}">${count}</div>
        </div>`;
    }
    html += '</div>';
    container.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', loadDashboard);
