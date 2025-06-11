import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates

st.set_page_config(page_title="Schengen Calculator", layout="wide")

st.title("🇪🇺 Schengen Visa Calculator")
st.markdown("Enter your **entry and exit dates**, and see a visual breakdown of your used days under the 90/180 rule.")

# --- Session state for storing trips ---
if "trips" not in st.session_state:
    st.session_state["trips"] = []

# --- Sidebar input form ---
with st.sidebar:
    st.header("✈️ Add a Trip")
    entry_date = st.date_input("Entry Date")
    exit_date = st.date_input("Exit Date")
    if st.button("Add Trip"):
        if entry_date > exit_date:
            st.error("Exit date must be after entry date.")
        else:
            st.session_state["trips"].append({"entry": entry_date, "exit": exit_date})

    # Display trip list
    if st.session_state["trips"]:
        st.subheader("🗂️ Current Trips")
        for i, trip in enumerate(st.session_state["trips"]):
            st.write(f"{i+1}. {trip['entry']} → {trip['exit']}")
            if st.button(f"❌ Remove Trip {i+1}", key=f"remove_{i}"):
                st.session_state["trips"].pop(i)
                st.experimental_rerun()

# --- Main logic and chart ---
trips = [{"entry": pd.to_datetime(t["entry"]), "exit": pd.to_datetime(t["exit"])} for t in st.session_state["trips"]]

if trips:
    # Build set of all Schengen days
    schengen_days = set()
    for trip in trips:
        current_day = trip["entry"]
        while current_day <= trip["exit"]:
            schengen_days.add(current_day)
            current_day += timedelta(days=1)

    # Build full date range
    earliest_entry = min(t["entry"] for t in trips)
    latest_exit = max(t["exit"] for t in trips)
    end_date = latest_exit + timedelta(days=180)
    full_range = pd.date_range(start=earliest_entry - timedelta(days=1), end=end_date)

    # Calculate rolling days used
    rolling_days = []
    for current_date in full_range:
        window_start = current_date - timedelta(days=179)
        used = sum(1 for d in schengen_days if window_start <= d <= current_date)
        rolling_days.append(used)

    df = pd.DataFrame({"date": full_range, "days_used": rolling_days})

    # Create chart
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(df["date"], df["days_used"], color="#3A86FF", linewidth=2.5, label="Días utilizados (últimos 180 días)")
    ax.axhline(90, color="#FF006E", linestyle="--", linewidth=1.5, label="Límite de 90 días")

    for trip in trips:
        x_start = mdates.date2num(trip["entry"])
        x_end = mdates.date2num(trip["exit"])
        width = x_end - x_start
        rect = Rectangle((x_start, 0), width, 90, facecolor="#FFD6A5", alpha=0.3)
        ax.add_patch(rect)
        ax.annotate(f'Entrada\n{trip["entry"].strftime("%d %b")}', xy=(trip["entry"], 0), xytext=(-10, 30),
                    textcoords="offset points", ha='center', fontsize=8, arrowprops=dict(arrowstyle="->"))
        ax.annotate(f'Salida\n{trip["exit"].strftime("%d %b")}', xy=(trip["exit"], 0), xytext=(10, -35),
                    textcoords="offset points", ha='center', fontsize=8, arrowprops=dict(arrowstyle="->"))

    ax.set_title("🗓️ Días utilizados según la regla 90/180", fontsize=16, weight='bold')
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Días utilizados")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    fig.autofmt_xdate()
    st.pyplot(fig)

    # --- 🟢 Summary: When days become available ---
    unlock_dates = [trip["exit"] + timedelta(days=180) for trip in trips]
    summary = []
    for unlock in unlock_dates:
        row = df[df["date"] == unlock]
        if not row.empty:
            used = row.iloc[0]["days_used"]
            available = 90 - used
            summary.append((unlock.strftime('%d %b %Y'), available))

    if summary:
        st.markdown("### 🟢 Additional days become available on:")
        for date_str, available in sorted(summary):
            st.markdown(f"- **{date_str}** — {available} days available")
