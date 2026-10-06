import re
import json
from typing import List, Dict, Any, Optional


COMMON_SKILLS = {
    "python", "java", "go", "golang", "c++", "c#", "javascript", "js", "typescript", "ts",
    "vue", "react", "angular", "node", "nodejs", "nextjs", "django", "flask", "spring",
    "mysql", "postgresql", "redis", "mongodb", "elasticsearch", "kafka", "rabbitmq",
    "docker", "kubernetes", "k8s", "linux", "nginx", "git", "aws", "azure", "gcp",
    "tensorflow", "pytorch", "机器学习", "深度学习", "nlp", "cv", "数据分析",
    "产品", "运营", "测试", "测试开发", "自动化测试", "selenium", "appium",
    "产品经理", "项目经理", "ui", "ux", "设计", "figma", "sketch",
    "excel", "sql", "spss", "tableau", "power bi", "bi",
    "html", "css", "前端", "后端", "全栈", "爬虫", "大数据", "spark", "hadoop",
    "flutter", "react native", "ios", "android", "swift", "kotlin"
}

LOCATION_KEYWORDS = [
    "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "苏州",
    "重庆", "天津", "长沙", "郑州", "青岛", "大连", "宁波", "厦门", "无锡", "佛山",
    "东莞", "福州", "合肥", "昆明", "哈尔滨", "长春", "沈阳", "济南", "石家庄", "太原",
    "remote", "远程", "居家办公", "居家"
]


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_salary(text: str) -> tuple:
    """从文本中提取薪资范围，返回 (min, max, currency)"""
    if not text:
        return 0, 0, "CNY"
    text = text.lower()
    # 匹配 "15k-25k", "15-25k", "15k-25k/月", "年薪 20-30 万" 等
    patterns = [
        r"(\d+)\s*[k千]?\s*[-~]\s*(\d+)\s*[k千]?(?:/月)?",
        r"月薪\s*(\d+)\s*[-~]\s*(\d+)",
        r"薪资\s*(\d+)\s*[-~]\s*(\d+)",
        r"(\d+)\s*-\s*(\d+)\s*k",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            # 统一换算为月薪（元）
            if a < 1000:
                a *= 1000
            if b < 1000:
                b *= 1000
            return min(a, b), max(a, b), "CNY"
    return 0, 0, "CNY"


def _extract_years(text: str) -> tuple:
    """从文本中提取工作年限要求，返回 (min, max)"""
    if not text:
        return 0, 0
    text = text.lower()
    # "3-5年", "3年以上", "5年以下", "经验不限"
    m = re.search(r"(\d+)\s*(?:-|~|到)\s*(\d+)\s*年", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)\s*年(?:及)?以[上内]", text)
    if m:
        return int(m.group(1)), 0
    m = re.search(r"(\d+)\s*年以下", text)
    if m:
        return 0, int(m.group(1))
    if re.search(r"经验不限|不限经验|应届生|应届", text):
        return 0, 0
    return 0, 0


def _extract_location(text: str) -> str:
    """从文本中提取地点"""
    if not text:
        return ""
    # 优先匹配 "地点：北京" 或 "base：上海"
    m = re.search(r"(?:地点|base|工作地|工作地点|城市)[：:]\s*([\u4e00-\u9fa5]{2,10})", text)
    if m:
        return m.group(1)
    # 否则扫描已知城市
    for loc in LOCATION_KEYWORDS:
        if loc in text:
            return loc
    return ""


def _extract_skills(text: str) -> List[str]:
    """从文本中提取技能关键词"""
    if not text:
        return []
    text = text.lower()
    found = []
    # 按长度降序匹配，避免短词覆盖长词；中文环境下用 in 更稳定
    for skill in sorted(COMMON_SKILLS, key=len, reverse=True):
        if skill in text:
            found.append(skill)
            # 替换掉避免再次命中子串（如 python 命中后不再被命中）
            text = text.replace(skill, "")
    return found


def _extract_title(text: str) -> str:
    """从文本第一行提取岗位标题"""
    lines = [l.strip() for l in _clean_text(text).split("\n") if l.strip()]
    if not lines:
        return "未命名岗位"
    first = lines[0]
    # 如果第一行是标题且不太长
    if len(first) < 50 and not first.startswith("岗位职责") and not first.startswith("职位"):
        return first
    # 尝试从 "职位：XX" 提取
    m = re.search(r"(?:职位|岗位|招聘)[：:]\s*([^\n]{2,30})", text)
    if m:
        return m.group(1).strip()
    return "未命名岗位"


def _extract_department(text: str) -> str:
    """提取部门"""
    m = re.search(r"(?:部门|事业部)[：:]\s*([^\n]{2,20})", text)
    if m:
        return m.group(1).strip()
    return ""


def parse_job(text: str) -> Dict[str, Any]:
    """规则引擎解析 JD 文本"""
    text = _clean_text(text)
    title = _extract_title(text)
    salary_min, salary_max, currency = _extract_salary(text)
    min_years, max_years = _extract_years(text)
    location = _extract_location(text)
    department = _extract_department(text)
    skills = _extract_skills(text)

    # 简单区分 required 和 preferred：出现在"加分项""优先""熟悉" 的为 preferred
    lower = text.lower()
    preferred_idx = lower.find("优先")
    bonus_idx = lower.find("加分")
    req_skills = []
    pref_skills = []
    for s in skills:
        pos = lower.find(s)
        if pos >= 0 and (
            (preferred_idx >= 0 and pos > preferred_idx)
            or (bonus_idx >= 0 and pos > bonus_idx)
        ):
            pref_skills.append(s)
        else:
            req_skills.append(s)

    return {
        "title": title,
        "department": department,
        "location": location,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": currency,
        "description": text,
        "requirements": text,
        "required_skills": req_skills,
        "preferred_skills": pref_skills,
        "min_years": min_years,
        "max_years": max_years,
        "status": "open",
        "parsed_by": "rule_engine",
    }


def _extract_name(text: str) -> str:
    if not text:
        return ""
    text = _clean_text(text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # 常见简历第一行是姓名
    if lines and len(lines[0]) <= 10 and not any(k in lines[0] for k in ["简历", "姓名", "求职"]):
        return lines[0]
    # 从 "姓名：张三" 提取
    m = re.search(r"(?:姓名|名字)[：:]\s*([^\n\s]{2,10})", text)
    if m:
        return m.group(1).strip()
    # 从 "张三，138..." 或 "张三 | 138..." 提取中文姓名
    m = re.search(r"^([^\na-zA-Z0-9，,|｜]{2,4})[，,|｜\s]+1[3-9]\d{9}", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return ""


def _extract_phone(text: str) -> str:
    m = re.search(r"1[3-9]\d{9}", text)
    if m:
        return m.group(0)
    return ""


def _extract_email(text: str) -> str:
    m = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    if m:
        return m.group(0)
    return ""


def _extract_work_history(text: str) -> List[Dict[str, Any]]:
    """简单提取工作经历"""
    history = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for i, line in enumerate(lines):
        m = re.match(r"^([^\d]{2,20})\s*[|│]\s*(.{2,30})$", line)
        if m:
            history.append({"company": m.group(1).strip(), "title": m.group(2).strip()})
    return history


def _extract_years_experience(text: str) -> float:
    """从简历中提取工作年限"""
    if not text:
        return 0.0
    # 工作5年、工作 5 年、5年经验、5 年以上经验
    patterns = [
        r"工作\s*(\d+(?:\.\d+)?)\s*年",
        r"(\d+(?:\.\d+)?)\s*年(?:及)?以[上内]?(?:工作经验|经验)?",
        r"工作年限?[：:]\s*(\d+(?:\.\d+)?)\s*年",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return float(m.group(1))
    # 根据毕业年份估算
    m = re.search(r"(20\d{2})\s*年\s*毕业", text)
    if m:
        from datetime import datetime
        year = int(m.group(1))
        exp = datetime.now().year - year
        return max(0, exp - 1)
    return 0.0


TITLE_SUFFIXES = [
    "工程师", "开发", "经理", "主管", "总监", "专员", "设计师", "产品经理", "项目经理",
    "运营", "测试", "架构师", "负责人", "顾问", "分析师", "副总裁", "VP", "CTO", "CEO"
]

TITLE_PREFIXES = ["初级", "中级", "高级", "资深", "主任", "首席"]

TITLE_DIRECTIONS = ["前端", "后端", "全栈", "客户端", "服务端", "大数据", "算法", "java", "python", "go"]

COMPANY_SUFFIXES = ["有限公司", "集团", "科技", "网络", "信息", "互联网", "公司"]


def _move_tail_words_to_title(company: str, title: str) -> tuple:
    """把 company 末尾的职位修饰词/方向词移到 title 前"""
    while company:
        # 优先吞掉方向词
        moved = False
        for word in sorted(TITLE_DIRECTIONS, key=len, reverse=True):
            if company.endswith(word):
                title = word + title
                company = company[:-len(word)].strip()
                moved = True
                break
        if moved:
            continue
        # 再吞掉前缀
        for word in sorted(TITLE_PREFIXES, key=len, reverse=True):
            if company.endswith(word):
                title = word + title
                company = company[:-len(word)].strip()
                moved = True
                break
        if not moved:
            break
    return company, title


def _split_title_from_company(full: str) -> tuple:
    """从公司+职位字符串中拆分出职位，返回 (company, title)"""
    # 按常见公司后缀优先切分
    for cs in sorted(COMPANY_SUFFIXES, key=len, reverse=True):
        idx = full.find(cs)
        if idx >= 0:
            company = full[:idx + len(cs)].strip()
            title = full[idx + len(cs):].strip()
            if title:
                return company, title
    # 否则从后往前找职位后缀
    for suffix in sorted(TITLE_SUFFIXES, key=len, reverse=True):
        idx = full.rfind(suffix)
        if idx < 0:
            continue
        title = full[idx:].strip()
        company = full[:idx].strip()
        company, title = _move_tail_words_to_title(company, title)
        return company, title
    return full, ""


def _extract_current_company_and_title(text: str) -> tuple:
    """提取当前公司与职位，返回 (company, title)"""
    # 模式：现任字节跳动高级后端开发 -> 从右向左切分职位
    m = re.search(r"现任\s*([^，,|｜\n]{2,40})", text)
    if m:
        return _split_title_from_company(m.group(1).strip())
    # 模式：目前就职于 XX 公司，担任 XX
    m = re.search(r"目前就职于\s*([^，,|｜\s]{2,40})", text)
    if m:
        company = m.group(1).strip()
        m2 = re.search(r"担任\s*([^，,|｜\n]{2,40})", text)
        title = m2.group(1).strip() if m2 else ""
        return company, title
    # 模式：公司 | 职位
    m = re.search(r"(?:目前公司|当前公司|公司)[：:]\s*([^\n]{2,40})", text)
    if m:
        company = m.group(1).strip()
        m2 = re.search(r"(?:目前职位|当前职位|职位)[：:]\s*([^\n]{2,40})", text)
        title = m2.group(1).strip() if m2 else ""
        return company, title
    return "", ""


def parse_resume(text: str) -> Dict[str, Any]:
    """规则引擎解析简历文本"""
    text = _clean_text(text)
    name = _extract_name(text)
    phone = _extract_phone(text)
    email = _extract_email(text)
    skills = _extract_skills(text)
    location = _extract_location(text)
    years = _extract_years_experience(text)
    work_history = _extract_work_history(text)

    # 当前公司与职位
    current_company, current_title = _extract_current_company_and_title(text)
    if not current_company and work_history:
        current_company = work_history[0].get("company", "")
        current_title = work_history[0].get("title", "")

    salary_min, salary_max, _ = _extract_salary(text)

    return {
        "name": name or "未命名候选人",
        "phone": phone,
        "email": email,
        "current_company": current_company,
        "current_title": current_title,
        "years_of_experience": years,
        "expected_salary_min": salary_min,
        "expected_salary_max": salary_max,
        "expected_location": location,
        "skills": skills,
        "education": [],
        "work_history": work_history,
        "raw_text": text,
        "source": "manual",
        "status": "new",
        "notes": "",
        "parsed_by": "rule_engine",
    }


def _skill_match_score(candidate_skills: List[str], job_skills: List[str]) -> float:
    if not job_skills:
        return 60.0  # 没有明确要求时给及格分
    if not candidate_skills:
        return 0.0
    cset = set(k.lower() for k in candidate_skills)
    jset = set(k.lower() for k in job_skills)
    matched = len(cset & jset)
    return min(100.0, round((matched / len(jset)) * 100, 1))


def _experience_match_score(years: float, min_years: int, max_years: int) -> float:
    if min_years <= 0 and max_years <= 0:
        return 80.0
    if max_years > 0:
        if years < min_years:
            return max(0, 100 - (min_years - years) * 25)
        if years > max_years * 1.5:
            return max(40, 100 - (years - max_years) * 10)
        return 100.0
    # 只有 min_years
    if years >= min_years:
        return 100.0
    return max(0, 100 - (min_years - years) * 20)


def _salary_match_score(
    cand_min: int, cand_max: int, job_min: int, job_max: int
) -> float:
    if job_min <= 0 and job_max <= 0:
        return 80.0
    if cand_max <= 0:
        return 70.0  # 未明确期望
    # 岗位区间与候选区间重叠程度
    lower = max(job_min, cand_min)
    upper = min(job_max, cand_max)
    if upper <= 0:
        # 无重叠：看偏离程度
        if cand_max < job_min:
            gap = job_min - cand_max
            return max(0, 100 - gap / max(job_min, 1) * 100)
        else:
            gap = cand_min - job_max
            return max(0, 100 - gap / max(job_max, 1) * 100)
    overlap = upper - lower
    span = max(job_max - job_min, 1)
    return min(100, round((overlap / span) * 100 + 10, 1))


def _location_match_score(cand_loc: str, job_loc: str) -> float:
    if not job_loc:
        return 80.0
    if not cand_loc:
        return 60.0
    c = cand_loc.lower()
    j = job_loc.lower()
    if c == j or j in c or c in j:
        return 100.0
    if "远程" in c or "remote" in c:
        return 90.0
    return 30.0


def calculate_match(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """规则引擎计算匹配分数"""
    req_skills = job.get("required_skills") or []
    cand_skills = candidate.get("skills") or []
    skill_score = _skill_match_score(cand_skills, req_skills)
    # 如果有加分技能则适当提升
    pref_skills = job.get("preferred_skills") or []
    if pref_skills:
        pref_score = _skill_match_score(cand_skills, pref_skills)
        skill_score = min(100, skill_score + pref_score * 0.15)

    experience_score = _experience_match_score(
        candidate.get("years_of_experience", 0) or 0,
        job.get("min_years", 0) or 0,
        job.get("max_years", 0) or 0,
    )

    salary_score = _salary_match_score(
        candidate.get("expected_salary_min", 0) or 0,
        candidate.get("expected_salary_max", 0) or 0,
        job.get("salary_min", 0) or 0,
        job.get("salary_max", 0) or 0,
    )

    location_score = _location_match_score(
        candidate.get("expected_location", ""),
        job.get("location", ""),
    )

    weights = {"skill": 0.4, "experience": 0.25, "salary": 0.2, "location": 0.15}
    overall = round(
        skill_score * weights["skill"]
        + experience_score * weights["experience"]
        + salary_score * weights["salary"]
        + location_score * weights["location"],
        1,
    )

    reason_parts = []
    if skill_score >= 80:
        reason_parts.append("技能匹配度高")
    elif skill_score < 50:
        reason_parts.append("核心技能不足")
    if experience_score >= 80:
        reason_parts.append("经验符合")
    if salary_score >= 80:
        reason_parts.append("薪资匹配")
    if location_score >= 80:
        reason_parts.append("地点合适")
    reason = "，".join(reason_parts) or "综合匹配一般"

    return {
        "skill_score": round(skill_score, 1),
        "experience_score": round(experience_score, 1),
        "salary_score": round(salary_score, 1),
        "location_score": round(location_score, 1),
        "overall_score": overall,
        "reason": reason,
    }
