let parsedCandidate = null;
let jobsList = [];

function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
    document.querySelector(`.tab[data-tab="${tab}"]`).classList.add('active');
    document.getElementById('panel-text').style.display = tab === 'text' ? 'block' : 'none';
    document.getElementById('panel-file').style.display = tab === 'file' ? 'block' : 'none';
}

async function loadJobsForSelect() {
    try {
        const data = await getJSON('/api/jobs');
        jobsList = data.items || [];
        const sel = document.getElementById('c-intended-job');
        sel.innerHTML = '<option value="">暂无</option>' + jobsList.map(j => `<option value="${j.id}">${escapeHtml(j.title)}</option>`).join('');
    } catch (e) {
        console.error('加载岗位失败', e);
    }
}

async function parseCandidateText() {
    const text = document.getElementById('candidate-text').value.trim();
    if (!text || text.length < 10) {
        showToast('请粘贴至少 10 个字符的简历文本', 'error');
        return;
    }
    try {
        const data = await postJSON('/api/candidates/parse-text', { text });
        parsedCandidate = data.parsed;
        parsedCandidate.source = 'manual';
        fillPreview(parsedCandidate);
        showToast('解析完成，请核对后保存', 'success');
    } catch (e) {
        showToast('解析失败：' + e.message, 'error');
    }
}

async function uploadFile(input) {
    const file = input.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', 'upload');
    try {
        const res = await fetch('/api/candidates/upload', { method: 'POST', body: formData });
        if (!res.ok) throw new Error('上传失败');
        const data = await res.json();
        parsedCandidate = data.candidate;
        fillPreview(parsedCandidate);
        document.getElementById('upload-result').innerHTML = `<div style="margin-top:10px;color:var(--success)">已解析：${escapeHtml(file.name)}</div>`;
        showToast('文件解析完成', 'success');
    } catch (e) {
        showToast('文件解析失败：' + e.message, 'error');
    }
}

function fillPreview(data) {
    document.getElementById('preview-card').style.display = 'block';
    document.getElementById('candidate-id').value = data.id || '';
    document.getElementById('c-name').value = data.name || '';
    document.getElementById('c-phone').value = data.phone || '';
    document.getElementById('c-email').value = data.email || '';
    document.getElementById('c-current-company').value = data.current_company || '';
    document.getElementById('c-current-title').value = data.current_title || '';
    document.getElementById('c-years').value = data.years_of_experience || '';
    document.getElementById('c-salary-min').value = data.expected_salary_min || '';
    document.getElementById('c-salary-max').value = data.expected_salary_max || '';
    document.getElementById('c-expected-location').value = data.expected_location || '';
    document.getElementById('c-skills').value = (data.skills || []).join(', ');
    document.getElementById('c-raw-text').value = data.raw_text || '';
    document.getElementById('c-notes').value = data.notes || '';
    document.getElementById('c-source').value = data.source || 'manual';
    document.getElementById('c-intended-job').value = data.intended_job_id || '';
    window.scrollTo({ top: document.getElementById('preview-card').offsetTop - 20, behavior: 'smooth' });
}

function collectCandidatePayload() {
    return {
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
        raw_text: document.getElementById('c-raw-text').value.trim(),
        source: document.getElementById('c-source').value,
        status: 'new',
        intended_job_id: parseInt(document.getElementById('c-intended-job').value) || null,
        notes: document.getElementById('c-notes').value.trim(),
    };
}

async function saveCandidate() {
    const id = document.getElementById('candidate-id').value;
    const payload = collectCandidatePayload();
    if (!payload.name) {
        showToast('请填写姓名', 'error');
        return;
    }
    try {
        const url = id ? `/api/candidates/${id}` : '/api/candidates';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('保存失败');
        const data = await res.json();
        showToast('候选人已保存，匹配结果已生成', 'success');
        setTimeout(() => window.location.href = `/candidates/${data.id}`, 600);
    } catch (e) {
        showToast('保存失败：' + e.message, 'error');
    }
}

function resetPreview() {
    parsedCandidate = null;
    document.getElementById('candidate-form').reset();
    document.getElementById('preview-card').style.display = 'none';
    document.getElementById('candidate-text').value = '';
    document.getElementById('upload-result').innerHTML = '';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 拖拽上传
document.addEventListener('DOMContentLoaded', () => {
    loadJobsForSelect();
    const zone = document.getElementById('upload-zone');
    if (zone) {
        zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
        zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length) {
                document.getElementById('candidate-file').files = files;
                uploadFile(document.getElementById('candidate-file'));
            }
        });
    }
});
