from dotenv import load_dotenv
import os

load_dotenv()

OMDB_KEY = os.getenv("OMDB_KEY")
TMDB_KEY = os.getenv("TMDB_KEY")
bearer_key = os.getenv("bearer_key")

tmdb_headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {bearer_key}"
}
