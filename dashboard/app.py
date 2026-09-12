import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")


col1, col2 = st.columns([3, 1])

with col1:
    st.title("ResolveX")
    st.caption("Customer Support Dashboard")

with col2:
    agents = requests.get(f"{API_URL}/agents").json()

    agent_names = {
        agent["name"]: agent["id"]
        for agent in agents
    }

    selected_agent = st.selectbox(
        "Agent",
        list(agent_names.keys())
    )

current_agent_id = agent_names[selected_agent]


stats = requests.get(f"{API_URL}/tickets/stats").json()

st.subheader("Ticket Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total", stats["total"])
col2.metric("Open", stats["open"])
col3.metric("Pending", stats["pending"])
col4.metric("Resolved", stats["resolved"])
col5.metric("Escalated", stats["escalated"])

st.header("Available Tickets")

available_tickets = requests.get(
    f"{API_URL}/tickets/available"
).json()

if not available_tickets:
    st.info("No available tickets.")

for ticket in available_tickets:
    with st.expander(ticket["subject"]):

        st.write(f"**Customer:** {ticket['customer']['name']}")
        st.write(f"**Email:** {ticket['customer']['email']}")
        st.write(f"**Status:** {ticket['status']}")
        st.write(ticket["message"])

        st.caption(f"Created: {ticket['created_at']}")

        if st.button("Claim", key=f"claim_{ticket['id']}"):
            response = requests.patch(
                f"{API_URL}/tickets/{ticket['id']}/claim",
                json={"agent_id": current_agent_id}
            )

            if response.status_code == 200:
                st.success("Ticket claimed!")
                st.rerun()
            else:
                st.error("Could not claim ticket.")

st.header("My Tickets")

my_tickets = requests.get(
    f"{API_URL}/tickets/my",
    params={"agent_id": current_agent_id}
).json()

if not my_tickets:
    st.info("You have no claimed tickets.")

statuses = ["open", "pending", "resolved", "escalated"]

for ticket in my_tickets:
    with st.expander(ticket["subject"]):

        st.write(f"**Customer:** {ticket['customer']['name']}")
        st.write(f"**Email:** {ticket['customer']['email']}")
        st.write(f"**Status:** {ticket['status']}")

        st.write(ticket["message"])

        st.caption(f"Created: {ticket['created_at']}")

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
            if st.button("Update Status", key=f"update_{ticket['id']}"):
                response = requests.patch(
                f"{API_URL}/tickets/{ticket['id']}/status",
                json={"status": new_status}
                )

                if response.status_code == 200:
                    st.success("Status updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Status update failed: {response.text}")

        with col2:
            if st.button("Save Response", key=f"save_{ticket['id']}"):
                requests.patch(
                    f"{API_URL}/tickets/{ticket['id']}/response",
                    json={"response": response_text}
                )
                st.rerun()   

                            

st.divider()
st.header("Knowledge Base")

docs = requests.get(f"{API_URL}/knowledge-base").json()

for d in docs:
    with st.expander(d["title"]):
        st.write(d["content"])
        