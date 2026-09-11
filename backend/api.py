"""
FastAPI server exposing the existing face-auth backend over HTTP so the
Android app (and, later, the web client) can call a single shared API.

Run with:
    uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
"""

import io
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from backend import user_profile_store
from backend.face_auth import authenticate_face, register_face

app = FastAPI(title="Face Auth API")

# Demo-only: open CORS so the app can be pointed at this server from any
# device on the network during the 학술제 demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

user_profile_store.init_db()


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

    result = authenticate_face(bgr_image)

    profile = None
    if result["authenticated"] and result["name"]:
        profile = user_profile_store.get_user(result["name"])

    return {
        "authenticated": result["authenticated"],
        "name": result["name"],
        "score": result["score"],
        "profile": profile,
        "reason": result.get("reason"),
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

    embedding = register_face(name, bgr_image)

    if embedding is None:
        raise HTTPException(status_code=422, detail="face_not_detected")

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


# ============================================================
# HEART RATE (rPPG) — placeholder
#
# B팀 rPPG 모듈이 통합되기 전까지는 "준비 중" 상태를 반환한다.
# 실제 측정 로직이 추가되면 이 두 엔드포인트만 교체하면 된다.
# ============================================================

@app.get("/users/{name}/heart-rate/latest")
def latest_heart_rate(name: str):
    if not user_profile_store.user_exists(name):
        raise HTTPException(status_code=404, detail="user_not_found")

    return {"available": False, "bpm": None, "status": None}


@app.get("/users/{name}/heart-rate/history")
def heart_rate_history(name: str):
    if not user_profile_store.user_exists(name):
        raise HTTPException(status_code=404, detail="user_not_found")

    return {"available": False, "records": []}


@app.post("/users/{name}/heart-rate/measure")
def measure_heart_rate(name: str):
    if not user_profile_store.user_exists(name):
        raise HTTPException(status_code=404, detail="user_not_found")

    return {"available": False, "bpm": None, "status": None}
