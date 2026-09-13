import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get(
    "API_URL",
    "http://127.0.0.1:8000"
)

st.set_page_config(
    page_title="ResolveX Admin",
    page_icon="🛠️",
    layout="wide"
)


def login(email, password):
    response = requests.post(
        f"{API_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )

    if response.status_code == 200:
        return response.json()

    return None


def logout():
    st.session_state.clear()
    st.rerun()


def auth_headers():
    return {
        "Authorization": (
            f"Bearer {st.session_state.access_token}"
        )
    }


if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "role" not in st.session_state:
    st.session_state.role = None

if "agent_name" not in st.session_state:
    st.session_state.agent_name = None


# -------------------------
# Login
# -------------------------

if not st.session_state.access_token:

    st.title("ResolveX")
    st.caption("Admin Dashboard")

    st.subheader("Admin Login")

    with st.form("admin_login"):

        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button("Login")

        if submitted:

            if not email or not password:

                st.error(
                    "Please enter your email and password."
                )

            else:

                login_data = login(
                    email,
                    password
                )

                if login_data:

                    if login_data["role"] != "admin":

                        st.error(
                            "This account does not have admin access."
                        )

                    else:

                        st.session_state.access_token = (
                            login_data["access_token"]
                        )

                        st.session_state.role = (
                            login_data["role"]
                        )

                        st.session_state.agent_name = (
                            login_data["name"]
                        )

                        st.rerun()

                else:

                    st.error(
                        "Invalid email or password."
                    )

    st.stop()


# -------------------------
# Header
# -------------------------

col1, col2 = st.columns([3, 1])

with col1:

    st.title("ResolveX Admin")
    st.caption(
        f"Welcome, {st.session_state.agent_name}"
    )

with col2:

    if st.button("Logout"):
        logout()


headers = auth_headers()


# -------------------------
# Statistics
# -------------------------

stats_response = requests.get(
    f"{API_URL}/admin/stats",
    headers=headers
)

if stats_response.status_code == 200:

    stats = stats_response.json()

    st.subheader("System Overview")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric(
        "Total Tickets",
        stats["total_tickets"]
    )

    col2.metric(
        "Open",
        stats["open"]
    )

    col3.metric(
        "Pending",
        stats["pending"]
    )

    col4.metric(
        "Resolved",
        stats["resolved"]
    )

    col5.metric(
        "Escalated",
        stats["escalated"]
    )

    col6.metric(
        "Agents",
        stats["total_agents"]
    )

else:

    if stats_response.status_code == 401:

        st.session_state.clear()
        st.rerun()

    elif stats_response.status_code == 403:

        st.error("Admin access required.")
        st.stop()

    else:

        st.error("Could not load admin statistics.")


# -------------------------
# Agents
# -------------------------

st.divider()

st.header("Agents")

agents_response = requests.get(
    f"{API_URL}/admin/agents",
    headers=headers
)

if agents_response.status_code == 200:

    agents = agents_response.json()

    for agent in agents:

        with st.expander(agent["name"]):

            st.write(
                f"**Email:** {agent['email']}"
            )

            st.write(
                f"**Role:** {agent['role']}"
            )

else:

    st.error("Could not load agents.")


# -------------------------
# Tickets
# -------------------------

st.divider()
st.header("All Tickets")

tickets_response = requests.get(
    f"{API_URL}/admin/tickets",
    headers=headers
)

if tickets_response.status_code == 200:
    tickets = tickets_response.json()

    if not tickets:
        st.info("No tickets found.")

    for ticket in tickets:
        with st.expander(ticket["subject"]):
            st.write(f"**Status:** {ticket['status']}")
            st.write(f"**Customer:** {ticket['customer_name']}")
            st.write(f"**Email:** {ticket['customer_email']}")
            st.write(f"**Message:** {ticket['message']}")

            if ticket["agent_name"]:
                st.write(f"**Assigned Agent:** {ticket['agent_name']}")
            else:
                st.write("**Assigned Agent:** Unassigned")

            if ticket["response"]:
                st.write(f"**Agent Response:** {ticket['response']}")

            st.caption(f"Created: {ticket['created_at']}")

else:
    st.error("Could not load tickets.")