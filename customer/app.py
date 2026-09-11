import streamlit as st
import os
import requests

from dotenv import load_dotenv

load_dotenv()
API_URL = os.environ.get("API_URL", "http://localhost:8000")


st.title("ResolveX")

st.header("Submit a Support Ticket")

name = st.text_input("Name", max_chars=50)
email = st.text_input("Email")
subject = st.text_input("Subject", max_chars=100)
message = st.text_area("Message", max_chars=2000)

if st.button("Submit Ticket"):
    response = requests.post(
        f"{API_URL}/tickets",
        json={
            "customer_name": name,
            "customer_email": email,
            "subject": subject,
            "message": message
        }
    )

    if response.status_code == 200:
        ticket = response.json()

        st.success("Ticket submitted successfully!")
        st.write(f"Ticket ID: {ticket['id']}")
        st.write(f"Status: {ticket['status']}")
    else:
        st.error("Something went wrong.")