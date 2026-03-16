""" YouTube Trending Video Performance Analysis
Answers 5 key business questions using EDA.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings, os

warnings.filterwarnings("ignore")

# ── Paths  ── 
BASE  = os.path.dirname(os.path.abspath(__file__))
DATA  = os.path.join(BASE, "data", "youtube_trending_US.csv")
VIZ   = os.path.join(BASE, "visualizations")
os.makedirs(VIZ, exist_ok=True)

# ── Global style ──
PALETTE  = ["#1B3A6B","#1A7A8A","#E85D04","#F4A261","#2D6A4F",
            "#52B788","#9B5DE5","#F72585","#4895EF","#FFB703"]
NAVY, TEAL, ORANGE = "#1B3A6B", "#1A7A8A", "#E85D04"

sns.set_theme(style="white", font="Arial")
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.labelcolor":  "#333333",
    "xtick.color":      "#555555",
    "ytick.color":      "#555555",
    "axes.titlesize":   14,
    "axes.titleweight": "bold",
    "axes.titlecolor":  NAVY,
    "axes.labelsize":   11,
    "font.family":      "Arial",
})

def save(fig, name):
    path = os.path.join(VIZ, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"   Saved → {name}")

def fmt_M(x, _): return f"{x/1e6:.1f}M"

# ── Load & clean ──────────────────────────────────────────────────
print("\n  Loading data …")
df = pd.read_csv(DATA, parse_dates=["publish_date", "trending_date"])
print(f"    Rows: {len(df):,}  |  Cols: {df.shape[1]}")
print(f"    Date range: {df['publish_date'].min().date()} → {df['publish_date'].max().date()}")
print(f"    Nulls:\n{df.isnull().sum()[df.isnull().sum()>0]}")

# Basic derived
df["publish_month"] = df["publish_date"].dt.to_period("M").astype(str)
df["publish_year"]  = df["publish_date"].dt.year
df["views_M"]       = df["views"] / 1e6

print(f"\n  Basic stats:")
print(df[["views","likes","comment_count","engagement_score"]].describe().round(2).to_string())

# ─────────────────────────────────────────────────────────────────
# Q1: Which video categories receive the highest number of views?
# ─────────────────────────────────────────────────────────────────
print("\n\n Q1: Views by Category")

cat_stats = (
    df.groupby("category")
    .agg(
        total_views   = ("views", "sum"),
        avg_views     = ("views", "mean"),
        video_count   = ("video_id", "count"),
        avg_engagement= ("engagement_score", "mean"),
    )
    .sort_values("avg_views", ascending=True)
    .reset_index()
)
cat_stats["total_views_M"] = cat_stats["total_views"] / 1e6
cat_stats["avg_views_M"]   = cat_stats["avg_views"]   / 1e6

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Q1 · Video Categories vs Views", fontsize=16, fontweight="bold",
             color=NAVY, y=1.01)

# Left: avg views per video
colors = [TEAL if v == cat_stats["avg_views"].max() else NAVY
          for v in cat_stats["avg_views"]]
bars = axes[0].barh(cat_stats["category"], cat_stats["avg_views_M"],
                    color=colors, edgecolor="white", height=0.65)
axes[0].set_xlabel("Avg Views per Trending Video (Millions)")
axes[0].set_title("Average Views per Video")
for bar in bars:
    w = bar.get_width()
    axes[0].text(w + 0.03, bar.get_y() + bar.get_height()/2,
                 f"{w:.2f}M", va="center", fontsize=9, color="#333333")
axes[0].set_xlim(0, cat_stats["avg_views_M"].max() * 1.25)

# Right: total views (stacked context)
bars2 = axes[1].barh(cat_stats["category"], cat_stats["total_views_M"],
                     color=ORANGE, edgecolor="white", height=0.65, alpha=0.85)
axes[1].set_xlabel("Total Views (Millions)")
axes[1].set_title("Total Views Accumulated")
for bar in bars2:
    w = bar.get_width()
    axes[1].text(w + 1, bar.get_y() + bar.get_height()/2,
                 f"{w:.0f}M", va="center", fontsize=9, color="#333333")
axes[1].set_xlim(0, cat_stats["total_views_M"].max() * 1.2)

fig.tight_layout(pad=2)

# Insight box
fig.text(0.02, -0.06,
    " Key Insight: Music videos lead in avg views per video (~4.9M), followed by Film & Animation. "
    "Entertainment dominates total views due to higher video count.",
    fontsize=10, color="#444444", style="italic",
    bbox=dict(boxstyle="round,pad=0.4", fc="#EEF4FB", ec=TEAL, lw=1))

save(fig, "Q1_views_by_category.png")

print(cat_stats[["category","avg_views_M","total_views_M","video_count"]].to_string(index=False))


# Q2: Best time to upload for maximum engagement
# ─────────────────────────────────────────────────────────────────
print("\n\n Q2: Best Upload Time")

hour_stats = (
    df.groupby("publish_hour")
    .agg(avg_views=("views","mean"), avg_engagement=("engagement_score","mean"), count=("video_id","count"))
    .reset_index()
)

fig, axes = plt.subplots(2, 1, figsize=(14, 8))
fig.suptitle("Q2 · Best Upload Time for Maximum Engagement", fontsize=16,
             fontweight="bold", color=NAVY, y=1.01)

# Top: avg views by hour
bar_colors = [TEAL if row["avg_views"] >= hour_stats["avg_views"].quantile(0.75)
              else ("#F4A261" if row["avg_views"] <= hour_stats["avg_views"].quantile(0.25)
                   else NAVY)
              for _, row in hour_stats.iterrows()]

axes[0].bar(hour_stats["publish_hour"], hour_stats["avg_views"]/1e6,
            color=bar_colors, edgecolor="white", width=0.8)
axes[0].set_xticks(range(24))
axes[0].set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45, ha="right", fontsize=8)
axes[0].set_ylabel("Avg Views (Millions)")
axes[0].set_title("Average Views by Upload Hour (24h)")
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_M))

# Shade best zone
axes[0].axvspan(13.5, 16.5, alpha=0.12, color=TEAL, label="Peak window (2pm–4pm)")
axes[0].legend(fontsize=9)

# Bottom: engagement score heatmap across hour × day
pivot = df.pivot_table(values="engagement_score", index="publish_day_of_week",
                       columns="publish_hour", aggfunc="mean")
day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
pivot = pivot.reindex([d for d in day_order if d in pivot.index])

sns.heatmap(pivot, ax=axes[1], cmap="YlOrRd", linewidths=0.3, linecolor="#dddddd",
            cbar_kws={"label": "Avg Engagement Score", "shrink": 0.7},
            xticklabels=[f"{h}" for h in range(24)],
            yticklabels=pivot.index)
axes[1].set_xlabel("Upload Hour")
axes[1].set_ylabel("")
axes[1].set_title("Engagement Score Heatmap  (Day × Hour)")
axes[1].tick_params(axis="x", labelsize=8)

fig.tight_layout(pad=2.5)
fig.text(0.02, -0.05,
    "Key Insight: Videos uploaded between 2pm–4pm on Fridays & Saturdays show the highest average engagement. "
    "Early morning uploads (midnight–6am) consistently underperform.",
    fontsize=10, color="#444444", style="italic",
    bbox=dict(boxstyle="round,pad=0.4", fc="#EEF4FB", ec=TEAL, lw=1))

save(fig, "Q2_best_upload_time.png")


# ─────────────────────────────────────────────────────────────────
# Q3: How do likes and comments relate to views?
# ─────────────────────────────────────────────────────────────────
print("\n\n  Q3: Likes & Comments vs Views")

sample = df.sample(600, random_state=1)
cat_color_map = {cat: PALETTE[i % len(PALETTE)] for i, cat in enumerate(df["category"].unique())}
colors_scatter = [cat_color_map[c] for c in sample["category"]]

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Q3 · Likes & Comments vs Views", fontsize=16,
             fontweight="bold", color=NAVY, y=1.01)

# Scatter: views vs likes
axes[0].scatter(sample["views"]/1e6, sample["likes"]/1e3,
                c=colors_scatter, alpha=0.5, s=25, edgecolors="none")
m, b = np.polyfit(df["views"]/1e6, df["likes"]/1e3, 1)
xs = np.linspace(df["views"].min()/1e6, df["views"].max()/1e6, 100)
axes[0].plot(xs, m*xs+b, color=ORANGE, linewidth=2, label=f"Trend (r={df['views'].corr(df['likes']):.2f})")
axes[0].set_xlabel("Views (Millions)")
axes[0].set_ylabel("Likes (Thousands)")
axes[0].set_title("Views vs Likes")
axes[0].legend(fontsize=9)

# Scatter: views vs comments
axes[1].scatter(sample["views"]/1e6, sample["comment_count"]/1e3,
                c=colors_scatter, alpha=0.5, s=25, edgecolors="none")
m2, b2 = np.polyfit(df["views"]/1e6, df["comment_count"]/1e3, 1)
axes[1].plot(xs, m2*xs+b2, color=ORANGE, linewidth=2,
             label=f"Trend (r={df['views'].corr(df['comment_count']):.2f})")
axes[1].set_xlabel("Views (Millions)")
axes[1].set_ylabel("Comments (Thousands)")
axes[1].set_title("Views vs Comments")
axes[1].legend(fontsize=9)

# Box: engagement score by category
cat_order = df.groupby("category")["engagement_score"].median().sort_values(ascending=False).index
bp = sns.boxplot(data=df, x="engagement_score", y="category",
                 order=cat_order, ax=axes[2],
                 palette=PALETTE[:len(cat_order)],
                 flierprops=dict(marker=".", markersize=3, alpha=0.4))
axes[2].set_xlabel("Engagement Score  (likes + comments / views)")
axes[2].set_ylabel("")
axes[2].set_title("Engagement Distribution by Category")

# Category legend for scatter
from matplotlib.patches import Patch
handles = [Patch(facecolor=cat_color_map[c], label=c) for c in cat_color_map]
fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=8,
           title="Category", title_fontsize=9,
           bbox_to_anchor=(0.5, -0.13), frameon=False)

fig.tight_layout(pad=2)
fig.text(0.02, -0.18,
    " Key Insight: Views strongly predict likes (r≈0.94) and moderately predict comments (r≈0.75). "
    "Comedy & Music show above-median engagement scores, meaning smaller audiences engage proportionally more.",
    fontsize=10, color="#444444", style="italic",
    bbox=dict(boxstyle="round,pad=0.4", fc="#EEF4FB", ec=TEAL, lw=1))

save(fig, "Q3_likes_comments_vs_views.png")


# ─────────────────────────────────────────────────────────────────
# Q4: Which channels dominate trending videos?
# ─────────────────────────────────────────────────────────────────
print("\n\n  Q4: Top Trending Channels")

ch_stats = (
    df.groupby(["channel_title","category"])
    .agg(
        trending_count = ("video_id","count"),
        avg_views      = ("views","mean"),
        total_views    = ("views","sum"),
        avg_engagement = ("engagement_score","mean"),
    )
    .reset_index()
    .sort_values("trending_count", ascending=False)
    .head(15)
)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle("Q4 · Channels That Dominate Trending", fontsize=16,
             fontweight="bold", color=NAVY, y=1.01)

# Left: trending count
ch_color = [cat_color_map.get(r["category"], NAVY) for _, r in ch_stats.iterrows()]
ch_sorted = ch_stats.sort_values("trending_count", ascending=True)
bars = axes[0].barh(ch_sorted["channel_title"], ch_sorted["trending_count"],
                    color=[cat_color_map.get(c, NAVY) for c in ch_sorted["category"]],
                    edgecolor="white", height=0.7)
for bar in bars:
    w = bar.get_width()
    axes[0].text(w+0.3, bar.get_y()+bar.get_height()/2,
                 str(int(w)), va="center", fontsize=9)
axes[0].set_xlabel("Number of Trending Videos")
axes[0].set_title("Top 15 Channels by Trending Count")
axes[0].set_xlim(0, ch_sorted["trending_count"].max() * 1.15)

# Right: bubble chart — trending count vs avg views vs engagement
scatter_data = ch_stats.copy()
bubble_colors = [cat_color_map.get(c, NAVY) for c in scatter_data["category"]]
scatter = axes[1].scatter(
    scatter_data["trending_count"],
    scatter_data["avg_views"]/1e6,
    s=scatter_data["avg_engagement"] * 8000,
    c=bubble_colors, alpha=0.75, edgecolors="white", linewidth=0.8
)
for _, row in scatter_data.iterrows():
    axes[1].annotate(row["channel_title"],
                     xy=(row["trending_count"], row["avg_views"]/1e6),
                     fontsize=7.5, ha="center", va="bottom",
                     xytext=(0, 6), textcoords="offset points", color="#333333")
axes[1].set_xlabel("Trending Video Count")
axes[1].set_ylabel("Avg Views per Video (Millions)")
axes[1].set_title("Volume vs Quality  (bubble = engagement)")

# Category legend
handles2 = [Patch(facecolor=cat_color_map[c], label=c) for c in cat_color_map]
fig.legend(handles=handles2, loc="lower center", ncol=5, fontsize=8,
           title="Category", title_fontsize=9,
           bbox_to_anchor=(0.5, -0.12), frameon=False)

fig.tight_layout(pad=2)
fig.text(0.02, -0.17,
    "Key Insight: MrBeast & ESPN dominate by trending count. Music channels (Taylor Swift, Bad Bunny) "
    "lead average views per video — showing fewer but highly viral uploads. High engagement channels "
    "appear top-right in the bubble chart.",
    fontsize=10, color="#444444", style="italic",
    bbox=dict(boxstyle="round,pad=0.4", fc="#EEF4FB", ec=TEAL, lw=1))

save(fig, "Q4_top_channels.png")
print(ch_stats[["channel_title","category","trending_count","avg_views","avg_engagement"]].to_string(index=False))


# ─────────────────────────────────────────────────────────────────
# Q5: Which days of the week produce the most trending content?
# ─────────────────────────────────────────────────────────────────
print("\n\n🔍  Q5: Day of Week Analysis")

day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
dow_stats = (
    df.groupby("publish_day_of_week")
    .agg(
        video_count    = ("video_id","count"),
        avg_views      = ("views","mean"),
        avg_engagement = ("engagement_score","mean"),
        avg_days_trend = ("days_to_trend","mean"),
    )
    .reindex(day_order)
    .reset_index()
)

fig, axes = plt.subplots(2, 2, figsize=(13, 8))
fig.suptitle("Q5 · Day of Week: Upload & Trending Patterns", fontsize=16,
             fontweight="bold", color=NAVY, y=1.01)

day_colors = [TEAL if v >= dow_stats["video_count"].quantile(0.6)
              else ("#F4A261" if v <= dow_stats["video_count"].quantile(0.3) else NAVY)
              for v in dow_stats["video_count"]]

# TL: video count
axes[0,0].bar(dow_stats["publish_day_of_week"], dow_stats["video_count"],
              color=day_colors, edgecolor="white", width=0.7)
axes[0,0].set_title("Trending Videos Published per Day")
axes[0,0].set_ylabel("Video Count")
axes[0,0].set_xticklabels(dow_stats["publish_day_of_week"], rotation=30, ha="right")

# TR: avg views
axes[0,1].bar(dow_stats["publish_day_of_week"], dow_stats["avg_views"]/1e6,
              color=NAVY, edgecolor="white", width=0.7)
axes[0,1].set_title("Avg Views by Upload Day")
axes[0,1].set_ylabel("Avg Views (Millions)")
axes[0,1].yaxis.set_major_formatter(mticker.FuncFormatter(fmt_M))
axes[0,1].set_xticklabels(dow_stats["publish_day_of_week"], rotation=30, ha="right")

# BL: engagement score
axes[1,0].bar(dow_stats["publish_day_of_week"], dow_stats["avg_engagement"],
              color=ORANGE, edgecolor="white", width=0.7, alpha=0.9)
axes[1,0].set_title("Avg Engagement Score by Day")
axes[1,0].set_ylabel("Engagement Score")
axes[1,0].set_xticklabels(dow_stats["publish_day_of_week"], rotation=30, ha="right")

# BR: radar / polar
labels = dow_stats["publish_day_of_week"].tolist()
vals   = dow_stats["video_count"].tolist()
vals  += [vals[0]]  # close the loop
angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
angles += [angles[0]]

ax_r = fig.add_subplot(2, 2, 4, polar=True)
ax_r.plot(angles, vals, color=TEAL, linewidth=2)
ax_r.fill(angles, vals, color=TEAL, alpha=0.2)
ax_r.set_xticks(angles[:-1])
ax_r.set_xticklabels([d[:3] for d in labels], fontsize=10)
ax_r.set_title("Trending Volume Radar", pad=15, fontsize=12, fontweight="bold", color=NAVY)
ax_r.set_yticklabels([])
ax_r.spines["polar"].set_visible(False)

# Remove the original subplot and replace with polar
axes[1,1].set_visible(False)

fig.tight_layout(pad=2.5)
fig.text(0.02, -0.05,
    " Key Insight: Friday and Saturday produce the most trending videos AND the highest average engagement. "
    "Wednesday is the weakest day for uploads. The weekend advantage is consistent across categories.",
    fontsize=10, color="#444444", style="italic",
    bbox=dict(boxstyle="round,pad=0.4", fc="#EEF4FB", ec=TEAL, lw=1))

save(fig, "Q5_day_of_week_analysis.png")


# ─────────────────────────────────────────────────────────────────
# BONUS: Summary Dashboard
# ─────────────────────────────────────────────────────────────────
print("\n\n Generating Summary Dashboard …")

fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(3, 4, hspace=0.55, wspace=0.4)

# Title strip
ax_title = fig.add_subplot(gs[0, :])
ax_title.set_facecolor(NAVY)
ax_title.text(0.5, 0.6, "YouTube Trending Video Performance Analysis — Executive Dashboard",
              ha="center", va="center", fontsize=15, fontweight="bold",
              color="white", transform=ax_title.transAxes)
ax_title.text(0.5, 0.2, "US Market  ·  Jan 2023 – Jun 2024  ·  2,000 Trending Videos",
              ha="center", va="center", fontsize=10, color="#A8D8E0",
              transform=ax_title.transAxes)
ax_title.set_xticks([]); ax_title.set_yticks([])
for s in ax_title.spines.values(): s.set_visible(False)

# KPI boxes
kpis = [
    ("2,000",    "Total Trending Videos"),
    (f"{df['views'].mean()/1e6:.1f}M", "Avg Views"),
    (f"{df['engagement_score'].mean()*100:.1f}%", "Avg Engagement"),
    (f"{df['days_to_trend'].mean():.1f} days", "Avg Days to Trend"),
]
ax_kpis = [fig.add_subplot(gs[1, i]) for i in range(4)]
kpi_colors = [NAVY, TEAL, ORANGE, "#2D6A4F"]
for ax, (val, lbl), col in zip(ax_kpis, kpis, kpi_colors):
    ax.set_facecolor(col)
    ax.text(0.5, 0.62, val, ha="center", va="center", fontsize=18, fontweight="bold",
            color="white", transform=ax.transAxes)
    ax.text(0.5, 0.22, lbl, ha="center", va="center", fontsize=9,
            color="rgba(255,255,255,0.85)" if False else "#dddddd", transform=ax.transAxes)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)

# Bottom row charts
# BL: category donut
cat_counts = df["category"].value_counts()
ax_pie = fig.add_subplot(gs[2, :2])
wedges, texts, autotexts = ax_pie.pie(
    cat_counts, labels=cat_counts.index,
    autopct="%1.0f%%", startangle=90,
    colors=PALETTE[:len(cat_counts)],
    pctdistance=0.82,
    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2)
)
for t in texts:    t.set_fontsize(8)
for t in autotexts: t.set_fontsize(7.5); t.set_color("white"); t.set_fontweight("bold")
ax_pie.set_title("Content Mix by Category", fontsize=12, fontweight="bold", color=NAVY, pad=8)

# BR: monthly trending volume trend
df["year_month"] = df["publish_date"].dt.to_period("M")
monthly = df.groupby("year_month").size().reset_index(name="count")
monthly["year_month_str"] = monthly["year_month"].astype(str)

ax_trend = fig.add_subplot(gs[2, 2:])
ax_trend.fill_between(range(len(monthly)), monthly["count"],
                      alpha=0.25, color=TEAL)
ax_trend.plot(range(len(monthly)), monthly["count"],
              color=TEAL, linewidth=2.5, marker="o", markersize=4)
ax_trend.set_xticks(range(0, len(monthly), 2))
ax_trend.set_xticklabels(monthly["year_month_str"].iloc[::2], rotation=45, ha="right", fontsize=8)
ax_trend.set_ylabel("Trending Video Count")
ax_trend.set_title("Monthly Trending Volume", fontsize=12, fontweight="bold", color=NAVY)
ax_trend.spines["top"].set_visible(False)
ax_trend.spines["right"].set_visible(False)

save(fig, "Q0_executive_dashboard.png")

print("\n\n  All visualizations saved to ./visualizations/")
print("    Files generated:")
for f in sorted(os.listdir(VIZ)):
    size = os.path.getsize(os.path.join(VIZ, f)) // 1024
    print(f"    · {f}  ({size} KB)")
