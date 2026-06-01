from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from medical.routes import router

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)