const SERVER_URL = 'http://127.0.0.1:8000/api/extension/push';

let currentTab = null;
let pageSource = 'manual';

document.addEventListener('DOMContentLoaded', async () => {
    const statusEl = document.getElementById('status');
    const infoEl = document.getElementById('page-info');
    const pushBtn = document.getElementById('push-btn');

    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        currentTab = tab;
        const host = new URL(tab.url).hostname;
        if (host.includes('zhipin.com')) {
            pageSource = 'boss';
            infoEl.textContent = '已识别：BOSS 直聘';
            pushBtn.disabled = false;
        } else if (host.includes('51job.com')) {
            pageSource = '51job';
            infoEl.textContent = '已识别：前程无忧';
            pushBtn.disabled = false;
        } else {
            infoEl.textContent = '当前页面不是 BOSS 直聘或前程无忧，仍可手动推送正文';
            pushBtn.disabled = false;
        }
    } catch (e) {
        infoEl.textContent = '无法识别当前页面';
        statusEl.textContent = '错误：' + e.message;
        statusEl.className = 'status error';
    }

    pushBtn.addEventListener('click', async () => {
        pushBtn.disabled = true;
        pushBtn.textContent = '抓取中...';
        statusEl.className = 'status info';
        statusEl.textContent = '正在抓取页面内容...';

        try {
            const results = await chrome.scripting.executeScript({
                target: { tabId: currentTab.id },
                func: grabPageText,
            });
            const pageText = results[0]?.result?.text || '';
            const title = results[0]?.result?.title || currentTab.title || '';
            if (!pageText || pageText.length < 30) {
                throw new Error('页面正文太短，无法解析');
            }

            statusEl.textContent = '正在推送到工作台...';
            const res = await fetch(SERVER_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source: pageSource,
                    url: currentTab.url,
                    title: title,
                    content: pageText,
                })
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || '推送失败');
            }
            const data = await res.json();
            statusEl.className = 'status success';
            statusEl.textContent = `推送成功：${data.candidate?.name || '候选人'} 已保存`;
        } catch (e) {
            statusEl.className = 'status error';
            statusEl.textContent = '失败：' + e.message;
        } finally {
            pushBtn.disabled = false;
            pushBtn.textContent = '一键推送简历';
        }
    });
});

function grabPageText() {
    const title = document.title || '';
    // 移除脚本、样式、导航等噪音
    const clone = document.body.cloneNode(true);
    const noise = clone.querySelectorAll('script, style, nav, header, footer, aside, .sidebar, .recommend, .ad, .ads');
    noise.forEach(el => el.remove());
    const text = clone.innerText || clone.textContent || '';
    return { title, text: text.trim().replace(/\s{2,}/g, '\n').substring(0, 20000) };
}
