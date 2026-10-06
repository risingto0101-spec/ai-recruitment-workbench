import json
import re
from typing import Optional, Dict, Any

import httpx

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, is_ai_enabled


class AIClient:
    def __init__(self):
        self.enabled = is_ai_enabled()
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_BASE_URL.rstrip("/")
        self.model = "deepseek-chat"
        self.timeout = 60.0

    def available(self) -> bool:
        return self.enabled and bool(self.api_key.strip())

    @staticmethod
    def extract_json(text: str) -> Optional[Dict[str, Any]]:
        """从 AI 返回中剥离 markdown 围栏并解析 JSON"""
        if not text:
            return None
        text = text.strip()
        # 去除 ```json ... ```
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if m:
            text = m.group(1).strip()
        # 直接尝试整个文本
        try:
            return json.loads(text)
        except Exception:
            pass
        # 截取第一个 { ... } 或 [ ... ]
        m = re.search(r"(\{[\s\S]*\})", text)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        m = re.search(r"(\[[\s\S]*\])", text)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        return None

    async def _chat(self, messages: list, temperature: float = 0.2) -> Optional[str]:
        if not self.available():
            return None
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 2048,
                }
                resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    async def parse_job(self, text: str) -> Optional[Dict[str, Any]]:
        prompt = f"""请将以下 JD（职位描述）解析为结构化 JSON，字段如下：
- title: 岗位标题
- department: 部门（可选）
- location: 工作地点
- salary_min: 最低月薪（整数，元）
- salary_max: 最高月薪（整数，元）
- required_skills: 必需技能数组
- preferred_skills: 加分技能数组
- min_years: 最低工作年限
- max_years: 最高工作年限（无则为 0）
- description: 岗位描述原文

JD 内容：
{text}

只返回 JSON，不要多余说明。"""
        content = await self._chat([{"role": "user", "content": prompt}])
        parsed = self.extract_json(content) if content else None
        if parsed:
            parsed["parsed_by"] = "ai"
        return parsed

    async def parse_resume(self, text: str) -> Optional[Dict[str, Any]]:
        prompt = f"""请将以下简历内容解析为结构化 JSON，字段如下：
- name: 姓名
- phone: 电话
- email: 邮箱
- current_company: 当前公司
- current_title: 当前职位
- years_of_experience: 工作年限（数字）
- expected_salary_min: 期望最低月薪（整数，元）
- expected_salary_max: 期望最高月薪（整数，元）
- expected_location: 期望工作地点
- skills: 技能数组
- work_history: 工作经历数组，每项包含 company 和 title

简历内容：
{text}

只返回 JSON，不要多余说明。"""
        content = await self._chat([{"role": "user", "content": prompt}])
        parsed = self.extract_json(content) if content else None
        if parsed:
            parsed["parsed_by"] = "ai"
            parsed["raw_text"] = text
        return parsed

    async def match(self, resume: Dict[str, Any], job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        prompt = f"""请评估以下候选人与岗位的匹配度，返回 JSON：
- skill_score: 技能匹配分 0-100
- experience_score: 经验匹配分 0-100
- salary_score: 薪资匹配分 0-100
- location_score: 地点匹配分 0-100
- overall_score: 综合得分 0-100
- reason: 简短匹配理由（50 字以内）

岗位：{json.dumps(job, ensure_ascii=False)}
候选人：{json.dumps(resume, ensure_ascii=False)}

只返回 JSON。"""
        content = await self._chat([{"role": "user", "content": prompt}])
        parsed = self.extract_json(content) if content else None
        return parsed


_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
