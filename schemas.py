"""
Database Schemas for Emergency Home Services App

Each Pydantic model represents a collection in your MongoDB database.
Collection name is the lowercase of the class name (e.g., User -> "user").
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date


class User(BaseModel):
    """Users collection schema"""
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Unique email address")
    password_hash: str = Field(..., description="Hashed password")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Default service address")
    is_active: bool = Field(True, description="Whether user is active")


class Worker(BaseModel):
    """Workers (Service providers) collection schema"""
    name: str = Field(..., description="Worker full name")
    service_type: str = Field(..., description="Type of service e.g., plumber, electrician, gas")
    location: str = Field(..., description="City/Area of service")
    availability: List[str] = Field(default_factory=list, description="Available time slots, e.g., ['09:00-11:00']")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating")
    experience_years: int = Field(1, ge=0, description="Years of experience")
    bio: Optional[str] = Field(None, description="Short bio or notes")


class Booking(BaseModel):
    """Bookings collection schema"""
    user_id: str = Field(..., description="ID of the user booking the service")
    worker_id: str = Field(..., description="ID of the worker to be booked")
    service_date: date = Field(..., description="Date of service")
    time_slot: str = Field(..., description="Chosen time slot")
    address: str = Field(..., description="Service address")
    status: str = Field("pending", description="Booking status: pending, confirmed, completed, cancelled")
