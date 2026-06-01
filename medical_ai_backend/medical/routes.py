from fastapi import APIRouter

from medical.schema import (
    OrganisationCreate,
    StoreCreate,
    UserCreate,
    LoginSchema
)

from medical.crud import (
    create_organization,
    create_store,
    create_user,
    login_user
)

router = APIRouter()


# =====================================================
# ORGANIZATION
# =====================================================

@router.post("/register/organization")
def register_organization(data: OrganisationCreate):

    return create_organization(data)


# =====================================================
# STORE
# =====================================================

@router.post("/register/store")
def register_store(data: StoreCreate):

    return create_store(data)


# =====================================================
# USER
# =====================================================

@router.post("/register/user")
def register_user(data: UserCreate):

    return create_user(data)


# =====================================================
# LOGIN
# =====================================================

@router.post("/login")
def login(data: LoginSchema):

    return login_user(data)