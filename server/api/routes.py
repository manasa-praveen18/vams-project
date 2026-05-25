import sys
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import Integer
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from server.auth.jwt import create_access_token, get_current_device
import uuid
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from server.database.db_manager import get_db
from server.database.models import User, Device, ActivityLog
from server.auth.jwt import create_access_token

router = APIRouter()

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
def get_top_apps(db: Session = Depends(get_db)):
    from sqlalchemy import func
    results = db.query(
        ActivityLog.app_name,
        func.sum(ActivityLog.duration).label("total_duration")
    ).group_by(ActivityLog.app_name).order_by(func.sum(ActivityLog.duration).desc()).limit(10).all()
    
    return [{"app_name": r.app_name, "total_duration": r.total_duration} for r in results]

@router.get("/api/analytics/overview")
def get_overview(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total_logs = db.query(func.count(ActivityLog.id)).scalar()
    total_duration = db.query(func.sum(ActivityLog.duration)).scalar() or 0
    total_devices = db.query(func.count(Device.id)).scalar()
    idle_count = db.query(func.count(ActivityLog.id)).filter(ActivityLog.is_idle == True).scalar()
    
    return {
        "total_logs": total_logs,
        "total_duration_hours": round(total_duration / 3600, 2),
        "total_devices": total_devices,
        "idle_count": idle_count
    }

@router.get("/api/devices")
def get_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return [{"id": str(d.id), "device_name": d.device_name, "last_seen": str(d.last_seen)} for d in devices]

@router.get("/api/analytics/resources")
def get_resources(db: Session = Depends(get_db)):
    results = db.query(
        ActivityLog.start_time,
        ActivityLog.cpu_usage,
        ActivityLog.memory_usage,
        ActivityLog.disk_usage,
        ActivityLog.upload_kb,
        ActivityLog.download_kb
    ).order_by(ActivityLog.start_time.desc()).limit(50).all()

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
    
    return {
        "current_app": latest_log.app_name.replace(".exe", ""),
        "window_title": latest_log.window_title,
        "is_idle": latest_log.is_idle,
        "cpu_usage": latest_log.cpu_usage,
        "memory_usage": latest_log.memory_usage,
        "disk_usage": latest_log.disk_usage,
        "upload_kb": latest_log.upload_kb,
        "download_kb": latest_log.download_kb,
        "last_updated": latest_log.end_time.strftime("%H:%M:%S")
    }
@router.get("/api/analytics/daily-usage")
def get_daily_usage(db: Session = Depends(get_db)):
    from sqlalchemy import func, cast, Date
    results = db.query(
        cast(ActivityLog.start_time, Date).label("date"),
        func.sum(ActivityLog.duration).label("total_duration"),
        func.count(ActivityLog.id).label("total_sessions"),
        func.sum(ActivityLog.duration.op('*')(ActivityLog.is_idle.cast(Integer))).label("idle_duration")
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
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    return [{
        "id": str(d.id),
        "device_name": d.device_name,
        "last_seen": str(d.last_seen),
        "status": "Online" if d.last_seen and (now - d.last_seen).seconds < 120 else "Offline"
    } for d in devices]