"""Streamlit dashboard for The Warden."""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="The Warden - Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark theme and styling
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #ff4b4b;
    }
    .status-pending {
        color: #ffa500;
    }
    .status-completed {
        color: #00cc00;
    }
    .status-failed {
        color: #ff4b4b;
    }
    .pattern-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #ff4b4b;
    }
    .severity-high {
        border-left-color: #ff4b4b;
    }
    .severity-medium {
        border-left-color: #ffa500;
    }
    .severity-low {
        border-left-color: #00cc00;
    }
</style>
""", unsafe_allow_html=True)


# Configuration
API_URL = st.sidebar.text_input("API URL", value="http://localhost:8000")
API_KEY = st.sidebar.text_input("API Key", type="password", value="")

# Headers for API calls
headers = {"X-API-Key": API_KEY} if API_KEY else {}


def make_request(method: str, endpoint: str, data: dict = None):
    """Make API request with error handling."""
    try:
        url = f"{API_URL}/api{endpoint}"
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return None

        if response.status_code == 401:
            st.error("Invalid API key. Check your credentials.")
            return None
        elif response.status_code == 403:
            st.error("Forbidden. Check your API key.")
            return None

        response.raise_for_status()
        return response.json() if response.text else None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_URL}")
        return None
    except Exception as e:
        st.error(f"API error: {str(e)}")
        return None


# Sidebar navigation
st.sidebar.title("🔒 The Warden")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "🎯 Goals", "✅ Commitments", "📋 Check-ins", "⚙️ Settings"],
)


# ============ DASHBOARD PAGE ============
if page == "📊 Dashboard":
    st.title("📊 Accountability Dashboard")

    # Fetch stats
    stats = make_request("GET", "/checkins/stats")

    if stats:
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Completion Rate",
                f"{stats['completion_rate']*100:.1f}%",
                delta=None,
            )

        with col2:
            st.metric(
                "Pending Tasks",
                stats["pending_commitments"],
            )

        with col3:
            st.metric(
                "Response Rate",
                f"{stats['response_rate']*100:.1f}%",
            )

        with col4:
            avg_response = stats.get("average_response_time_hours")
            st.metric(
                "Avg Response Time",
                f"{avg_response:.1f}h" if avg_response else "N/A",
            )

        st.markdown("---")

        # Two column layout
        left_col, right_col = st.columns([2, 1])

        with left_col:
            # Commitment status breakdown
            st.subheader("Commitment Status")

            status_data = {
                "Status": ["Completed", "Pending", "Failed"],
                "Count": [
                    stats["completed_commitments"],
                    stats["pending_commitments"],
                    stats["failed_commitments"],
                ],
            }
            df = pd.DataFrame(status_data)

            fig = px.pie(
                df,
                values="Count",
                names="Status",
                color="Status",
                color_discrete_map={
                    "Completed": "#00cc00",
                    "Pending": "#ffa500",
                    "Failed": "#ff4b4b",
                },
                hole=0.4,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            )
            st.plotly_chart(fig, use_container_width=True)

        with right_col:
            # Active patterns
            st.subheader("🚨 Active Patterns")

            patterns = stats.get("active_patterns", [])
            if patterns:
                for pattern in patterns:
                    severity_class = "severity-high" if pattern["severity"] >= 4 else (
                        "severity-medium" if pattern["severity"] >= 2 else "severity-low"
                    )
                    severity_emoji = "🔴" if pattern["severity"] >= 4 else (
                        "🟡" if pattern["severity"] >= 2 else "🟢"
                    )
                    st.markdown(
                        f"""<div class="pattern-card {severity_class}">
                        <strong>{severity_emoji} {pattern['pattern_type'].upper()}</strong><br>
                        {pattern['description']}
                        </div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No active patterns detected. Stay vigilant.")

        # Recent check-ins
        st.markdown("---")
        st.subheader("Recent Check-ins")

        checkins = make_request("GET", "/checkins?limit=5")
        if checkins:
            for ci in checkins:
                with st.expander(
                    f"{'✅' if ci['response_received'] else '⏳'} {ci['check_in_type']} - {ci['sent_at'][:16]}"
                ):
                    st.write(ci["message_sent"])
                    if ci["response_received"]:
                        st.success(f"Responded at: {ci.get('responded_at', 'N/A')}")
                    else:
                        st.warning("Awaiting response")
        else:
            st.info("No check-ins yet. The Warden is watching...")

    else:
        st.warning("Configure your API URL and key in the sidebar to view dashboard.")


# ============ GOALS PAGE ============
elif page == "🎯 Goals":
    st.title("🎯 Goals")

    # Add new goal form
    with st.expander("➕ Add New Goal", expanded=False):
        with st.form("new_goal"):
            title = st.text_input("Goal Title")
            description = st.text_area("Description (optional)")
            target_date = st.date_input("Target Date (optional)", value=None)

            submitted = st.form_submit_button("Create Goal")
            if submitted and title:
                data = {"title": title}
                if description:
                    data["description"] = description
                if target_date:
                    data["target_date"] = target_date.isoformat()

                result = make_request("POST", "/goals", data)
                if result:
                    st.success("Goal created!")
                    st.rerun()

    # List goals
    st.markdown("---")
    goals = make_request("GET", "/goals?active_only=true")

    if goals:
        for goal in goals:
            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                st.markdown(f"### {goal['title']}")
                if goal.get("description"):
                    st.write(goal["description"])
                if goal.get("target_date"):
                    st.caption(f"Target: {goal['target_date'][:10]}")

            with col2:
                if st.button("📝 Edit", key=f"edit_goal_{goal['id']}"):
                    st.session_state[f"editing_goal_{goal['id']}"] = True

            with col3:
                if st.button("🗑️ Delete", key=f"delete_goal_{goal['id']}"):
                    make_request("DELETE", f"/goals/{goal['id']}")
                    st.rerun()

            st.markdown("---")
    else:
        st.info("No active goals. Create one to get started.")


# ============ COMMITMENTS PAGE ============
elif page == "✅ Commitments":
    st.title("✅ Commitments")

    # Add new commitment form
    with st.expander("➕ Add New Commitment", expanded=False):
        with st.form("new_commitment"):
            title = st.text_input("Commitment Title")
            description = st.text_area("Description (optional)")
            due_date = st.date_input("Due Date (optional)", value=None)

            # Get goals for dropdown
            goals = make_request("GET", "/goals?active_only=true") or []
            goal_options = {g["title"]: g["id"] for g in goals}
            goal_options["None"] = None
            selected_goal = st.selectbox("Link to Goal (optional)", options=list(goal_options.keys()))

            submitted = st.form_submit_button("Create Commitment")
            if submitted and title:
                data = {"title": title}
                if description:
                    data["description"] = description
                if due_date:
                    data["due_date"] = due_date.isoformat()
                if goal_options[selected_goal]:
                    data["goal_id"] = goal_options[selected_goal]

                result = make_request("POST", "/commitments", data)
                if result:
                    st.success("Commitment created!")
                    st.rerun()

    # Filter tabs
    st.markdown("---")
    status_filter = st.radio(
        "Filter by status:",
        ["All", "Pending", "Completed", "Failed", "Deferred"],
        horizontal=True,
    )

    # Map filter to API parameter
    filter_map = {
        "All": None,
        "Pending": "pending",
        "Completed": "completed",
        "Failed": "failed",
        "Deferred": "deferred",
    }
    filter_param = filter_map[status_filter]

    endpoint = "/commitments"
    if filter_param:
        endpoint += f"?status_filter={filter_param}"

    commitments = make_request("GET", endpoint)

    if commitments:
        for commit in commitments:
            status_emoji = {
                "pending": "⏳",
                "completed": "✅",
                "failed": "❌",
                "deferred": "⏸️",
            }.get(commit["status"], "❓")

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.markdown(f"**{status_emoji} {commit['title']}**")
                if commit.get("description"):
                    st.caption(commit["description"])
                if commit.get("due_date"):
                    due = datetime.fromisoformat(commit["due_date"].replace("Z", ""))
                    is_overdue = due < datetime.utcnow() and commit["status"] == "pending"
                    color = "red" if is_overdue else "gray"
                    st.caption(f":{color}[Due: {commit['due_date'][:10]}]")
                if commit.get("deferred_count", 0) > 0:
                    st.caption(f"🔄 Deferred {commit['deferred_count']} times")

            with col2:
                if commit["status"] == "pending":
                    if st.button("✅ Complete", key=f"complete_{commit['id']}"):
                        make_request("POST", f"/commitments/{commit['id']}/complete")
                        st.rerun()

            with col3:
                if commit["status"] == "pending":
                    if st.button("⏸️ Defer", key=f"defer_{commit['id']}"):
                        make_request("POST", f"/commitments/{commit['id']}/defer")
                        st.rerun()

            with col4:
                if st.button("🗑️", key=f"delete_commit_{commit['id']}"):
                    make_request("DELETE", f"/commitments/{commit['id']}")
                    st.rerun()

            st.markdown("---")
    else:
        st.info("No commitments found. Time to make some promises!")


# ============ CHECK-INS PAGE ============
elif page == "📋 Check-ins":
    st.title("📋 Check-in History")

    # Manual trigger buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔔 Trigger Check-in Now"):
            result = make_request("POST", "/trigger/checkin".replace("/api", ""))
            if result:
                st.success("Check-in triggered!")

    with col2:
        if st.button("📊 Trigger Weekly Review"):
            result = make_request("POST", "/trigger/weekly-review".replace("/api", ""))
            if result:
                st.success("Weekly review triggered!")

    st.markdown("---")

    # Check-in history
    checkins = make_request("GET", "/checkins?limit=20")

    if checkins:
        for ci in checkins:
            status_icon = "✅" if ci["response_received"] else "⏳"
            type_emoji = {
                "daily": "☀️",
                "weekly_review": "📊",
                "escalation": "⚠️",
                "deadline_alert": "⏰",
                "manual": "👆",
            }.get(ci["check_in_type"], "📋")

            with st.expander(
                f"{status_icon} {type_emoji} {ci['check_in_type'].replace('_', ' ').title()} - {ci['sent_at'][:16]}"
            ):
                st.markdown("**Message sent:**")
                st.info(ci["message_sent"])

                if ci["response_received"]:
                    st.markdown(f"**Responded at:** {ci.get('responded_at', 'N/A')}")
                else:
                    st.warning("No response yet")
    else:
        st.info("No check-ins recorded yet.")

    # Response history
    st.markdown("---")
    st.subheader("Your Responses")

    responses = make_request("GET", "/checkins/responses?limit=10")

    if responses:
        for resp in responses:
            shipped_icon = "📦" if resp.get("detected_shipped") else ""
            excuse_icon = "🤥" if resp.get("detected_excuse") else ""
            avoidance_icon = "🏃" if resp.get("detected_avoidance") else ""

            icons = " ".join(filter(None, [shipped_icon, excuse_icon, avoidance_icon]))

            with st.expander(f"💬 {resp['received_at'][:16]} {icons}"):
                st.write(resp["message_text"])

                if resp.get("analysis_notes"):
                    st.markdown("**Analysis:**")
                    st.caption(resp["analysis_notes"])
    else:
        st.info("No responses recorded yet.")


# ============ SETTINGS PAGE ============
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")

    # Schedule configuration
    st.subheader("📅 Schedule Configuration")

    schedule = make_request("GET", "/checkins/schedule")

    if schedule:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Daily Check-in**")
            st.write(f"Time: {schedule['daily_checkin_hour']:02d}:{schedule['daily_checkin_minute']:02d}")
            st.caption("Timezone: America/Phoenix")

        with col2:
            st.markdown("**Weekly Review**")
            st.write(f"Day: {schedule['weekly_review_day'].title()}")
            st.write(f"Time: {schedule['weekly_review_hour']:02d}:{schedule['weekly_review_minute']:02d}")

        st.info("To change schedule settings, update environment variables and restart the app.")

    # Detected patterns
    st.markdown("---")
    st.subheader("🔍 All Detected Patterns")

    patterns = make_request("GET", "/checkins/patterns?active_only=false")

    if patterns:
        df_data = []
        for p in patterns:
            df_data.append({
                "Type": p["pattern_type"],
                "Description": p["description"],
                "Severity": "🔴" * min(p["severity"], 5),
                "Active": "✅" if p["is_active"] else "❌",
                "Detected": p["detected_at"][:10],
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No patterns detected yet.")

    # API Test
    st.markdown("---")
    st.subheader("🔌 API Connection")

    if st.button("Test Connection"):
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success(f"Connected to {API_URL}")
                st.json(response.json())
            else:
                st.error(f"API returned status {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {e}")


# Footer
st.sidebar.markdown("---")
st.sidebar.caption("The Warden is watching.")
st.sidebar.caption("What have you shipped today?")
