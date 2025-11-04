import os
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import Recommendation, SuggestionItem
from database import create_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MoodRequest(BaseModel):
    mood: str
    message: str | None = None

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# Static list of curated radios (HTTPS streams where possible)
RADIOS: List[dict] = [
    {
        "name": "TruckersFM",
        "stream_url": "https://radio.truckers.fm/stream",
        "genre": "Gaming / Community",
        "country": "UK"
    },
    {
        "name": "1.FM - Top 40",
        "stream_url": "https://strm112.1.fm/top40_64?aw_0_1st.playerid=1fmweb",
        "genre": "Top 40 / Pop",
        "country": "International"
    },
    {
        "name": "SomaFM Groove Salad",
        "stream_url": "https://ice6.somafm.com/groovesalad-128-mp3",
        "genre": "Ambient / Downtempo",
        "country": "USA"
    },
    {
        "name": "LoFi HipHop Radio",
        "stream_url": "https://streams.ilovemusic.de/iloveradio15.mp3",
        "genre": "LoFi / Beats",
        "country": "DE"
    }
]

@app.get("/api/radios")
def get_radios():
    return {"radios": RADIOS}

MOOD_MIX = {
    "happy": [
        ("Pharrell Williams - Happy", "ZbZSe6N_BXs"),
        ("Avicii - Levels", "_ovdm2yX4MA"),
        ("Daft Punk - One More Time", "FGBhQbmPwH8")
    ],
    "sad": [
        ("Adele - Someone Like You", "hLQl3WQQoQ0"),
        ("Lewis Capaldi - Someone You Loved", "zABLecsR5UE"),
        ("Billie Eilish - when the party's over", "pbMwTqkKSps")
    ],
    "chill": [
        ("Joji - Glimpse of Us", "NgsWGfUlwJI"),
        ("ODESZA - A Moment Apart", "aQkPcPqTq4M"),
        ("Lauv - I Like Me Better", "BXa8JqZrK30")
    ],
    "focus": [
        ("lofi hip hop mix - beats to study/relax to", "jfKfPfyJRdk"),
        ("Tycho - Awake", "t1tG0K3tQFQ"),
        ("Aphex Twin - Avril 14th", "MBFXJw7n-fU")
    ],
    "party": [
        ("David Guetta - Titanium", "JRfuAukYTKg"),
        ("Calvin Harris - Feel So Close", "dGghkjpNCQ8"),
        ("Black Eyed Peas - I Gotta Feeling", "uSD4vsh1zDA")
    ]
}

@app.post("/api/agent/suggest")
def suggest_music(req: MoodRequest):
    mood_key = (req.mood or "").strip().lower()
    # Map similar moods
    aliases = {
        "good": "happy",
        "great": "happy",
        "awesome": "happy",
        "excited": "party",
        "energetic": "party",
        "ok": "chill",
        "fine": "chill",
        "relaxed": "chill",
        "study": "focus",
        "work": "focus",
        "sad": "sad",
        "down": "sad",
    }
    mood = aliases.get(mood_key, mood_key if mood_key in MOOD_MIX else "chill")

    picks = MOOD_MIX.get(mood, MOOD_MIX["chill"])[:5]
    suggestions = [
        SuggestionItem(
            title=title,
            source="youtube",
            id=vid,
            thumbnail=f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            meta={"mood": mood}
        ) for title, vid in picks
    ]

    # Also include a radio or two that fit the mood
    if mood in ("chill", "focus"):
        radios = [r for r in RADIOS if "Groove" in r["name"] or "LoFi" in r["name"]]
    elif mood in ("party", "happy"):
        radios = [r for r in RADIOS if r["name"] in ("TruckersFM", "1.FM - Top 40")]
    else:
        radios = [RADIOS[0]]

    for r in radios:
        suggestions.append(SuggestionItem(title=r["name"], source="radio", stream_url=r["stream_url"]))

    rec = Recommendation(mood=mood, message=req.message, suggestions=suggestions)

    # Try to persist the recommendation history (best-effort)
    try:
        create_document("recommendation", rec)
    except Exception:
        pass

    return {"mood": mood, "suggestions": [s.model_dump() for s in suggestions]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
