from pydantic import BaseModel
from typing import List, Optional

class OrganisationCreate(BaseModel):
    name: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    org_type: str = None
    gst_number: Optional[str] = None

class StoreCreate(BaseModel):
    name: str
    drug_license_number: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gst_number: Optional[str] = None
    organisation_id: int
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

class UserCreate(BaseModel):
    full_name: str
    username: str
    email: str
    phone_number: Optional[str] = None
    password: str
    role: str
    store_id: int

class LoginSchema(BaseModel):
    username: str
    password: str

