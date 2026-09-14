import os

import requests
import streamlit as st

from dotenv import load_dotenv


load_dotenv()


API_URL = os.environ.get(
    "API_URL",
    "http://127.0.0.1:8000"
)


def get_current_user():
    token = st.session_state.get("access_token")

    if not token:
        return None

    response = requests.get(
        f"{API_URL}/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    if response.status_code == 200:
        return response.json()

    st.session_state.clear()
    return None


def get_auth_headers():
    return {
        "Authorization": (
            f"Bearer "
            f"{st.session_state['access_token']}"
        )
    }


st.title("ResolveX")
st.caption("Local learning demo")


if "access_token" not in st.session_state:

    st.header("Sign in")

    email = st.text_input("Email")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Sign in"):

        response = requests.post(
            f"{API_URL}/v1/auth/login",
            json={
                "email": email,
                "password": password
            }
        )

        if response.status_code == 200:

            data = response.json()

            st.session_state["access_token"] = (
                data["access_token"]
            )

            st.session_state["current_view"] = (
                "My requests"
            )

            st.session_state["ticket_page"] = 1

            st.rerun()

        else:
            st.error("Invalid email or password")


else:

    user = get_current_user()

    if user:

        if user["role"] != "customer":

            st.error(
                "You do not have access to the customer portal."
            )

            if st.button("Sign out"):
                st.session_state.clear()
                st.rerun()

        else:

            if "current_view" not in st.session_state:
                st.session_state["current_view"] = (
                    "My requests"
                )

            if (
                "ticket_page" not in st.session_state
                or not isinstance(st.session_state["ticket_page"], int)
            ):
                st.session_state["ticket_page"] = 1

            if "search" not in st.session_state:
                st.session_state["search"] = ""

            if "status" not in st.session_state:
                st.session_state["status"] = "All"

            current_view = st.session_state[
                "current_view"
            ]

            st.sidebar.title("ResolveX")

            st.sidebar.write(
                f"**{user['name']}**"
            )

            navigation = [
                "My requests",
                "Submit a request"
            ]

            if current_view in navigation:
                navigation_index = navigation.index(
                    current_view
                )
            else:
                navigation_index = 0

            selected_view = st.sidebar.radio(
                "Navigation",
                navigation,
                index=navigation_index
            )

            if selected_view != current_view:

                st.session_state["current_view"] = (
                    selected_view
                )

                if selected_view == "My requests":
                    st.session_state["ticket_page"] = 1

                st.rerun()

            st.sidebar.caption("Local demo")

            if st.sidebar.button("Sign out"):
                st.session_state.clear()
                st.rerun()


            # ==================================================
            # MY REQUESTS
            # ==================================================

            if current_view == "My requests":

                st.header("My requests")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Refresh"):
                        st.rerun()

                with col2:
                    if st.button("Submit a request"):
                        st.session_state["current_view"] = (
                            "Submit a request"
                        )
                        st.rerun()


                search = st.text_input(
                    "Search subject or message",
                    value=st.session_state["search"]
                )

                status = st.selectbox(
                    "Status",
                    [
                        "All",
                        "Open",
                        "In progress",
                        "Resolved"
                    ],
                    index=[
                        "All",
                        "Open",
                        "In progress",
                        "Resolved"
                    ].index(
                        st.session_state["status"]
                    )
                )


                col1, col2 = st.columns(2)

                with col1:

                    if st.button("Apply"):

                        st.session_state["search"] = (
                            search.strip()
                        )

                        st.session_state["status"] = (
                            status
                        )

                        st.session_state["ticket_page"] = 1

                        st.rerun()

                with col2:

                    if st.button("Clear"):

                        st.session_state["search"] = ""
                        st.session_state["status"] = "All"
                        st.session_state["ticket_page"] = 1

                        st.rerun()


                current_search = st.session_state[
                    "search"
                ]

                current_status = st.session_state[
                    "status"
                ]

                current_page = st.session_state[
                    "ticket_page"
                ]


                status_map = {
                    "All": "all",
                    "Open": "open",
                    "In progress": "in_progress",
                    "Resolved": "resolved"
                }

                status_value = status_map[
                    current_status
                ]


                response = requests.get(
                    f"{API_URL}/v1/tickets",
                    headers=get_auth_headers(),
                    params={
                        "search": current_search,
                        "status": status_value,
                        "page": current_page,
                        "page_size": 10
                    }
                )


                if response.status_code == 200:

                    data = response.json()

                    tickets = data["items"]
                    total = data["total"]

                    st.write(
                        f"Total requests: **{total}**"
                    )


                    if not tickets:

                        if total == 0 and not current_search:

                            st.info(
                                "You have no requests yet."
                            )

                            if st.button(
                                "Submit your first request"
                            ):

                                st.session_state[
                                    "current_view"
                                ] = "Submit a request"

                                st.rerun()

                        else:

                            st.info(
                                "No requests match your filters."
                            )

                            if st.button(
                                "Clear filters"
                            ):

                                st.session_state[
                                    "search"
                                ] = ""

                                st.session_state[
                                    "status"
                                ] = "All"

                                st.session_state[
                                    "ticket_page"
                                ] = 1

                                st.rerun()


                    else:

                        # ==========================================
                        # TABLE FIRST
                        # ==========================================

                        st.table(
                            [
                                {
                                    "Reference": ticket["id"],
                                    "Subject": ticket["subject"],
                                    "Status": ticket["status"],
                                    "Created UTC":
                                        ticket["created_at"],
                                    "Last public activity UTC":
                                        ticket["updated_at"]
                                }
                                for ticket in tickets
                            ]
                        )


                        # ==========================================
                        # SELECT REQUEST AFTER TABLE
                        # ==========================================

                        options = {
                            (
                                f"{ticket['id']} — "
                                f"{ticket['subject']}"
                            ): ticket
                            for ticket in tickets
                        }

                        selected_label = st.selectbox(
                            "Select request",
                            list(options.keys())
                        )

                        selected_ticket = options[
                            selected_label
                        ]


                        # ==========================================
                        # OPEN REQUEST
                        # ==========================================

                        if st.button("Open request"):

                            st.session_state[
                                "selected_ticket"
                            ] = str(
                                selected_ticket["id"]
                            )

                            st.session_state[
                                "current_view"
                            ] = "Request detail"

                            st.rerun()


                    total_pages = max(
                        1,
                        (total + 9) // 10
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Previous",
                            disabled=current_page <= 1
                        ):

                            st.session_state[
                                "ticket_page"
                            ] = current_page - 1

                            st.rerun()

                    with col2:

                        if st.button(
                            "Next",
                            disabled=current_page >= total_pages
                        ):

                            st.session_state[
                                "ticket_page"
                            ] = current_page + 1

                            st.rerun()


                    st.caption(
                        f"Page {current_page} "
                        f"of {total_pages}"
                    )


                elif response.status_code == 401:

                    st.session_state.clear()
                    st.rerun()


                else:

                    st.error(
                        "Unable to load your requests. "
                        "Please try again."
                    )


            # ==================================================
            # SUBMIT A REQUEST
            # ==================================================

            elif current_view == "Submit a request":

                st.header("Submit a support request")

                st.write(
                    f"Signed-in customer: "
                    f"**{user['name']}**"
                )

                subject = st.text_input(
                    "Subject",
                    max_chars=160
                )

                message = st.text_area(
                    "Describe the issue",
                    max_chars=5000
                )

                st.warning(
                    "Use fictional details only. "
                    "Do not enter passwords or payment data."
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button("Submit request"):

                        if len(subject.strip()) < 5:

                            st.error(
                                "Subject must be at least "
                                "5 characters."
                            )

                        elif len(message.strip()) < 10:

                            st.error(
                                "Description must be at least "
                                "10 characters."
                            )

                        else:

                            response = requests.post(
                                f"{API_URL}/v1/tickets",
                                headers=get_auth_headers(),
                                json={
                                    "subject": subject.strip(),
                                    "message": message.strip()
                                }
                            )

                            if response.status_code == 200:

                                ticket = response.json()

                                st.success(
                                    "Saved — request submitted "
                                    "successfully."
                                )

                                st.write(
                                    f"Reference: "
                                    f"`{ticket['id']}`"
                                )

                                st.write(
                                    f"Status: "
                                    f"**{ticket['status']}**"
                                )

                                st.session_state[
                                    "last_created_ticket"
                                ] = str(
                                    ticket["id"]
                                )

                            elif response.status_code == 401:

                                st.session_state.clear()
                                st.rerun()

                            else:

                                st.error(
                                    "Unable to submit your request."
                                )

                with col2:

                    if st.button("Cancel"):

                        st.session_state[
                            "current_view"
                        ] = "My requests"

                        st.rerun()


            # ==================================================
            # REQUEST DETAIL
            # ==================================================

            elif current_view == "Request detail":

                st.header("Request detail")

                selected_ticket = st.session_state.get(
                    "selected_ticket"
                )

                if not selected_ticket:
                    st.warning("No request selected.")

                if st.button("Back to My requests"):
                    st.session_state["current_view"] = "My requests"
                    st.rerun()

                else:
                    st.write(
                    f"Selected request: `{selected_ticket}`"
                    )

                    st.info(
                    "Request conversation will be implemented "
                    "in C03."
                    )

                    if st.button("Back to My requests"):

                        st.session_state["current_view"] = (
                        "My requests"
                        )

                        st.rerun()