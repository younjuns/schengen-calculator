# 📅 Show unlock dates and how many days will be available

# Only run if trips have been added
if trips:
    # Rebuild date range with all Schengen days used
    schengen_days = set()
    for trip in trips:
        current_day = trip["entry"]
        while current_day <= trip["exit"]:
            schengen_days.add(current_day)
            current_day += timedelta(days=1)

    # Create full rolling calendar
    earliest_entry = min(trip["entry"] for trip in trips)
    latest_unlock = max(trip["exit"] for trip in trips) + timedelta(days=180)
    calendar_dates = pd.date_range(start=earliest_entry - timedelta(days=1), end=latest_unlock)
    usage = []
    for current_date in calendar_dates:
        window_start = current_date - timedelta(days=179)
        used = sum(1 for d in schengen_days if window_start <= d <= current_date)
        usage.append(used)
    df = pd.DataFrame({"date": calendar_dates, "days_used": usage})

    # Compute unlock dates (180 days after each trip's exit)
    unlock_dates = [trip["exit"] + timedelta(days=180) for trip in trips]
    summary_points = []
    for unlock in unlock_dates:
        row = df[df["date"] == unlock]
        if not row.empty:
            days_used = row["days_used"].values[0]
            available = 90 - days_used
            summary_points.append((unlock, available))

    # Display in app
    if summary_points:
        st.markdown("### 🟢 Additional days become available on:")
        for d, avail in sorted(summary_points):
            st.markdown(f"- **{d.strftime('%d %b %Y')}** — {avail} days available")
