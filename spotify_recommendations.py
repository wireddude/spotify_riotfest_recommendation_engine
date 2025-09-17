#!/usr/bin/env python 
"""
Band Recommender
~~~~~~~~~~~~~~~~

Given:
  • Your Spotify listening history (top tracks)
  • A list of 100+ band names you don't know

Outputs:
  • A ranked list of the bands most similar to your taste

Note: This version uses genre matching and popularity metrics instead of audio features
due to Spotify API deprecations as of September 2023.
"""

import os
import sys
import time
import json
from collections import Counter
import numpy as np
import pandas as pd
from tqdm import tqdm
import spotipy
from spotipy.oauth2 import SpotifyOAuth
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
spo_auth = SpotifyOAuth(scope=SCOPE, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI)
sp = spotipy.Spotify(auth_manager=spo_auth)

# ------------------------------------------------------------------
# 3️⃣ Build your "taste profile" based on genres and popularity
# ------------------------------------------------------------------
print("📥 Pulling your top tracks…")
top_tracks = sp.current_user_top_tracks(limit=50, time_range="short_term")["items"]
if not top_tracks:
    sys.exit("❌ No top tracks found. Add some music to Spotify first.")

# Get artists from top tracks
top_artists_ids = list(set([t["artists"][0]["id"] for t in top_tracks]))
top_artists_info = [sp.artist(artist_id) for artist_id in top_artists_ids[:20]]  # Limit to avoid rate limits

# Extract genres and calculate average popularity
all_genres = []
for artist in top_artists_info:
    all_genres.extend(artist.get("genres", []))

# Create user profile based on genre frequency and average popularity
genre_counts = Counter(all_genres)
total_genres = sum(genre_counts.values())
user_genres = {genre: count/total_genres for genre, count in genre_counts.most_common(10)}
user_popularity = np.mean([artist["popularity"] for artist in top_artists_info])

print("\nYour top genres:")
for genre, weight in user_genres.items():
    print(f"  {genre:<20}: {weight:.3f}")
print(f"\nYour average artist popularity: {user_popularity:.1f}/100")

# ------------------------------------------------------------------
# 4️⃣ Load candidate bands
# ------------------------------------------------------------------
if len(sys.argv) < 2:
    sys.exit("Usage: python spotify_recommendations.py <bands.txt>")

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

def jaccard_similarity(set1, set2):
    """Calculate Jaccard similarity between two sets (overlap / union)."""
    if not set1 or not set2:
        return 0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0

print("\n🏁 Scoring bands…")
for band in tqdm(candidates):
    artist_id = get_artist_id(band)
    if not artist_id:
        continue
    
    # Get artist info including genres
    try:
        artist_info = sp.artist(artist_id)
        
        # Calculate genre similarity
        artist_genres = set(artist_info.get("genres", []))
        user_genre_set = set(user_genres.keys())
        genre_sim = jaccard_similarity(artist_genres, user_genre_set)
        
        # Calculate popularity similarity
        artist_popularity = artist_info.get("popularity", 0)
        pop_diff = abs(artist_popularity - user_popularity) / 100
        pop_sim = 1 - pop_diff
        
        # Combined similarity score (70% genre, 30% popularity)
        similarity = (genre_sim * 0.7) + (pop_sim * 0.3)
        
        results.append({
            "name": band,
            "similarity": similarity,
            "genres": artist_info.get("genres", []),
            "popularity": artist_popularity
        })
    except Exception as e:
        print(f"Error processing {band}: {str(e)}")
    
    # Avoid rate limiting
    time.sleep(0.1)

# ------------------------------------------------------------------
# 6️⃣ Present results
# ------------------------------------------------------------------
if not results:
    sys.exit("❌ No bands could be analyzed. Check your input file.")

# Sort by similarity (higher = more similar)
results.sort(key=lambda x: x["similarity"], reverse=True)

# Display top matches
print("\n🎵 Top Recommended Bands:")
for i, band in enumerate(results[:10], 1):
    print(f"{i}. {band['name']}")
    print(f"   Similarity: {band['similarity']:.2f}")
    print(f"   Genres: {', '.join(band['genres'][:3])}")
    print(f"   Popularity: {band['popularity']}/100")
    print()

# Save full results to JSON
output_file = os.path.splitext(bands_file)[0] + "_recommendations.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"✅ Full results saved to {output_file}")