"""
generate_data.py
Generates a realistic YouTube Trending Video dataset (US market, 2023–2024).
Run once to create: data/youtube_trending_US.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# ── Config ────────────────────────────────────────────────────────
N = 2000          # total trending records
START = datetime(2023, 1, 1)
END   = datetime(2024, 6, 30)

# ── Categories with realistic engagement profiles ─────────────────
CATEGORIES = {
    "Entertainment":     {"weight": 0.22, "base_views": 3_500_000, "std": 2_000_000},
    "Music":             {"weight": 0.18, "base_views": 5_000_000, "std": 3_500_000},
    "Gaming":            {"weight": 0.14, "base_views": 2_000_000, "std": 1_500_000},
    "Sports":            {"weight": 0.10, "base_views": 2_800_000, "std": 1_800_000},
    "News & Politics":   {"weight": 0.09, "base_views": 1_800_000, "std": 1_200_000},
    "Education":         {"weight": 0.08, "base_views": 1_500_000, "std": 900_000},
    "Comedy":            {"weight": 0.07, "base_views": 2_500_000, "std": 1_600_000},
    "Science & Tech":    {"weight": 0.06, "base_views": 1_200_000, "std": 800_000},
    "Howto & Style":     {"weight": 0.04, "base_views": 1_000_000, "std": 700_000},
    "Film & Animation":  {"weight": 0.02, "base_views": 3_000_000, "std": 2_000_000},
}

# ── Top channels per category ─────────────────────────────────────
CHANNELS = {
    "Entertainment":     ["MrBeast", "DramaAlert", "Jubilee", "Vsauce", "LazarBeam"],
    "Music":             ["Taylor Swift", "BTS HYBE", "Bad Bunny", "Drake VEVO", "The Weeknd"],
    "Gaming":            ["Markiplier", "Jacksepticeye", "Valkyrae", "Ninja", "Dream"],
    "Sports":            ["ESPN", "NBA", "Sky Sports", "Goal", "WWE"],
    "News & Politics":   ["CNN", "BBC News", "MSNBC", "Vice News", "The Young Turks"],
    "Education":         ["CrashCourse", "TED-Ed", "Kurzgesagt", "Veritasium", "3Blue1Brown"],
    "Comedy":            ["Smosh", "The Try Guys", "Dude Perfect", "Lilly Singh", "CollegeHumor"],
    "Science & Tech":    ["Linus Tech Tips", "Marques Brownlee", "Fireship", "TwoMinutePapers", "Wendover Productions"],
    "Howto & Style":     ["Good Mythical Morning", "Tasty", "NikkieTutorials", "James Charles", "SORTEDfood"],
    "Film & Animation":  ["Screen Junkies", "CinemaWins", "MovieClips", "Corridor Crew", "IGN"],
}

# ── Upload hour distribution (peaks at 2pm–4pm EST) ───────────────
HOUR_WEIGHTS = [1, 1, 1, 1, 1, 2, 3, 4, 5, 5, 6, 7,
                8, 9, 10, 10, 9, 8, 6, 5, 4, 3, 2, 1]

# ── Day of week weights (Fri/Sat/Sun higher) ──────────────────────
DOW_WEIGHTS = [6, 5, 5, 6, 8, 9, 7]  # Mon=0 … Sun=6
DOW_NAMES   = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# ── Generate records ──────────────────────────────────────────────
records = []
cat_list   = list(CATEGORIES.keys())
cat_weights = [CATEGORIES[c]["weight"] for c in cat_list]

for _ in range(N):
    cat = random.choices(cat_list, weights=cat_weights)[0]
    cfg = CATEGORIES[cat]

    channel = random.choice(CHANNELS[cat])

    # Random publish date/time
    days_range = (END - START).days
    day_offset = random.choices(range(days_range), weights=None)[0]
    pub_date   = START + timedelta(days=day_offset)
    hour       = random.choices(range(24), weights=HOUR_WEIGHTS)[0]
    pub_dt     = pub_date.replace(hour=hour, minute=random.randint(0,59))

    # Views: log-normal distribution
    views = max(50_000, int(np.random.lognormal(
        mean=np.log(cfg["base_views"]),
        sigma=0.8
    )))

    # Engagement rates
    like_rate    = np.random.uniform(0.03, 0.12)
    comment_rate = np.random.uniform(0.003, 0.02)
    dislike_rate = np.random.uniform(0.001, 0.01)

    likes    = int(views * like_rate)
    comments = int(views * comment_rate)
    dislikes = int(views * dislike_rate)

    # Days to trend (how long after upload did it trend)
    days_to_trend = random.choices([0,1,2,3,4,5,6,7],
                                   weights=[30,25,18,10,7,4,3,3])[0]
    trending_date = pub_dt + timedelta(days=days_to_trend)

    # Title length (chars)
    title_len = random.randint(25, 90)

    # Tags count
    tags = random.randint(5, 30)

    dow = pub_dt.weekday()

    records.append({
        "video_id":         f"vid_{_:05d}",
        "channel_title":    channel,
        "category":         cat,
        "publish_date":     pub_dt.strftime("%Y-%m-%d"),
        "publish_hour":     hour,
        "publish_day_of_week": DOW_NAMES[dow],
        "trending_date":    trending_date.strftime("%Y-%m-%d"),
        "days_to_trend":    days_to_trend,
        "views":            views,
        "likes":            likes,
        "dislikes":         dislikes,
        "comment_count":    comments,
        "title_length":     title_len,
        "tags_count":       tags,
    })

df = pd.DataFrame(records)

# Derived columns
df["like_ratio"]    = (df["likes"] / df["views"]).round(4)
df["comment_ratio"] = (df["comment_count"] / df["views"]).round(4)
df["engagement_score"] = ((df["likes"] + df["comment_count"]) / df["views"]).round(4)

out = os.path.join(os.path.dirname(__file__), "youtube_trending_US.csv")
df.to_csv(out, index=False)
print(f" Dataset saved → {out}")
print(f"    Shape : {df.shape}")
print(f"    Cols  : {list(df.columns)}")
print(df.head(3).to_string())
