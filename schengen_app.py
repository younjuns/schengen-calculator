import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta

st.set_page_config(page_title="Schengen Visa Calculator", layout="wide")
st.title("📅 Schengen Visa 90/180 Day Calculator")

if 'trips' not in st.session_state:
    st.session_state.trips = []

trips = st.session_state.trips

# --- Input Section ---
st.sidebar.header("🕴️ Add a trip")
entry = st.sidebar.date_input("Entry date")
exit = st.sidebar.date_input("Exit date")

if st.sidebar.button("Add Trip"):
    if entry <= exit:
        st.session_state.trips.append({'entry': entry, 'exit': exit})
    else:
        st.sidebar.error("Entry date must be before exit date.")

if st.sidebar.button("Clear Trips"):
    st.session_state.trips = []

trips = st.session_state.trips

# --- Intro Text ---
if not trips:
    st.markdown("""
    Use this app to track your stay in the Schengen Area.
    Enter your **entry and exit dates**, and see a visual breakdown of your used days under the 90/180 rule.
    """)
    st.info("Add some trips using the sidebar to see your chart.")
    st.stop()

# --- Process Trip Data ---
trip_df = pd.DataFrame(trips)
trip_df["entry"] = pd.to_datetime(trip_df["entry"])
trip_df["exit"] = pd.to_datetime(trip_df["exit"])

schengen_days = set()
for _, row in trip_df.iterrows():
    current_day = row["entry"]
    while current_day <= row["exit"]:
        schengen_days.add(current_day)
        current_day += timedelta(days=1)

# --- Create rolling window ---
start_date = trip_df["entry"].min() - timedelta(days=5)
end_date = trip_df["exit"].max() + timedelta(days=365)
date_range = pd.date_range(start=start_date, end=end_date)

rolling_days_used = []
for current_date in date_range:
    window_start = current_date - timedelta(days=179)
    days_in_window = sum(1 for d in schengen_days if window_start <= d <= current_date)
    rolling_days_used.append(days_in_window)

df = pd.DataFrame({"date": date_range, "days_used": rolling_days_used})

# --- Inflection Points ---
inflection_dates = [
    (row["exit"] + timedelta(days=180)).strftime("%Y-%m-%d") for _, row in trip_df.iterrows()
]
inflection_df = df[df["date"].isin(pd.to_datetime(inflection_dates))]

# --- Plotting ---
fig, ax = plt.subplots(figsize=(14, 5))

ax.plot(df["date"], df["days_used"], color="#6A8EAE", linewidth=3, label="Días usados")
ax.axhline(90, color="#FFB5A7", linestyle="--", linewidth=2, label="Límite de 90 días")

for _, row in trip_df.iterrows():
    x_start = mdates.date2num(row["entry"])
    width = (row["exit"] - row["entry"]).days + 1
    rect = Rectangle((x_start, 0), width, 90, facecolor="#FFD6A5", alpha=0.3)
    ax.add_patch(rect)
    ax.annotate("Entrada\n" + row["entry"].strftime("%d %b"), xy=(row["entry"], 0), xytext=(0, 30),
                textcoords="offset points", ha='center', fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#666666"))
    ax.annotate("Salida\n" + row["exit"].strftime("%d %b"), xy=(row["exit"], 0), xytext=(0, -35),
                textcoords="offset points", ha='center', fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#666666"))

for _, row in inflection_df.iterrows():
    ax.annotate(f"{row['days_used']} días\n{row['date'].strftime('%d %b')}",
                xy=(row["date"], row["days_used"]),
                xytext=(0, 30), textcoords="offset points",
                ha='center', fontsize=9, color="#99C1B9",
                arrowprops=dict(arrowstyle="->", color="#99C1B9"))

ax.set_title("Tu uso del visado Schengen (Regla 90/180)", fontsize=16, weight='bold', color="#6A8EAE")
ax.set_xlabel("Fecha", fontsize=12)
ax.set_ylabel("Días usados", fontsize=12)
ax.legend(frameon=False)
ax.grid(True, linestyle="--", alpha=0.3)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)
