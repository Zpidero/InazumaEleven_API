"""Refresh data/players.json, data/techniques.json and data/teams.json.

    uv run python update.py
"""
from app.build import run

if __name__ == "__main__":
    print("⚡ Starting update ⚡\n")
    run()
