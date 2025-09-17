# Spotify Festival Band Recommendation Engine

This tool helps you discover bands you might like from a festival lineup or any list of bands, based on your personal Spotify listening history.

## How it Works

1. Connects to your Spotify account to analyze your top tracks
2. Creates a "taste profile" based on your most common music genres and artist popularity
3. Analyzes each band from your input list for genre similarity
4. Ranks bands by overall similarity to your musical taste
5. Outputs recommendations and saves detailed results

## Note on Spotify API Changes

As of September 2023, Spotify has deprecated several API endpoints including Audio Features and Recommendations. This tool has been updated to use genre-based similarity and popularity comparisons instead of audio feature analysis.

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a Spotify Developer account at https://developer.spotify.com/dashboard/
4. Create a new application to get your Client ID and Client Secret
5. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   cp .env.example .env
   ```
6. Edit the `.env` file with your Spotify API credentials

## Usage

```bash
python spotify_recommendations.py bands.txt
```

Where `bands.txt` is a text file with one band name per line.

## Output

The program will:
- Display your musical taste profile
- Show the top 10 recommended bands with similarity scores
- Save complete results to a JSON file

## Requirements

- Python 3.7+
- A Spotify account
- Spotify API credentials