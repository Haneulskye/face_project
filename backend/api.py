"""
FastAPI server exposing the existing face-auth backend over HTTP so the
Android app (and, later, the web client) can call a single shared API.

Run with:
    uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
"""

import io
import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

from backend import heart_rate_store, user_profile_store
from backend.face_auth import LowQualityFaceError, authenticate_face, delete_face, register_face
from backend.iris_auth import authenticate_iris_from_photo, delete_iris, has_iris, register_iris

app = FastAPI(title="Face Auth API")

# Demo-only default — set a real ADMIN_TOKEN env var for any non-local
# deployment (e.g. in render.yaml). The admin page asks for this as a
# password and sends it back as the X-Admin-Token header on every call.
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "changeme-admin")

# Demo-only: open CORS so the app can be pointed at this server from any
# device on the network during the 학술제 demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

user_profile_store.init_db()
heart_rate_store.init_db()


def _heart_rate_status(bpm: float) -> str:
    if bpm < 60:
        return "bradycardia"
    if bpm > 100:
        return "tachycardia"
    return "normal"


def _require_admin(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


def _delete_user_cascade(name: str):
    delete_face(name)
    delete_iris(name)
    heart_rate_store.delete_records(name)
    user_profile_store.delete_user(name)


def _read_image(upload: UploadFile) -> np.ndarray:
    """Decode an uploaded image file into a BGR numpy array."""
    data = upload.file.read()

    try:
        pil_image = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_image")

    rgb = np.array(pil_image)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/face")
def auth_face(image: UploadFile = File(...)):
    bgr_image = _read_image(image)

    # Face is the primary (and gating) signal — iris runs alongside it on
    # the same photo purely as a secondary, informational signal. The iris
    # model is prototype-quality (see backend/iris_auth.py), so it is not
    # allowed to block or override a face-based authentication decision.
    result = authenticate_face(bgr_image)
    iris_result = authenticate_iris_from_photo(bgr_image)

    profile = None
    if result["authenticated"] and result["name"]:
        profile = user_profile_store.get_user(result["name"])

    return {
        "authenticated": result["authenticated"],
        "name": result["name"],
        "score": result["score"],
        "profile": profile,
        "reason": result.get("reason"),
        "iris": {
            # "matched" means the iris result's own best match is the SAME
            # person the face result identified — not merely that iris
            # matched *someone* in the gallery (a different registered
            # person's iris scoring highest would otherwise still show as
            # a misleading "일치").
            "matched": bool(iris_result.get("authenticated"))
            and iris_result.get("name") == result.get("name"),
            "score": iris_result.get("score", 0.0),
            "reason": iris_result.get("reason"),
        },
    }


@app.post("/users/register")
def register_user(
    name: str = Form(...),
    age: int = Form(...),
    nickname: str = Form(...),
    gender: str = Form(...),
    height_cm: float = Form(...),
    weight_kg: Optional[float] = Form(None),
    consent: bool = Form(...),
    image: UploadFile = File(...),
):
    if not consent:
        raise HTTPException(status_code=400, detail="consent_required")

    if age < user_profile_store.MINIMUM_AGE:
        raise HTTPException(status_code=400, detail="age_restricted")

    if user_profile_store.user_exists(name):
        raise HTTPException(status_code=409, detail="name_already_registered")

    bgr_image = _read_image(image)

    try:
        embedding = register_face(name, bgr_image)
    except LowQualityFaceError:
        raise HTTPException(status_code=422, detail="low_quality_face")

    if embedding is None:
        raise HTTPException(status_code=422, detail="face_not_detected")

    # Best-effort: don't fail registration if no eye could be located —
    # iris is a secondary modality (see backend/iris_auth.py).
    register_iris(name, bgr_image)

    user_profile_store.create_user(
        name=name,
        age=age,
        nickname=nickname,
        gender=gender,
        height_cm=height_cm,
        weight_kg=weight_kg,
    )

    return {
        "success": True,
        "name": name,
        "profile": user_profile_store.get_user(name),
    }


@app.get("/users/{name}")
def get_user(name: str):
    profile = user_profile_store.get_user(name)

    if profile is None:
        raise HTTPException(status_code=404, detail="user_not_found")

    return profile


@app.delete("/users/{name}")
def delete_user(name: str):
    if not user_profile_store.user_exists(name):
        raise HTTPException(status_code=404, detail="user_not_found")

    _delete_user_cascade(name)

    return {"success": True, "name": name}


# ============================================================
# ADMIN — list/delete registered accounts.
#
# Protected by a single shared token (ADMIN_TOKEN env var), sent as the
# X-Admin-Token header. This is demo-grade auth, not production-grade —
# good enough to keep the delete button out of a random visitor's hands,
# not meant to withstand a determined attacker.
# ============================================================

@app.get("/admin/users")
def admin_list_users(_: None = Depends(_require_admin)):
    users = user_profile_store.list_users()
    for user in users:
        user["has_iris"] = has_iris(user["name"])
        user["latest_heart_rate"] = heart_rate_store.get_latest(user["name"])
    return {"users": users}


@app.delete("/admin/users/{name}")
def admin_delete_user(name: str, _: None = Depends(_require_admin)):
    if not user_profile_store.user_exists(name):
        raise HTTPException(status_code=404, detail="user_not_found")

    _delete_user_cascade(name)

    return {"success": True, "name": name}


# ============================================================
# HEART RATE — watch-sourced (Galaxy Watch / Health Connect on Android,
# Apple Watch / HealthKit on iOS). The phone app reads the value from the
# platform health API and pushes it here via /measure; the web client has
# no direct watch access, so it only ever reads /latest and /history.
# ============================================================

@app.get("/users/{name}/heart-rate/latest")
def latest_heart_rate(name: str):
    if not user_profile_store.user_exists(name):
        raise HTTPException(status_code=404, detail="user_not_found")

    record = heart_rate_store.get_latest(name)

    if record is None:
        return {"available": False, "bpm": None, "status": None}

    return {
        "available": True,
        "bpm": record["bpm"],
        "status": _heart_rate_status(record["bpm"]),
        "measured_at": record["measured_at"],
        "source": record["source"],
    }


@app.get("/users/{name}/heart-rate/history")
def heart_rate_history(name: str):
    if not user_profile_store.user_exists(name):
        raise HTTPException(status_code=404, detail="user_not_found")

    records = heart_rate_store.get_history(name)

    return {
        "available": len(records) > 0,
        "records": [
            {
                "bpm": r["bpm"],
                "status": _heart_rate_status(r["bpm"]),
                "measured_at": r["measured_at"],
                "source": r["source"],
            }
            for r in records
        ],
    }


@app.post("/users/{name}/heart-rate/measure")
def measure_heart_rate(
    name: str,
    bpm: Optional[float] = Form(None),
    source: str = Form("watch"),
):
    if not user_profile_store.user_exists(name):
        raise HTTPException(status_code=404, detail="user_not_found")

    # No bpm means the client has no watch reading to report yet (e.g. no
    # watch paired) — keep the old "measurement not available" response.
    if bpm is None:
        return {"available": False, "bpm": None, "status": None}

    record = heart_rate_store.record_heart_rate(name, bpm, source)

    return {
        "available": True,
        "bpm": record["bpm"],
        "status": _heart_rate_status(record["bpm"]),
        "measured_at": record["measured_at"],
        "source": record["source"],
    }


# ============================================================
# WEB CLIENT
#
# Serves web/ as a static site at the server root. Must be mounted last —
# a "/" mount registered earlier would shadow every API route above it.
# ============================================================

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
