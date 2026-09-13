
import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="ResolveX",
    page_icon="🎫",
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
        "Authorization": f"Bearer {st.session_state.access_token}"
    }

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "agent_id" not in st.session_state:
    st.session_state.agent_id = None

if "agent_name" not in st.session_state:
    st.session_state.agent_name = None

if "agent_email" not in st.session_state:
    st.session_state.agent_email = None

if not st.session_state.access_token:

    st.title("ResolveX")
    st.caption("Customer Support Dashboard")

    st.subheader("Agent Login")

    with st.form("login_form"):

        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button("Login")

        if submitted:

            if not email or not password:
                st.error("Please enter your email and password.")

            else:

                login_data = login(
                    email,
                    password
                )

                if login_data:

                    st.session_state.access_token = (
                        login_data["access_token"]
                    )

                    st.session_state.agent_id = (
                        login_data["agent_id"]
                    )

                    st.session_state.agent_name = (
                        login_data["name"]
                    )

                    st.session_state.agent_email = (
                        login_data["email"]
                    )

                    st.rerun()

                else:
                    st.error("Invalid email or password.")

    st.stop()


col1, col2 = st.columns([3, 1])

with col1:

    st.title("ResolveX")
    st.caption("Customer Support Dashboard")

    st.write(
        f"Welcome, **{st.session_state.agent_name}**"
    )

with col2:

    if st.button("Logout"):
        logout()


headers = auth_headers()

stats_response = requests.get(
    f"{API_URL}/tickets/stats",
    headers=headers
)

if stats_response.status_code == 200:

    stats = stats_response.json()

    st.subheader("Ticket Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total", stats["total"])
    col2.metric("Open", stats["open"])
    col3.metric("Pending", stats["pending"])
    col4.metric("Resolved", stats["resolved"])
    col5.metric("Escalated", stats["escalated"])

else:

    if stats_response.status_code == 401:
        st.session_state.clear()
        st.rerun()

    st.error("Could not load ticket statistics.")


st.header("Available Tickets")

available_response = requests.get(
    f"{API_URL}/tickets/available",
    headers=headers
)

if available_response.status_code == 200:

    available_tickets = available_response.json()

    if not available_tickets:
        st.info("No available tickets.")

    for ticket in available_tickets:

        with st.expander(ticket["subject"]):

            st.write(
                f"**Customer:** {ticket['customer']['name']}"
            )

            st.write(
                f"**Email:** {ticket['customer']['email']}"
            )

            st.write(
                f"**Status:** {ticket['status']}"
            )

            st.write(ticket["message"])

            st.caption(
                f"Created: {ticket['created_at']}"
            )

            if st.button(
                "Claim",
                key=f"claim_{ticket['id']}"
            ):

                response = requests.patch(
                    f"{API_URL}/tickets/{ticket['id']}/claim",
                    json={
                        "agent_id": st.session_state.agent_id
                    },
                    headers=headers
                )

                if response.status_code == 200:

                    st.success("Ticket claimed!")
                    st.rerun()

                elif response.status_code == 401:

                    st.session_state.clear()
                    st.rerun()

                else:

                    st.error(
                        f"Could not claim ticket: "
                        f"{response.text}"
                    )

else:

    st.error("Could not load available tickets.")


st.header("My Tickets")

my_response = requests.get(
    f"{API_URL}/tickets/my",
    headers=headers
)

if my_response.status_code == 200:

    my_tickets = my_response.json()

    if not my_tickets:
        st.info("You have no claimed tickets.")

    statuses = [
        "open",
        "pending",
        "resolved",
        "escalated"
    ]

    for ticket in my_tickets:

        with st.expander(ticket["subject"]):

            st.write(
                f"**Customer:** {ticket['customer']['name']}"
            )

            st.write(
                f"**Email:** {ticket['customer']['email']}"
            )

            st.write(
                f"**Status:** {ticket['status']}"
            )

            st.write(ticket["message"])

            st.caption(
                f"Created: {ticket['created_at']}"
            )

            new_status = st.selectbox(
                "Status",
                statuses,
                index=statuses.index(ticket["status"]),
                key=f"status_{ticket['id']}"
            )

            response_text = st.text_area(
                "Response",
                value=ticket.get("response") or "",
                key=f"response_{ticket['id']}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Update Status",
                    key=f"update_{ticket['id']}"
                ):

                    response = requests.patch(
                        f"{API_URL}/tickets/{ticket['id']}/status",
                        json={
                            "status": new_status
                        },
                        headers=headers
                    )

                    if response.status_code == 200:

                        st.success(
                            "Status updated successfully!"
                        )

                        st.rerun()

                    elif response.status_code == 401:

                        st.session_state.clear()
                        st.rerun()

                    else:

                        st.error(
                            f"Status update failed: "
                            f"{response.text}"
                        )

            with col2:

                if st.button(
                    "Save Response",
                    key=f"save_{ticket['id']}"
                ):

                    response = requests.patch(
                        f"{API_URL}/tickets/{ticket['id']}/response",
                        json={
                            "response": response_text
                        },
                        headers=headers
                    )

                    if response.status_code == 200:

                        st.success(
                            "Response saved successfully!"
                        )

                        st.rerun()

                    elif response.status_code == 401:

                        st.session_state.clear()
                        st.rerun()

                    else:

                        st.error(
                            f"Response update failed: "
                            f"{response.text}"
                        )

else:

    if my_response.status_code == 401:

        st.session_state.clear()
        st.rerun()

    else:

        st.error("Could not load your tickets.")


st.divider()

st.header("Knowledge Base")

docs_response = requests.get(
    f"{API_URL}/knowledge-base",
    headers=headers
)

if docs_response.status_code == 200:

    docs = docs_response.json()

    for d in docs:

        with st.expander(d["title"]):
            st.write(d["content"])

else:

    st.error("Could not load knowledge base.")