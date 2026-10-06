import os
import sys
import webbrowser
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.config import HOST, PORT, get_base_dir, get_work_dir, is_ai_enabled
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    yield


app = FastAPI(title="AI 招聘工作台", version="1.0.0", lifespan=lifespan)

# 静态资源与模板路径：兼容源码模式和 PyInstaller exe 模式
base_dir = get_base_dir()
static_dir = base_dir / "app" / "static"
templates_dir = base_dir / "app" / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# 延迟导入并注册路由，避免循环依赖
from app.routers import jobs, candidates, matches, dashboard, extension, messages

app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(extension.router, prefix="/api/extension", tags=["extension"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/jobs")


@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    return templates.TemplateResponse("jobs.html", {"request": request})


@app.get("/candidates", response_class=HTMLResponse)
async def candidates_page(request: Request):
    return templates.TemplateResponse("candidates.html", {"request": request})


@app.get("/talent-pool", response_class=HTMLResponse)
async def talent_pool_page(request: Request):
    return templates.TemplateResponse("talent_pool.html", {"request": request})


@app.get("/candidates/{candidate_id}", response_class=HTMLResponse)
async def candidate_detail_page(candidate_id: int, request: Request):
    return templates.TemplateResponse(
        "candidate_detail.html", {"request": request, "candidate_id": candidate_id}
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


def _open_browser():
    try:
        webbrowser.open(f"http://{HOST}:{PORT}/jobs")
    except Exception:
        pass


def run_server(open_browser: bool = True):
    import uvicorn

    if open_browser:
        threading.Timer(1.0, _open_browser).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    run_server()
