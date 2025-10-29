import os
import hashlib
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User as UserSchema, Worker as WorkerSchema, Booking as BookingSchema


app = FastAPI(title="Emergency Home Services API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------- Auth Models ---------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# --------- Helpers ---------
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def to_public_id(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


# --------- Startup seed ---------
@app.on_event("startup")
def seed_workers_if_empty():
    if db is None:
        return
    if db["worker"].count_documents({}) == 0:
        sample_workers = [
            WorkerSchema(
                name="Amit Verma",
                service_type="plumber",
                location="Downtown",
                availability=["09:00-11:00", "13:00-15:00"],
                rating=4.7,
                experience_years=6,
                bio="Expert in leak fixes and bathroom fittings",
            ),
            WorkerSchema(
                name="Sara Khan",
                service_type="electrician",
                location="Uptown",
                availability=["10:00-12:00", "16:00-18:00"],
                rating=4.8,
                experience_years=8,
                bio="Certified electrician for home wiring and repairs",
            ),
            WorkerSchema(
                name="Rohan Das",
                service_type="gas",
                location="Midtown",
                availability=["08:00-10:00", "14:00-16:00"],
                rating=4.6,
                experience_years=5,
                bio="Gas line installation and stove servicing",
            ),
        ]
        for w in sample_workers:
            create_document("worker", w)


# --------- Basic ---------
@app.get("/")
def read_root():
    return {"message": "Emergency Home Services Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# --------- Auth Endpoints ---------
@app.post("/auth/register")
def register(payload: RegisterRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    existing = db["user"].find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = UserSchema(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
        address=payload.address,
        is_active=True,
    )
    user_id = create_document("user", user_doc)
    user = db["user"].find_one({"_id": ObjectId(user_id)})
    return to_public_id(user)


@app.post("/auth/login")
def login(payload: LoginRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    user = db["user"].find_one({"email": payload.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.get("password_hash") != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return to_public_id(user)


# --------- Workers ---------
@app.get("/workers")
def list_workers(service_type: Optional[str] = None, location: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    query = {}
    if service_type:
        query["service_type"] = service_type
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    workers = list(db["worker"].find(query).limit(100))
    return [to_public_id(w) for w in workers]


class CreateWorkerRequest(BaseModel):
    name: str
    service_type: str
    location: str
    availability: List[str] = []
    rating: float = 4.5
    experience_years: int = 1
    bio: Optional[str] = None


@app.post("/workers")
def create_worker(payload: CreateWorkerRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    worker_doc = WorkerSchema(**payload.model_dump())
    worker_id = create_document("worker", worker_doc)
    worker = db["worker"].find_one({"_id": ObjectId(worker_id)})
    return to_public_id(worker)


# --------- Bookings ---------
class CreateBookingRequest(BaseModel):
    user_id: str
    worker_id: str
    service_date: str  # ISO date string
    time_slot: str
    address: str


@app.post("/bookings")
def create_booking(payload: CreateBookingRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    # Validate references
    try:
        user = db["user"].find_one({"_id": ObjectId(payload.user_id)})
        worker = db["worker"].find_one({"_id": ObjectId(payload.worker_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id or worker_id")
    if not user or not worker:
        raise HTTPException(status_code=404, detail="User or Worker not found")

    booking_doc = BookingSchema(
        user_id=payload.user_id,
        worker_id=payload.worker_id,
        service_date=datetime.fromisoformat(payload.service_date).date(),
        time_slot=payload.time_slot,
        address=payload.address,
        status="pending",
    )
    booking_id = create_document("booking", booking_doc)
    booking = db["booking"].find_one({"_id": ObjectId(booking_id)})
    return to_public_id(booking)


@app.get("/bookings")
def list_bookings(user_id: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    query = {}
    if user_id:
        query["user_id"] = user_id
    bookings = list(db["booking"].find(query).sort("created_at", -1).limit(100))
    return [to_public_id(b) for b in bookings]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
