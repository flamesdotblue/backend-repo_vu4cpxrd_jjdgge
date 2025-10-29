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
        # Andhra Pradesh focused worker set across cities and services
        ap_workers = [
            # Visakhapatnam
            WorkerSchema(name="Srinivas Reddy", service_type="plumber", location="Visakhapatnam", availability=["09:00-11:00", "15:00-17:00"], rating=4.8, experience_years=9, bio="Leak repair, bathroom fitting, water purifier plumbing"),
            WorkerSchema(name="Kalyan Kumar", service_type="electrician", location="Visakhapatnam", availability=["10:00-12:00", "16:00-18:00"], rating=4.7, experience_years=7, bio="Wiring, MCB, inverter & fan installations"),
            WorkerSchema(name="Suresh Yadav", service_type="ac", location="Visakhapatnam", availability=["11:00-13:00", "18:00-20:00"], rating=4.6, experience_years=6, bio="AC servicing, gas refill, installation"),
            # Vijayawada
            WorkerSchema(name="Ravi Teja", service_type="plumber", location="Vijayawada", availability=["08:00-10:00", "14:00-16:00"], rating=4.5, experience_years=5, bio="Kitchen sink, pipeline & overhead tank solutions"),
            WorkerSchema(name="Imran Shaik", service_type="electrician", location="Vijayawada", availability=["09:00-11:00", "17:00-19:00"], rating=4.7, experience_years=8, bio="Short-circuit fix, appliance wiring, geyser fix"),
            WorkerSchema(name="Pradeep Varma", service_type="gas", location="Vijayawada", availability=["12:00-14:00", "19:00-21:00"], rating=4.6, experience_years=6, bio="Gas stove service, pipeline checks, regulator"),
            # Guntur
            WorkerSchema(name="Arun K", service_type="plumber", location="Guntur", availability=["10:00-12:00", "16:00-18:00"], rating=4.4, experience_years=4, bio="Shower, tap & flush repairs"),
            WorkerSchema(name="Rahul Dev", service_type="electrician", location="Guntur", availability=["09:00-11:00", "13:00-15:00"], rating=4.5, experience_years=6, bio="Switchboard, LED light & fan services"),
            WorkerSchema(name="Naveen Kumar", service_type="carpenter", location="Guntur", availability=["11:00-13:00", "17:00-19:00"], rating=4.6, experience_years=7, bio="Door, cupboard repair & modular fittings"),
            # Tirupati
            WorkerSchema(name="Bhaskar", service_type="plumber", location="Tirupati", availability=["08:00-10:00", "15:00-17:00"], rating=4.5, experience_years=5, bio="Bathroom & kitchen plumbing"),
            WorkerSchema(name="Naresh", service_type="electrician", location="Tirupati", availability=["10:00-12:00", "18:00-20:00"], rating=4.6, experience_years=6, bio="Home wiring & fan installation"),
            WorkerSchema(name="Sandeep", service_type="ac", location="Tirupati", availability=["09:00-11:00", "14:00-16:00"], rating=4.6, experience_years=6, bio="Split/Window AC install & service"),
            # Kakinada
            WorkerSchema(name="Vamsi", service_type="plumber", location="Kakinada", availability=["10:00-12:00", "16:00-18:00"], rating=4.4, experience_years=4, bio="Blockage clearing & leak fixes"), 
            WorkerSchema(name="Hemanth", service_type="electrician", location="Kakinada", availability=["09:30-11:30", "17:30-19:30"], rating=4.5, experience_years=5, bio="Switch repair, UPS, geyser wiring"),
            # Rajahmundry
            WorkerSchema(name="Sridhar", service_type="plumber", location="Rajahmundry", availability=["08:00-10:00", "13:00-15:00"], rating=4.5, experience_years=5, bio="Tap replacement & pipeline checks"),
            WorkerSchema(name="Maneesh", service_type="electrician", location="Rajahmundry", availability=["11:00-13:00", "18:00-20:00"], rating=4.6, experience_years=6, bio="Switchboard, lighting and fans"),
            # Nellore
            WorkerSchema(name="Venkat", service_type="plumber", location="Nellore", availability=["09:00-11:00", "15:00-17:00"], rating=4.5, experience_years=5, bio="Bathroom fittings & tap leaks"),
            WorkerSchema(name="Kishore", service_type="electrician", location="Nellore", availability=["10:00-12:00", "17:00-19:00"], rating=4.6, experience_years=7, bio="Inverter, MCB and wiring"),
            # Anantapur
            WorkerSchema(name="Fayaz", service_type="plumber", location="Anantapur", availability=["08:00-10:00", "14:00-16:00"], rating=4.4, experience_years=4, bio="Sink & pipeline fixes"),
            WorkerSchema(name="Harish", service_type="electrician", location="Anantapur", availability=["11:00-13:00", "18:00-20:00"], rating=4.5, experience_years=5, bio="Meter board & earthing"),
            # Kurnool
            WorkerSchema(name="Shiva", service_type="plumber", location="Kurnool", availability=["09:00-11:00", "15:00-17:00"], rating=4.5, experience_years=5, bio="Bathroom repairs & water leaks"),
            WorkerSchema(name="Lokesh", service_type="electrician", location="Kurnool", availability=["10:00-12:00", "17:00-19:00"], rating=4.6, experience_years=7, bio="Wiring, fan & LED installs"),
            # Kadapa
            WorkerSchema(name="Arif", service_type="plumber", location="Kadapa", availability=["08:00-10:00", "13:00-15:00"], rating=4.4, experience_years=4, bio="Tap & shower repairs"),
            WorkerSchema(name="Mahesh", service_type="electrician", location="Kadapa", availability=["11:00-13:00", "18:00-20:00"], rating=4.5, experience_years=5, bio="Switchboard & home wiring"),
            # Srikakulam
            WorkerSchema(name="Rakesh", service_type="plumber", location="Srikakulam", availability=["09:00-11:00", "16:00-18:00"], rating=4.3, experience_years=3, bio="Leak repairs & drain cleaning"),
            WorkerSchema(name="Charan", service_type="electrician", location="Srikakulam", availability=["10:00-12:00", "17:00-19:00"], rating=4.5, experience_years=5, bio="Lighting, fan installation"),
            # Vizianagaram
            WorkerSchema(name="Ajay", service_type="plumber", location="Vizianagaram", availability=["08:30-10:30", "15:30-17:30"], rating=4.4, experience_years=4, bio="Kitchen & bathroom plumbing"),
            WorkerSchema(name="Yogesh", service_type="electrician", location="Vizianagaram", availability=["10:00-12:00", "18:00-20:00"], rating=4.6, experience_years=6, bio="Switchboard & inverter wiring"),
            # Ongole
            WorkerSchema(name="Ramu", service_type="plumber", location="Ongole", availability=["09:00-11:00", "14:00-16:00"], rating=4.4, experience_years=4, bio="Sink blockage & tap leaks"),
            WorkerSchema(name="Sujith", service_type="electrician", location="Ongole", availability=["11:00-13:00", "17:00-19:00"], rating=4.5, experience_years=5, bio="Fan, LED, wiring"),
            # Eluru
            WorkerSchema(name="Ravi Kumar", service_type="plumber", location="Eluru", availability=["08:00-10:00", "13:00-15:00"], rating=4.5, experience_years=5, bio="Bathroom fittings & leaks"),
            WorkerSchema(name="Anil", service_type="electrician", location="Eluru", availability=["10:00-12:00", "18:00-20:00"], rating=4.6, experience_years=6, bio="Short circuit & wiring"),
            # Machilipatnam
            WorkerSchema(name="Gopi", service_type="plumber", location="Machilipatnam", availability=["09:00-11:00", "16:00-18:00"], rating=4.3, experience_years=3, bio="Drain cleaning & taps"),
            WorkerSchema(name="Venkatesh", service_type="electrician", location="Machilipatnam", availability=["10:00-12:00", "17:00-19:00"], rating=4.5, experience_years=5, bio="MCB, wiring & fans"),
            # Chittoor
            WorkerSchema(name="Mohan", service_type="plumber", location="Chittoor", availability=["08:00-10:00", "14:00-16:00"], rating=4.4, experience_years=4, bio="Pipelines & taps"),
            WorkerSchema(name="Sathish", service_type="electrician", location="Chittoor", availability=["11:00-13:00", "18:00-20:00"], rating=4.6, experience_years=6, bio="Wiring & appliances"),
            # Hindupur
            WorkerSchema(name="Rahim", service_type="plumber", location="Hindupur", availability=["09:00-11:00", "15:00-17:00"], rating=4.3, experience_years=3, bio="Leakage & fittings"),
            WorkerSchema(name="Teja", service_type="electrician", location="Hindupur", availability=["10:00-12:00", "17:00-19:00"], rating=4.5, experience_years=5, bio="Lighting, fans, wiring"),
            # Tenali
            WorkerSchema(name="Surya", service_type="plumber", location="Tenali", availability=["08:30-10:30", "16:00-18:00"], rating=4.4, experience_years=4, bio="Bathroom, kitchen plumbing"),
            WorkerSchema(name="Rohit", service_type="electrician", location="Tenali", availability=["10:00-12:00", "18:00-20:00"], rating=4.6, experience_years=6, bio="Electrical fittings"),
            # Bhimavaram
            WorkerSchema(name="Prakash", service_type="plumber", location="Bhimavaram", availability=["09:00-11:00", "15:00-17:00"], rating=4.4, experience_years=4, bio="Taps & pipelines"),
            WorkerSchema(name="Sunny", service_type="electrician", location="Bhimavaram", availability=["11:00-13:00", "17:00-19:00"], rating=4.5, experience_years=5, bio="Switchboard & wiring"),
            # Tadepalligudem
            WorkerSchema(name="Madhu", service_type="plumber", location="Tadepalligudem", availability=["08:00-10:00", "14:00-16:00"], rating=4.4, experience_years=4, bio="Leak & blockage fixes"),
            WorkerSchema(name="Vivek", service_type="electrician", location="Tadepalligudem", availability=["10:00-12:00", "18:00-20:00"], rating=4.6, experience_years=6, bio="Wiring & lights"),
            # Add some specialized services across AP
            WorkerSchema(name="Iqbal", service_type="locksmith", location="Vijayawada", availability=["24x7"], rating=4.7, experience_years=10, bio="Emergency lock opening & key duplication"),
            WorkerSchema(name="Anusha", service_type="cleaning", location="Visakhapatnam", availability=["09:00-12:00", "13:00-16:00"], rating=4.8, experience_years=7, bio="Deep home cleaning & kitchen cleaning"),
            WorkerSchema(name="Pooja", service_type="pest", location="Guntur", availability=["10:00-13:00", "15:00-18:00"], rating=4.6, experience_years=6, bio="Cockroach, termite & mosquito control"),
        ]
        for w in ap_workers:
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
    workers = list(db["worker"].find(query).limit(200))
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
