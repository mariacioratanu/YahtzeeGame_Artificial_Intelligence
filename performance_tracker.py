import json
import datetime
import os

STATS_FILE = "yahtzee_stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_stats(stats_data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats_data, f, indent=2, ensure_ascii=False)

def record_result(player_score, ai_score, comment=""):
    stats = load_stats()
    new_entry = {
        "date": str(datetime.datetime.now())[:19],
        "player_score": player_score,
        "ai_score": ai_score,
        "comment": comment
    }
    stats.append(new_entry)
    save_stats(stats)

def get_performance_summary():
    stats = load_stats()
    if not stats:
        return "Nu exista date inregistrate inca."

    total_games = len(stats)
    total_player_score = sum(entry["player_score"] for entry in stats)
    total_ai_score = sum(entry["ai_score"] for entry in stats)

    avg_player_score = total_player_score / total_games
    avg_ai_score = total_ai_score / total_games

    summary = (
        f"Numar total de jocuri: {total_games}\n"
        f"Scor mediu jucator: {avg_player_score:.2f}\n"
        f"Scor mediu AI: {avg_ai_score:.2f}\n"
    )

    player_wins = sum(1 for entry in stats if entry["player_score"] > entry["ai_score"])
    ai_wins = sum(1 for entry in stats if entry["ai_score"] > entry["player_score"])
    draws = total_games - player_wins - ai_wins

    summary += (
        f"Victoriile jucatorului: {player_wins}\n"
        f"Victoriile AI: {ai_wins}\n"
        f"Egalitati: {draws}\n"
    )
    return summary
