from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nba_analysis import router as nba_router

app = FastAPI(
    title="Crypto-NBA Event Intelligence API",
    description="Analyzes the impact of cryptocurrency trends on NBA outcomes and behavior.",
    version="1.0.0"
)

# Allow CORS for frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount your router
app.include_router(nba_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Crypto-NBA Event Intelligence API"}
