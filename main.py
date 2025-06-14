from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nba_analysis import router as nba_router
from property_impact import router as property_router
from med_analysis import router as med_router
from preprocess import router as preprocess_router
from graph import router as graph_router

app = FastAPI(
    title="Crypto-NBA Event Intelligence API",
    description="Analyzes the impact of cryptocurrency trends on other outcomes and behavior.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://main.d3sl5dh34mbovk.amplifyapp.com", "https://deltautils-1.onrender.com"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "https://main.d3sl5dh34mbovk.amplifyapp.com",
        "https://deltautils-1.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount your router
app.include_router(nba_router)
app.include_router(property_router)
app.include_router(med_router)
app.include_router(preprocess_router)
app.include_router(graph_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Crypto-NBA Event Intelligence API"}
