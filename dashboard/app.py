import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.title("ResolveX")


stats = requests.get(f"{API_URL}/tickets/stats").json()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total", stats["total"])
col2.metric("Open", stats["open"])
col3.metric("Pending", stats["pending"])
col4.metric("Resolved", stats["resolved"])
col5.metric("Escalated", stats["escalated"])


# --- Ticket list with filter ---

status_filter = st.selectbox(
    "Filter by status",
    ["all", "open", "pending", "resolved", "escalated"]
)

params = {} if status_filter == "all" else {"status": status_filter}

tickets = requests.get(
    f"{API_URL}/tickets",
    params=params
).json()

statuses = ["open", "pending", "resolved", "escalated"]


for t in tickets:

    with st.expander(f"{t['subject']} — {t['status']}"):

        st.write(t["message"])


        new_status = st.selectbox(
            "Change status",
            statuses,
            index=statuses.index(t["status"]),
            key=f"status_{t['id']}"
        )

        if st.button("Update status", key=f"update_{t['id']}"):
            requests.patch(
                f"{API_URL}/tickets/{t['id']}/status",
                json={"status": new_status}
            )
            st.rerun()

        response_text = st.text_area(
            "Write a response",
            value=t.get("response") or "",
            key=f"response_{t['id']}"
        )

        if st.button("Save response", key=f"save_{t['id']}"):
            requests.patch(
                f"{API_URL}/tickets/{t['id']}/response",
                json={"response": response_text}
            )
            st.rerun()


st.header("Knowledge Base")

docs = requests.get(f"{API_URL}/knowledge-base").json()

for d in docs:
    with st.expander(d["title"]):
        st.write(d["content"])