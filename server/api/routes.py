import sys
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import Integer
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from server.auth.jwt import create_access_token, get_current_device
import uuid
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.responses import StreamingResponse
import csv
import io
import httpx
from functools import lru_cache
import bcrypt

limiter = Limiter(key_func=get_remote_address)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from server.database.db_manager import get_db
from server.database.models import User, Device, ActivityLog
from server.auth.jwt import create_access_token

router = APIRouter()

@lru_cache(maxsize=500)
def classify_activity(app_name: str, window_title: str) -> str:
    prompt = f"""Classify this computer activity into exactly one category.
App: {app_name}
Window Title: {window_title}

Categories to choose from:
- Teams Meeting
- Communication
- Development
- Browser - Work
- Browser - Entertainment
- Documents
- System
- Other

Reply with only the category name, nothing else."""

    try:
        response = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            params={"key": os.environ.get("GEMINI_API_KEY", "")},
            json={
                "contents": [{"parts": [{"text": prompt}]}]
            },
            timeout=5.0
        )
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return "Other"
# Request models
class RegisterRequest(BaseModel):
    device_name: str
    username: str
    department: Optional[str] = None

class LogEntry(BaseModel):
    app_name: str
    window_title: str
    start_time: datetime
    end_time: datetime
    duration: int
    is_idle: bool
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    upload_kb: Optional[float] = None
    download_kb: Optional[float] = None

class UploadRequest(BaseModel):
    device_id: str
    logs: List[LogEntry]

# Routes
@router.post("/api/client/register")
def register_client(request: RegisterRequest, db: Session = Depends(get_db)):
    # create or get user
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        user = User(username=request.username, department=request.department)
        db.add(user)
        db.commit()
        db.refresh(user)

    # check if device already exists
    device = db.query(Device).filter(
        Device.device_name == request.device_name,
        Device.user_id == user.id
    ).first()

    if not device:
        device = Device(device_name=request.device_name, user_id=user.id)
        db.add(device)
        db.commit()
        db.refresh(device)

    # generate token
    token = create_access_token({"device_id": str(device.id), "username": user.username})

    return {"device_id": str(device.id), "token": token}
@router.post("/api/logs/upload")
@limiter.limit("60/minute")
def upload_logs(request: Request, body: UploadRequest, db: Session = Depends(get_db), current_device: dict = Depends(get_current_device)):
    device = db.query(Device).filter(Device.id == uuid.UUID(body.device_id)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    for log in body.logs:
        activity = ActivityLog(
            device_id=device.id,
            app_name=log.app_name,
            window_title=log.window_title,
            start_time=log.start_time,
            end_time=log.end_time,
            duration=log.duration,
            is_idle=log.is_idle,
            cpu_usage=log.cpu_usage,
            memory_usage=log.memory_usage,
            disk_usage=log.disk_usage,
            upload_kb=log.upload_kb,
            download_kb=log.download_kb
        )
        db.add(activity)

    device.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return {"status": "success", "records_saved": len(body.logs)}

@router.get("/api/health")
def health_check():
    return {"status": "ok"}

@router.get("/api/analytics/top-apps")
def get_top_apps(device_id: Optional[str] = None, period: Optional[str] = None, db: Session = Depends(get_db)):
    from sqlalchemy import func
    from datetime import datetime, timedelta

    query = db.query(
        ActivityLog.app_name,
        func.sum(ActivityLog.duration).label("total_duration")
    )

    if device_id:
        query = query.filter(ActivityLog.device_id == uuid.UUID(device_id))

    # Filter by period
    if period == "day":
        cutoff = datetime.now() - timedelta(days=1)
        query = query.filter(ActivityLog.start_time >= cutoff)
    elif period == "week":
        cutoff = datetime.now() - timedelta(weeks=1)
        query = query.filter(ActivityLog.start_time >= cutoff)
    elif period == "month":
        cutoff = datetime.now() - timedelta(days=30)
        query = query.filter(ActivityLog.start_time >= cutoff)
    # if period is None or anything else, no date filter (all time)

    results = query.group_by(ActivityLog.app_name).order_by(func.sum(ActivityLog.duration).desc()).limit(10).all()
    return [{"app_name": r.app_name, "total_duration": r.total_duration} for r in results]

@router.get("/api/analytics/overview")
def get_overview(device_id: Optional[str] = None, db: Session = Depends(get_db)):
    from sqlalchemy import func, cast, Date
    from datetime import date
    
    query = db.query(ActivityLog)
    if device_id:
        query = query.filter(ActivityLog.device_id == uuid.UUID(device_id))
    
    total_logs = query.count()
    total_duration = query.with_entities(func.sum(ActivityLog.duration)).scalar() or 0
    total_devices = db.query(func.count(Device.id)).scalar()
    idle_count = query.filter(ActivityLog.is_idle == True).count()
    
    # active users today
    today = date.today()
    active_users_today = db.query(func.count(func.distinct(Device.user_id))).join(
        ActivityLog, ActivityLog.device_id == Device.id
    ).filter(
        cast(ActivityLog.start_time, Date) == today
    ).scalar() or 0
    total_apps = query.with_entities(func.count(func.distinct(ActivityLog.app_name))).scalar() or 0
    
    return {
    "total_logs": total_logs,
    "total_duration_hours": round(total_duration / 3600, 2),
    "total_devices": total_devices,
    "idle_count": idle_count,
    "active_users_today": active_users_today,
    "total_apps": total_apps
}

@router.get("/api/devices")
def get_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return [{"id": str(d.id), "device_name": d.device_name, "last_seen": str(d.last_seen)} for d in devices]

@router.get("/api/analytics/resources")
def get_resources(device_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ActivityLog)
    if device_id:
        query = query.filter(ActivityLog.device_id == uuid.UUID(device_id))
    
    results = query.order_by(ActivityLog.end_time.desc()).limit(50).all()

    return [{
        "time": r.start_time.strftime("%H:%M"),
        "cpu": round(r.cpu_usage or 0, 1),
        "memory": round(r.memory_usage or 0, 1),
        "disk": round(r.disk_usage or 0, 1),
        "upload": round(r.upload_kb or 0, 1),
        "download": round(r.download_kb or 0, 1)
    } for r in results]
@router.get("/api/live")
def get_live_status(db: Session = Depends(get_db)):
    latest_log = db.query(ActivityLog).order_by(ActivityLog.end_time.desc()).first()
    
    if not latest_log:
        return {"status": "no data"}
    
    device = db.query(Device).filter(Device.id == latest_log.device_id).first()
    user = db.query(User).filter(User.id == device.user_id).first() if device else None
    
    return {
        "current_app": latest_log.app_name.replace(".exe", ""),
        "window_title": latest_log.window_title,
        "is_idle": latest_log.is_idle,
        "cpu_usage": latest_log.cpu_usage,
        "memory_usage": latest_log.memory_usage,
        "disk_usage": latest_log.disk_usage,
        "upload_kb": latest_log.upload_kb,
        "download_kb": latest_log.download_kb,
        "last_updated": latest_log.end_time.strftime("%H:%M:%S"),
        "username": user.username if user else "Unknown",
        "device_name": device.device_name if device else "Unknown"
    }
@router.get("/api/analytics/daily-usage")
def get_daily_usage(device_id: Optional[str] = None, db: Session = Depends(get_db)):
    from sqlalchemy import func, cast, Date
    query = db.query(ActivityLog)
    if device_id:
        query = query.filter(ActivityLog.device_id == uuid.UUID(device_id))

    results = query.with_entities(
        cast(ActivityLog.start_time, Date).label("date"),
        func.sum(ActivityLog.duration).label("total_duration"),
        func.count(ActivityLog.id).label("total_sessions"),
        func.sum(ActivityLog.duration).filter(ActivityLog.is_idle == True).label("idle_duration")
    ).group_by(cast(ActivityLog.start_time, Date)).order_by(cast(ActivityLog.start_time, Date)).all()

    return [{
        "date": str(r.date),
        "hours": round((r.total_duration or 0) / 3600, 2),
        "sessions": r.total_sessions,
        "idle_hours": round((r.idle_duration or 0) / 3600, 2)
    } for r in results]
@router.get("/api/devices/status")
def get_device_status(db: Session = Depends(get_db)):
    from datetime import timedelta
    devices = db.query(Device).all()
    now = datetime.utcnow()
    
    return [{
        "id": str(d.id),
        "device_name": d.device_name,
        "last_seen": str(d.last_seen),
        "status": "Online" if d.last_seen and (now - d.last_seen).seconds < 120 else "Offline"
    } for d in devices]
@router.get("/api/analytics/heatmap")
def get_heatmap(device_id: Optional[str] = None, db: Session = Depends(get_db)):
    from sqlalchemy import func, cast, Date, extract
    query = db.query(ActivityLog)
    if device_id:
        query = query.filter(ActivityLog.device_id == uuid.UUID(device_id))
    
    results = query.with_entities(
        cast(ActivityLog.start_time, Date).label("date"),
        extract('hour', ActivityLog.start_time).label("hour"),
        func.sum(ActivityLog.duration).label("total_duration")
    ).group_by(
        cast(ActivityLog.start_time, Date),
        extract('hour', ActivityLog.start_time)
    ).all()

    return [{
        "date": str(r.date),
        "hour": int(r.hour),
        "duration_minutes": round((r.total_duration or 0) / 60, 1)
    } for r in results]
@router.get("/api/analytics/timeline")
def get_timeline(db: Session = Depends(get_db)):
    from sqlalchemy import cast, Date
    from datetime import date
    today = date.today()
    
    results = db.query(
        ActivityLog.app_name,
        ActivityLog.window_title,
        ActivityLog.start_time,
        ActivityLog.end_time,
        ActivityLog.duration,
        ActivityLog.is_idle
    ).filter(
        cast(ActivityLog.start_time, Date) == today
    ).order_by(ActivityLog.start_time).all()

    return [{
        "app": r.app_name.replace(".exe", ""),
        "title": r.window_title,
        "start": r.start_time.strftime("%H:%M:%S"),
        "end": r.end_time.strftime("%H:%M:%S"),
        "duration": r.duration,
        "is_idle": r.is_idle
    } for r in results]
@router.get("/api/analytics/idle-report")
def get_idle_report(db: Session = Depends(get_db)):
    from sqlalchemy import func, cast, Date
    
    total_duration = db.query(func.sum(ActivityLog.duration)).scalar() or 0
    idle_duration = db.query(func.sum(ActivityLog.duration)).filter(ActivityLog.is_idle == True).scalar() or 0
    active_duration = total_duration - idle_duration
    
    daily_idle = db.query(
        cast(ActivityLog.start_time, Date).label("date"),
        func.sum(ActivityLog.duration).label("total"),
        func.count(ActivityLog.id).filter(ActivityLog.is_idle == True).label("idle_sessions")
    ).group_by(cast(ActivityLog.start_time, Date)).order_by(cast(ActivityLog.start_time, Date)).all()

    return {
        "total_hours": round(total_duration / 3600, 2),
        "active_hours": round(active_duration / 3600, 2),
        "idle_hours": round(idle_duration / 3600, 2),
        "idle_percentage": round((idle_duration / total_duration * 100) if total_duration > 0 else 0, 1),
        "daily": [{
            "date": str(r.date),
            "total_hours": round((r.total or 0) / 3600, 2),
            "idle_sessions": r.idle_sessions
        } for r in daily_idle]
    }
@router.post("/api/session/login")
def session_login(device_id: str, db: Session = Depends(get_db), current_device: dict = Depends(get_current_device)):
    from server.database.models import SessionLog
    session = SessionLog(
        device_id=uuid.UUID(device_id),
        login_time=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": str(session.id), "login_time": str(session.login_time)}

@router.post("/api/session/logout")
def session_logout(session_id: str, db: Session = Depends(get_db), current_device: dict = Depends(get_current_device)):
    from server.database.models import SessionLog
    session = db.query(SessionLog).filter(SessionLog.id == uuid.UUID(session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.logout_time = datetime.now(timezone.utc).replace(tzinfo=None)
    session.duration_seconds = int((session.logout_time - session.login_time).total_seconds())
    db.commit()
    return {"session_id": session_id, "duration_seconds": session.duration_seconds}

@router.get("/api/session/history")
def session_history(db: Session = Depends(get_db)):
    from server.database.models import SessionLog
    sessions = db.query(SessionLog).order_by(SessionLog.login_time.desc()).limit(20).all()
    return [{
        "login_time": str(s.login_time),
        "logout_time": str(s.logout_time) if s.logout_time else "Still active",
        "duration_minutes": round(s.duration_seconds / 60, 1) if s.duration_seconds else None
    } for s in sessions]
@router.get("/api/analytics/weekly-trends")
def get_weekly_trends(db: Session = Depends(get_db)):
    from sqlalchemy import func, cast, Date, extract
    from datetime import timedelta, date
    
    results = db.query(
        extract('year', ActivityLog.start_time).label("year"),
        extract('week', ActivityLog.start_time).label("week"),
        func.min(cast(ActivityLog.start_time, Date)).label("week_start"),
        func.max(cast(ActivityLog.start_time, Date)).label("week_end"),
        func.sum(ActivityLog.duration).label("total_duration"),
        func.count(ActivityLog.id).label("total_sessions")
    ).group_by(
        extract('year', ActivityLog.start_time),
        extract('week', ActivityLog.start_time)
    ).order_by(
        extract('year', ActivityLog.start_time),
        extract('week', ActivityLog.start_time)
    ).all()

    return [{
        "week": f"{r.week_start.strftime('%d %b')} - {r.week_end.strftime('%d %b')}",
        "hours": round((r.total_duration or 0) / 3600, 2),
        "sessions": r.total_sessions
    } for r in results]
@router.get("/api/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{
        "id": str(u.id),
        "username": u.username,
        "department": u.department,
        "created_at": str(u.created_at)
    } for u in users]

@router.get("/api/reports/activity-csv")
def download_activity_report(device_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ActivityLog)
    if device_id:
        query = query.filter(ActivityLog.device_id == uuid.UUID(device_id))
    
    logs = query.order_by(ActivityLog.start_time.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['App Name', 'Window Title', 'Start Time', 'End Time', 'Duration (seconds)', 'Is Idle', 'CPU %', 'Memory %', 'Disk %', 'Upload KB/s', 'Download KB/s'])
    
    for log in logs:
        writer.writerow([
            log.app_name,
            log.window_title,
            log.start_time,
            log.end_time,
            log.duration,
            log.is_idle,
            log.cpu_usage,
            log.memory_usage,
            log.disk_usage,
            log.upload_kb,
            log.download_kb
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=activity_report.csv"}
    )
@router.get("/api/analytics/resource-alerts")
def get_resource_alerts(device_id: Optional[str] = None, db: Session = Depends(get_db)):
    from sqlalchemy import func
    from datetime import timedelta

    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(hours=24)

    def base_query(start):
        q = db.query(ActivityLog).filter(ActivityLog.start_time >= start)
        if device_id:
            q = q.filter(ActivityLog.device_id == uuid.UUID(device_id))
        return q

    # Get averages over last 24 hours
    avg_result = base_query(one_day_ago).with_entities(
        func.avg(ActivityLog.cpu_usage).label("avg_cpu"),
        func.avg(ActivityLog.memory_usage).label("avg_memory"),
        func.avg(ActivityLog.disk_usage).label("avg_disk")
    ).first()

    avg_cpu = avg_result.avg_cpu or 0
    avg_memory = avg_result.avg_memory or 0
    avg_disk = avg_result.avg_disk or 0

    # Get std deviation over last 24 hours
    std_result = base_query(one_day_ago).with_entities(
        func.stddev(ActivityLog.cpu_usage).label("std_cpu"),
        func.stddev(ActivityLog.memory_usage).label("std_memory"),
        func.stddev(ActivityLog.disk_usage).label("std_disk")
    ).first()

    std_cpu = std_result.std_cpu or 0
    std_memory = std_result.std_memory or 0
    std_disk = std_result.std_disk or 0

    # Threshold = average + 3 standard deviations, capped at 90%
    cpu_threshold = min(avg_cpu + 3 * std_cpu, 90)
    memory_threshold = min(avg_memory + 3 * std_memory, 90)
    disk_threshold = min(avg_disk + 3 * std_disk, 90)

    # Check last hour for spikes
    recent_logs = base_query(one_hour_ago).all()

    alerts = []
    for log in recent_logs:
        if log.cpu_usage and log.cpu_usage > cpu_threshold:
            alerts.append({
                "type": "CPU",
                "value": round(log.cpu_usage, 1),
                "threshold": round(cpu_threshold, 1),
                "time": log.start_time.strftime("%H:%M:%S"),
                "app": log.app_name
            })
        if log.memory_usage and log.memory_usage > memory_threshold:
            alerts.append({
                "type": "Memory",
                "value": round(log.memory_usage, 1),
                "threshold": round(memory_threshold, 1),
                "time": log.start_time.strftime("%H:%M:%S"),
                "app": log.app_name
            })
        if log.disk_usage and log.disk_usage > disk_threshold:
            alerts.append({
                "type": "Disk",
                "value": round(log.disk_usage, 1),
                "threshold": round(disk_threshold, 1),
                "time": log.start_time.strftime("%H:%M:%S"),
                "app": log.app_name
            })
    
    seen = {}
    for a in alerts:
        key = (a["type"], a["app"])
        if key not in seen or a["value"] > seen[key]["value"]:
            seen[key] = a

    alerts = list(seen.values())

    alerts.sort(key=lambda x: x["time"], reverse=True)
    return alerts[:10]
@router.get("/api/analytics/top-titles")
def get_top_titles(device_id: Optional[str] = None, period: Optional[str] = None, db: Session = Depends(get_db)):
    from sqlalchemy import func
    from datetime import timedelta

    query = db.query(
        ActivityLog.window_title,
        ActivityLog.app_name,
        func.sum(ActivityLog.duration).label("total_duration")
    )

    if device_id:
        query = query.filter(ActivityLog.device_id == uuid.UUID(device_id))

    if period == "day":
        cutoff = datetime.now() - timedelta(days=1)
        query = query.filter(ActivityLog.start_time >= cutoff)
    elif period == "week":
        cutoff = datetime.now() - timedelta(weeks=1)
        query = query.filter(ActivityLog.start_time >= cutoff)
    elif period == "month":
        cutoff = datetime.now() - timedelta(days=30)
        query = query.filter(ActivityLog.start_time >= cutoff)

    results = query.group_by(ActivityLog.window_title, ActivityLog.app_name)\
        .order_by(func.sum(ActivityLog.duration).desc()).limit(10).all()

    return [{
        "title": (r.window_title or "Unknown")[:60],
        "app": (r.app_name or "").replace(".exe", ""),
        "minutes": round((r.total_duration or 0) / 60),
        "category": classify_activity(r.app_name or "", r.window_title or "")
    } for r in results]

@router.get("/api/analytics/categories")
def get_categories(device_id: Optional[str] = None, period: Optional[str] = None, db: Session = Depends(get_db)):
    from datetime import timedelta

    query = db.query(ActivityLog)

    if device_id:
        query = query.filter(ActivityLog.device_id == uuid.UUID(device_id))

    if period == "day":
        query = query.filter(ActivityLog.start_time >= datetime.now() - timedelta(days=1))
    elif period == "week":
        query = query.filter(ActivityLog.start_time >= datetime.now() - timedelta(weeks=1))
    elif period == "month":
        query = query.filter(ActivityLog.start_time >= datetime.now() - timedelta(days=30))

    logs = query.all()
    totals = {}
    for log in logs:
        cat = classify_activity(log.app_name or "", log.window_title or "")
        totals[cat] = totals.get(cat, 0) + (log.duration or 0)

    return [{"category": k, "minutes": round(v / 60)} for k, v in sorted(totals.items(), key=lambda x: -x[1])]
class AdminLoginRequest(BaseModel):
    username: str
    password: str

@router.post("/api/admin/login")
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username, User.is_admin == True).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not bcrypt.checkpw(request.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"username": user.username, "is_admin": True})
    return {"token": token, "username": user.username}

@router.post("/api/admin/setup")
def setup_admin(request: AdminLoginRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.is_admin == True).first()
    if existing:
        raise HTTPException(status_code=400, detail="Admin already exists")
    password_hash = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()
    admin = User(username=request.username, password_hash=password_hash, is_admin=True)
    db.add(admin)
    db.commit()
    return {"message": "Admin created successfully"}
@router.get("/api/live/all")
def get_all_live_status(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    now = datetime.utcnow()
    result = []

    for device in devices:
        latest_log = db.query(ActivityLog)\
            .filter(ActivityLog.device_id == device.id)\
            .order_by(ActivityLog.end_time.desc()).first()
        user = db.query(User).filter(User.id == device.user_id).first()

        is_online = device.last_seen and (now - device.last_seen).total_seconds() < 120

        # detect if in a Teams call
        in_call = False
        call_with = None
        if latest_log:
            app_lower = (latest_log.app_name or "").lower()
            title_lower = (latest_log.window_title or "").lower()
            if "teams" in app_lower and any(x in title_lower for x in ["meeting", "call", "| microsoft teams"]):
                in_call = True
                call_with = latest_log.window_title.split("|")[0].strip()

        result.append({
            "username": user.username if user else "Unknown",
            "device_name": device.device_name,
            "current_app": latest_log.app_name.replace(".exe", "") if latest_log else None,
            "window_title": latest_log.window_title if latest_log else None,
            "is_idle": latest_log.is_idle if latest_log else None,
            "is_online": is_online,
            "in_call": in_call,
            "call_with": call_with,
            "last_updated": latest_log.end_time.strftime("%H:%M:%S") if latest_log else None
        })

    return result