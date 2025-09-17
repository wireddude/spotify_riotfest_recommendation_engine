#!/usr/bin/env python 
"""
Band Recommender
~~~~~~~~~~~~~~~~


Given:
  • Your Spotify listening history (top tracks)
  • A list of 100+ band names you don't know

Outputs:
  • A ranked list of the bands most similar to your taste
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from dotenv import load_dotenv

# ------------------------------------------------------------------
# 1️⃣ Load Spotify credentials
# ------------------------------------------------------------------
load_dotenv()
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
    sys.exit("❌ Missing credentials in .env file")

# ------------------------------------------------------------------
# 2️⃣ Authenticate (read your top tracks)
# ------------------------------------------------------------------
SCOPE = "user-top-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))

# ------------------------------------------------------------------
# 3️⃣ Build your “taste vector”
# ------------------------------------------------------------------
print("📥 Pulling your top tracks…")
top_tracks = sp.current_user_top_tracks(limit=50, time_range="short_term")["items"]
if not top_tracks:
    sys.exit("❌ No top tracks found. Add some music to Spotify first.")

track_ids = [t["id"] for t in top_tracks]

print("🔎 Fetching audio features…")
features = sp.audio_features(track_ids)

# Keep only the numeric fields we care about
df = pd.DataFrame(features)[["danceability", "energy", "valence", "tempo"]]
user_profile = df.mean().to_dict()
print("\nYour taste vector (mean audio features):")
for k, v in user_profile.items():
    print(f"  {k:<12}: {v:.3f}")

# ------------------------------------------------------------------
# 4️⃣ Load candidate bands
# ------------------------------------------------------------------
if len(sys.argv) < 2:
    sys.exit("Usage: python recommend_bands.py <bands.txt>")

bands_file = sys.argv[1]
with open(bands_file, "r", encoding="utf-8") as f:
    candidates = [line.strip() for line in f if line.strip()]

print(f"\n🔍 Found {len(candidates)} candidate bands.")

# ------------------------------------------------------------------
# 5️⃣ Score each band
# ------------------------------------------------------------------
results = []

def get_artist_id(name):
    """Search Spotify for an artist and return the best match ID."""
    try:
        res = sp.search(q=name, type="artist", limit=1)
        items = res.get("artists", {}).get("items", [])
        return items[0]["id"] if items else None
    except Exception:
        return None

def get_top_track_features(artist_id, limit=5):
    """Return audio features for an artist's top tracks."""
    try:
        top = sp.artist_top_tracks(artist_id)["tracks"][:limit]
        ids = [t["id"] for t in top]
        return sp.audio_features(ids)
    except Exception:
        return []

def cosine_distance(a, b):
    """Cosine distance between two 1‑D numpy arrays."""
    a, b = np.array(a), np.array(b)
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print("\n🏁 Scoring bands…")
for band in tqdm(candidates):
    artist_id = get_artist_id(band)
    if not artist_id:
        continue
    
    # Get top tracks features
    features = get_top_track_features(artist_id)
    if not features:
        continue
    
    # Calculate average features for this artist
    artist_features = pd.DataFrame(features)[["danceability", "energy", "valence", "tempo"]]
    artist_profile = artist_features.mean().to_dict()
    
    # Calculate distance to user profile
    user_vector = [user_profile[f] for f in ["danceability", "energy", "valence", "tempo"]]
    artist_vector = [artist_profile[f] for f in ["danceability", "energy", "valence", "tempo"]]
    
    # Skip if we have NaN values
    if np.isnan(np.sum(artist_vector)):
        continue
    
    distance = cosine_distance(user_vector, artist_vector)
    
    # Get genre info
    artist_info = sp.artist(artist_id)
    genres = artist_info.get("genres", [])
    popularity = artist_info.get("popularity", 0)
    
    results.append({
        "name": band,
        "distance": distance,
        "genres": genres,
        "popularity": popularity,
        "profile": artist_profile
    })
    
    # Avoid rate limiting
    time.sleep(0.1)

# ------------------------------------------------------------------
# 6️⃣ Present results
# ------------------------------------------------------------------
if not results:
    sys.exit("❌ No bands could be analyzed. Check your input file.")

# Sort by similarity (lower distance = more similar)
results.sort(key=lambda x: x["distance"])

# Display top matches
print("\n🎵 Top Recommended Bands:")
for i, band in enumerate(results[:10], 1):
    print(f"{i}. {band['name']}")
    print(f"   Similarity: {1 - band['distance']:.2f}")
    print(f"   Genres: {', '.join(band['genres'][:3])}")
    print(f"   Popularity: {band['popularity']}/100")
    print()

# Save full results to JSON
output_file = os.path.splitext(bands_file)[0] + "_recommendations.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"✅ Full results saved to {output_file}")