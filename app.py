import streamlit as st
from datetime import date
import datetime
import sqlite3
from auth_utils import init_database, authenticate_user, add_user, load_users
from task_utils import init_task_database, create_task, update_task_status, get_user_tasks, get_user_task_stats, \
    get_task_messages, create_message
from config import DATABASE_PATH
import pandas as pd
import shutil
import os


def main_page():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    st.sidebar.markdown(f"<h1 style='color: black;'>Welcome, {st.session_state.username}</h1>", unsafe_allow_html=True)
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    # Modify menu based on roles
    if st.session_state.role == 'boss':
        menu = st.sidebar.selectbox(
            "Menu",
            ["Tasks", "Create Task", "Team Overview", "Self-Assign Task"]
        )
    elif st.session_state.role == 'database':
        menu = st.sidebar.selectbox(
            "Menu",
            ["Database Management"]
        )
    else:
        menu = st.sidebar.selectbox(
            "Menu",
            ["Tasks", "Create Task", "Self-Assign Task"]
        )

    if menu == "Tasks":
        st.markdown(
            """
            <h1 style="
                text-align: center; 
                font-family: 'Trebuchet MS', sans-serif; 
                background: linear-gradient(to right, #4B9CD3, #34D399); 
                -webkit-background-clip: text; 
                color: transparent; 
                font-size: 40px; 
                font-weight: bold; 
                text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            ">
                 Tasks Dashboard
            </h1>
            """,
            unsafe_allow_html=True
        )
        tasks = get_user_tasks(st.session_state.username, st.session_state.role)

        if not tasks:
            st.info("No tasks found.")
        else:
            for task_id, task in tasks.items():
                display_task_card(task_id, task)

    elif menu == "Database Management" and st.session_state.role == 'database':
        database_management_page()

    elif menu == "Create Task":
        st.markdown(
            """
            <h1 style="
                text-align: center; 
                font-family: 'Trebuchet MS', sans-serif; 
                background: linear-gradient(to right, #4B9CD3, #34D399); 
                -webkit-background-clip: text; 
                color: transparent; 
                font-size: 40px; 
                font-weight: bold; 
                text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            ">
                 Create New Tasks
            </h1>
            """,
            unsafe_allow_html=True
        )
        with st.form(key="create_task_form"):
            title = st.text_input("Task Title")
            description = st.text_area("Task Description")
            users = load_users()
            team_members = [user for user, data in users.items() if data['role'] == 'member']
            assigned_to = st.multiselect("Assign To", team_members)
            due_date = st.date_input("Due Date", min_value=date.today())

            submitted = st.form_submit_button("Create Task")
            if submitted:
                if title and description and assigned_to:
                    create_task(
                        title,
                        description,
                        st.session_state.username,
                        assigned_to,
                        due_date.isoformat()
                    )
                    st.success("Task created successfully")
                    st.rerun()
                else:
                    st.error("Please fill all required fields")

    elif menu == "Team Overview" and st.session_state.role == 'boss':
        st.markdown(
            """
            <h1 style="
                text-align: center; 
                font-family: 'Trebuchet MS', sans-serif; 
                background: linear-gradient(to right, #4B9CD3, #34D399); 
                -webkit-background-clip: text; 
                color: transparent; 
                font-size: 40px; 
                font-weight: bold; 
                text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            ">
                 Team Overview
            </h1>
            """,
            unsafe_allow_html=True
        )
        users = load_users()
        team_members = [user for user, data in users.items() if data['role'] == 'member']

        selected_member = st.selectbox("Select Team Member", team_members)
        if selected_member:
            view_member_profile(selected_member)

    elif menu == "Self-Assign Task":
        st.markdown(
            """
            <h1 style="
                text-align: center; 
                font-family: 'Trebuchet MS', sans-serif; 
                background: linear-gradient(to right, #4B9CD3, #34D399); 
                -webkit-background-clip: text; 
                color: transparent; 
                font-size: 40px; 
                font-weight: bold; 
                text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
            ">
                 Self-Assign Task
            </h1>
            """,
            unsafe_allow_html=True
        )
        with st.form(key="self_assign_task_form"):
            title = st.text_input("Task Title")
            description = st.text_area("Task Description")
            due_date = st.date_input("Due Date", min_value=date.today())

            submitted = st.form_submit_button("Self-Assign Task")
            if submitted:
                if title and description:
                    task_id = create_task(
                        title,
                        description,
                        st.session_state.username,  # Boss assigns task
                        [st.session_state.username],  # Self-assign
                        due_date.isoformat()
                    )

                    # Create a system message to log task creation
                    create_message(
                        task_id,
                        'System',
                        f"Task self-assigned by {st.session_state.username}",
                        message_type='system'
                    )

                    st.success("Task self-assigned successfully")
                    st.rerun()
                else:
                    st.error("Please fill all required fields")


st.set_page_config(
    page_title="Team Tasker",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling the title and making it mobile-friendly
st.markdown("""
    <style>
        /* Stylish title with gradient, shadow, and animation */
        h1 {
            font-size: 48px;  /* Larger title font for desktop */
            font-weight: 700;  /* Bold title */
            text-align: center;
            background: linear-gradient(45deg, #4CAF50, #FF5722);  /* Gradient color */
            -webkit-background-clip: text;
            color: transparent;
            text-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2);  /* Subtle text shadow */
            animation: titleAnimation 2s ease-in-out infinite;  /* Animation for smooth transitions */
            margin-top: 40px;
        }

        /* Mobile specific styling */
        @media (max-width: 768px) {
            h1 {
                font-size: 32px;  /* Smaller title font on mobile */
                text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.3);  /* Slightly softer shadow on mobile */
            }
        }

        /* Animation for title */
        @keyframes titleAnimation {
            0% { transform: translateY(0); opacity: 0.7; }
            50% { transform: translateY(-10px); opacity: 1; }
            100% { transform: translateY(0); opacity: 0.7; }
        }

        /* Optional: Style the sidebar to match the modern theme */
        .css-18e3th9 {
            background-color: #f5f5f5;  /* Light gray background for the sidebar */
            border-right: 2px solid #e0e0e0;  /* Light border to separate sidebar */
        }

        /* Content padding adjustments */
        .css-12oz5g7 {
            padding: 20px;  /* Adding padding around the content */
        }

    </style>
""", unsafe_allow_html=True)



def format_timestamp(timestamp):
    """Convert timestamp to a more readable format"""
    try:
        # Parse the ISO format timestamp manually
        dt = datetime.datetime.strptime(timestamp.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%b %d at %I:%M %p")  # Simplified date format
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return timestamp


def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None


def reset_form_fields():
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0
    st.session_state.form_key += 1



def view_member_profile(username):
    st.markdown("""
    <style>
    .profile-container {
        background-color: #ffffff;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        padding: 30px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .profile-header {
        display: flex;
        align-items: center;
        margin-bottom: 25px;
        border-bottom: 1px solid #e9ecef;
        padding-bottom: 20px;
    }
    .profile-avatar {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background-color: #e9ecef;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 25px;
        font-size: 40px;
        color: #6c757d;
        font-weight: 600;
        text-transform: uppercase;
    }
    .profile-info {
        flex-grow: 1;
    }
    .profile-name {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .profile-role {
        font-size: 1rem;
        color: #6c757d;
        background-color: #e9ecef;
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
    }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin-top: 25px;
    }
    .stat-card {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s ease;
    }
    .stat-card:hover {
        transform: translateY(-5px);
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
    }
    .tasks-section {
        margin-top: 30px;
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 25px;
    }
    .task-list-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        border-bottom: 1px solid #e9ecef;
        padding-bottom: 15px;
    }
    .task-list-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
    }
    .task-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px;
        background-color: #ffffff;
        border-radius: 10px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    .task-item:hover {
        background-color: #f1f3f5;
    }
    .task-title {
        font-weight: 500;
        color: #2c3e50;
    }
    .task-status {
        font-size: 0.8rem;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: 600;
    }
    .status-pending { background-color: #ffd54f; color: #1a1a1a; }
    .status-in_progress { background-color: #4fc3f7; color: white; }
    .status-completed { background-color: #81c784; color: white; }
    .status-followup_needed { background-color: #e57373; color: white; }
    </style>
    """, unsafe_allow_html=True)

    # Fetch user tasks and stats
    tasks = get_user_tasks(username, "member")
    stats = get_user_task_stats(username)

    st.markdown(f"""
    <div class="profile-container">
        <div class="profile-header">
            <div class="profile-avatar">{username[0]}</div>
            <div class="profile-info">
                <div class="profile-name">{username}</div>
                <div class="profile-role">Team Member</div>
            </div>
        </div>

    """, unsafe_allow_html=True)

    # Task List
    if tasks:
        for task_id, task in tasks.items():
            status_class = {
                'pending': 'status-pending',
                'in_progress': 'status-in_progress',
                'completed': 'status-completed',
                'followup_needed': 'status-followup_needed'
            }.get(task['status'], 'status-pending')

            st.markdown(f"""
            <div class="task-item">
                <div class="task-title">{task['title']}</div>
                <div class="task-status {status_class}">{task['status'].replace('_', ' ').title()}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="task-item">
            <div class="task-title">No tasks assigned</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

# Add these helper functions if they're not already defined
def get_status_class(status):
    status_classes = {
        'pending': 'task-status-pending',
        'in_progress': 'task-status-in_progress',
        'completed': 'task-status-completed',
        'followup_needed': 'task-status-followup_needed'
    }
    return status_classes.get(status, 'task-status-pending')


def get_status_badge_style(status):
    status_styles = {
        'pending': 'background-color: #F39C12; color: white;',
        'in_progress': 'background-color: #3498DB; color: white;',
        'completed': 'background-color: #2ECC71; color: white;',
        'followup_needed': 'background-color: #E74C3C; color: white;'
    }
    return status_styles.get(status, 'background-color: gray; color: white;')


def login_page():
    st.title("Team Task Manager")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            authenticated, role = authenticate_user(username, password)
            if authenticated:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        with st.form(key="signup_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Set Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            submitted = st.form_submit_button("Sign Up")
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif new_username and new_password:
                    if add_user(new_username, new_password):
                        st.success("Account created successfully. Please log in.")
                    else:
                        st.error("Username already exists")
                else:
                    st.error("Please fill all fields")


def display_task_card(task_id, task, context="main"):
    st.markdown("""
    <style>
    /* Global Styles */
    body {
        font-family: 'Roboto', sans-serif;
        color: #333;
        background-color: #f7f7f7;
    }

    .task-card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 0; /* Remove margin to merge with expander */
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .task-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 20px;
        cursor: pointer;
        border-radius: 12px 12px 0 0; /* Round top corners */
        transition: background-color 0.3s ease;
    }

    /* Modify the expander to look like a continuation of the task card */
    .stExpander {
        margin-top: 0 !important;
        border: none;
    }

    .stExpander > [data-testid="stExpander"] {
        border: none;
        box-shadow: none;
    }

    .stExpander > [data-testid="stExpander"] > div {
        padding: 0 !important;
    }

    .task-details-section {
        background-color: #f8f9fa;
        padding: 15px 20px;
        border-radius: 0 0 12px 12px; /* Round bottom corners */
        font-size: 0.95rem;
        color: #495057;
    }

    .task-details-section div {
        margin-bottom: 10px;
        line-height: 1.4;
    }

    .task-details-section div:last-child {
        margin-bottom: 0;
    }
    .task-status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px; /* Creates an oval shape */
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-left: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }

    /* Specific color styles for each status */
    .badge-pending {
        background-color: #FFC107; /* Amber */
        color: #212121;
    }

    .badge-in-progress {
        background-color: #2196F3; /* Blue */
        color: white;
    }

    .badge-completed {
        background-color: #4CAF50; /* Green */
        color: white;
    }

    .badge-followup-needed {
        background-color: #F44336; /* Red */
        color: white;
    }

    /* Hover effect for badges */
    .task-status-badge:hover {
        opacity: 0.9;
        transform: scale(1.05);
    }

    /* Ensures the badge doesn't break the layout */
    .task-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .view-previous-btn {
        width: 100%;
        text-align: center;
        padding: 10px;
        background-color: #f1f1f1;
        color: #333;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        margin-bottom: 10px;
        transition: background-color 0.3s ease;
    }
    .view-previous-btn:hover {
        background-color: #e1e1e1;
    }
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        display: flex;
        flex-direction: column-reverse;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 8px;
        scrollbar-width: thin;
        scrollbar-color: #888 #f1f1f1;
    }
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1; 
    }
    .chat-container::-webkit-scrollbar-thumb {
        background: #888; 
        border-radius: 4px;
    }


    /* Message Bubbles */
    .message-bubble {
        max-width: 30%; /* Narrower bubble */
        padding: 8px 12px;
        border-radius: 18px;
        word-wrap: break-word;
        font-size: 0.85rem;
        line-height: 1.3;
        position: relative;
        margin: 0 0 8px 0; /* Margin between messages */
    }

    /* Sender's Message (Right Aligned) */
    .message-sender {
        background-color: #dcf8c6;
        align-self: flex-end;
        margin-left: auto;
        border-radius: 18px 18px 0 18px; /* Rounded corners for the sender */
    }

    /* Receiver's Message (Left Aligned) */
    .message-receiver {
        background-color: #ffffff;
        border: 1px solid #ddd;
        align-self: flex-start;
        margin-right: auto;
        border-radius: 18px 18px 18px 0; /* Rounded corners for the receiver */
    }

    /* System Message (Center Aligned) */
    .system-message {
        max-width: 70%; /* Narrower bubble */

        background-color: #f0f0f0;
        align-self: center;
        border-radius: 8px;
        font-size: 0.75rem;
        color: #555;
        padding: 6px 12px;
    }

    /* Sender's Name */
    .message-sender-name {
        font-size: 0.75rem;
        color: #999;
        font-weight: 600;
        margin-bottom: 4px;
    }

    /* Timestamp */
    .message-timestamp {
        font-size: 0.65rem;
        color: #888;
        text-align: right;
        margin-top: 4px;
    }

    .message-timestamp {
        font-size: 0.7rem;
        color: #888;
        text-align: right;
        margin-top: 6px;
    }

    /* Message Input */
    .chat-input-container {
        margin-top: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .chat-input-container textarea {
        width: 85%;
        padding: 12px;
        border-radius: 20px;
        border: 1px solid #ddd;
        font-size: 0.9rem;
        color: #333;
        background-color: #f8f8f8;
        resize: none;
        box-sizing: border-box;
    }
    .submit-button {
        background-color: #3498DB;
        color: white;
        padding: 10px 18px;
        border-radius: 30px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }

    .submit-button:hover {
        background-color: #2980b9;
    }

    /* Status Change Section */
    .status-update-section {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .status-update-section select {
        padding: 8px 15px;
        border-radius: 8px;
        border: 1px solid #ddd;
        background-color: #fff;
        font-size: 0.9rem;
        color: #333;
        width: 100%;
        max-width: 250px;
    }

    .status-update-section button {
        background-color: #2ECC71;
        color: white;
        padding: 10px 15px;
        border-radius: 30px;
        border: none;
        cursor: pointer;
        font-weight: 600;
        margin-top: 15px;
        transition: background-color 0.3s ease;
    }

    .status-update-section button:hover {
        background-color: #27ae60;
    }


    </style>
    """, unsafe_allow_html=True)

    def get_status_badge_class(status):
        badge_classes = {
            'pending': 'badge-pending',
            'in_progress': 'badge-in-progress',
            'completed': 'badge-completed',
            'followup_needed': 'badge-followup-needed'
        }
        return badge_classes.get(status, 'badge-pending')

        # Task Card with Expandable Details

    with st.container():
        # Task Header
        st.markdown(f"""
         <div class="task-card" id="task-{task_id}">
             <div class="task-header">
                 <div class="task-title">{task['title']}</div>
                 <div class="task-status-badge {get_status_badge_class(task['status'])}">
                     {task['status'].replace('_', ' ').title()}
                 </div>
             </div>
         </div>
         """, unsafe_allow_html=True)

        # Expandable Details Section
        with st.expander("Task Details", expanded=False):
            # Task Details
            st.markdown(f"""
             <div class="task-details-section">
                 <div><strong>Assigned By:</strong> {task['assigned_by']}</div>
                 <div><strong>Assigned To:</strong> {', '.join(task['assigned_to'])}</div>
                 <div><strong>Description:</strong> {task['description']}</div>
                 <div><strong>Due Date:</strong> {task['due_date']}</div>
             </div>
             """, unsafe_allow_html=True)

            # Chat Section
            messages = get_task_messages(task_id)
            for msg in messages:
                message_class = "message-bubble"
                if msg['sender'] == 'System':
                    message_class += " system-message"
                elif msg['sender'] == st.session_state.username:
                    message_class += " message-sender"
                else:
                    message_class += " message-receiver"

                formatted_timestamp = format_timestamp(msg['timestamp'])

                message_html = f"""
                 <div class="{message_class}">
                     {'<div class="message-sender-name">' + msg["sender"] + '</div>' if msg['sender'] != 'System' else ''}
                     {msg['message']}
                     <div class="message-timestamp">{formatted_timestamp}</div>
                 </div>
                 """
                st.markdown(message_html, unsafe_allow_html=True)


            # Message Input Form
            st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
            with st.form(key=f'chat_form_{task_id}', clear_on_submit=True):
                col1, col2 = st.columns([8, 1])
                with col1:
                    message = st.text_area("Type your message", key=f'chat_input_{task_id}',
                                           label_visibility="collapsed", height=80)
                with col2:
                    submit_message = st.form_submit_button("➤", help="Send Message", use_container_width=True)

                if submit_message and message:
                    create_message(task_id, st.session_state.username, message)
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            # Status Change Section
            if st.session_state.role == 'boss' or st.session_state.username in task['assigned_to']:
                st.markdown('<div class="status-update-section">', unsafe_allow_html=True)
                st.subheader("Update Task Status")
                status_options = [
                    'pending',
                    'in_progress',
                    'completed',
                    'followup_needed'
                ]
                new_status = st.selectbox(
                    "Change Task Status",
                    status_options,
                    index=status_options.index(task['status']),
                    key=f'status_{task_id}'
                )

                if new_status != task['status']:
                    if st.button("Update Status", key=f'update_status_{task_id}'):
                        update_task_status(task_id, new_status)

                        # Create a system message to log status change
                        create_message(
                            task_id,
                            'System',
                            f"Task status changed from {task['status']} to {new_status}",
                            message_type='system'
                        )
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)


def database_backup_restore():
    """Backup and restore database functionality"""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Backup Database")
        if st.button("Create Backup"):
            try:
                backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_path = os.path.join("data", backup_filename)
                shutil.copy(DATABASE_PATH, backup_path)
                st.success(f"Database backed up to {backup_filename}")
            except Exception as e:
                st.error(f"Backup failed: {e}")

    with col2:
        st.subheader("Restore Database")
        backup_files = [f for f in os.listdir("data") if f.startswith("backup_") and f.endswith(".db")]

        if backup_files:
            selected_backup = st.selectbox("Select Backup", backup_files)

            if st.button("Restore Selected Backup"):
                try:
                    backup_path = os.path.join("data", selected_backup)
                    shutil.copy(backup_path, DATABASE_PATH)
                    st.success("Database restored successfully")
                except Exception as e:
                    st.error(f"Restore failed: {e}")
        else:
            st.info("No backup files found")


def view_database_tables(selected_table):
    """Enhanced function to view and interact with database tables"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Fetch table columns
            cursor.execute(f"PRAGMA table_info({selected_table})")
            columns = [column[1] for column in cursor.fetchall()]

            # Fetch all data
            cursor.execute(f"SELECT * FROM {selected_table}")
            rows = cursor.fetchall()

            if rows:
                # Convert rows to list of dictionaries
                data = [dict(row) for row in rows]
                df = pd.DataFrame(data)

                # Identify primary key column (first column)
                primary_key = columns[0] if columns else None

                # Display editable dataframe
                edited_df = st.data_editor(
                    df,
                    num_rows="dynamic",  # Allow adding/deleting rows
                    column_config={
                        primary_key: st.column_config.TextColumn(disabled=True) if primary_key else None
                    } if primary_key else {}
                )

                # Detect changes
                if st.button(f"Save Changes to {selected_table}"):
                    update_table_data(selected_table, columns, df, edited_df)

                st.write(f"Total Rows: {len(rows)}")
            else:
                st.info(f"No data in {selected_table} table")

        except sqlite3.Error as e:
            st.error(f"Error fetching data: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")


def update_table_data(table_name, columns, original_df, edited_df):
    """
    Wrapper function for database synchronization
    Maintains compatibility with existing code
    """
    success = sync_database_changes(table_name, columns, original_df, edited_df)
    if success and table_name == 'users':
        # Reload users data in the application
        updated_users = reload_users_data()
    return success

    if not columns:
        st.error("No columns found in the table")
        return

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        try:
            # Ensure DataFrames have consistent column names and index
            original_df = original_df.reset_index(drop=True)
            edited_df = edited_df.reset_index(drop=True)

            # Rename columns to match the database schema
            original_df.columns = columns
            edited_df.columns = columns

            # Assume first column is primary key
            primary_key = columns[0]

            # Detect changes
            # Added rows
            added_rows = edited_df[~edited_df.duplicated(subset=[primary_key], keep=False)]

            # Deleted rows
            deleted_rows = original_df[~original_df[primary_key].isin(edited_df[primary_key])]

            # Modified rows (excluding primary key)
            modified_rows = edited_df[
                edited_df[primary_key].isin(original_df[primary_key]) &
                ~edited_df.equals(original_df)
                ]

            # Delete rows
            if not deleted_rows.empty:
                for _, row in deleted_rows.iterrows():
                    delete_query = f"DELETE FROM {table_name} WHERE {primary_key} = ?"
                    cursor.execute(delete_query, (row[primary_key],))
                st.success(f"Deleted {len(deleted_rows)} rows")

            # Update existing rows
            if not modified_rows.empty:
                update_columns = [col for col in columns if col != primary_key]
                for _, row in modified_rows.iterrows():
                    update_query = f"""
                    UPDATE {table_name} 
                    SET {', '.join([f"{col} = ?" for col in update_columns])} 
                    WHERE {primary_key} = ?
                    """
                    update_values = [row[col] for col in update_columns] + [row[primary_key]]
                    cursor.execute(update_query, update_values)
                st.success(f"Updated {len(modified_rows)} rows")

            # Insert new rows
            if not added_rows.empty:
                for _, row in added_rows.iterrows():
                    # Remove NaN values and handle potential issues
                    row = row.dropna()

                    # Ensure we have values for all columns
                    insert_columns = [col for col in columns if col in row.index]
                    insert_query = f"""
                    INSERT INTO {table_name} ({', '.join(insert_columns)}) 
                    VALUES ({', '.join(['?' for _ in insert_columns])})
                    """
                    cursor.execute(insert_query, [row[col] for col in insert_columns])
                st.success(f"Added {len(added_rows)} new rows")

            # Commit changes
            conn.commit()
            st.success("Database updated successfully")

        except sqlite3.Error as e:
            conn.rollback()
            st.error(f"Database error: {e}")
        except Exception as e:
            conn.rollback()
            st.error(f"Unexpected error: {e}")


def database_management_page():
    """Enhanced Database Management Page"""
    st.title("Database Management")

    # Tabs for different database operations
    tab1, tab2, tab3, tab4 = st.tabs([
        "Manage Tables",
        "Execute SQL Query",
        "Backup & Restore",
        "Database Info"
    ])

    with tab1:
        # Get list of tables
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]

        # Table selection and management
        selected_table = st.selectbox("Select Table to Manage", tables)
        view_database_tables(selected_table)

    with tab2:
        # Advanced SQL Query Execution
        query_type = st.selectbox("Query Type", ["SELECT", "INSERT", "UPDATE", "DELETE"])
        query = st.text_area("Enter SQL Query", height=150)

        if st.button("Execute Query"):
            execute_advanced_sql_query(query, query_type)

    with tab3:
        database_backup_restore()

    with tab4:
        display_database_info()


def execute_advanced_sql_query(query, query_type):
    """Enhanced SQL query execution with better error handling and results display"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            # Validate query type
            if not query.upper().startswith(query_type):
                st.error(f"Query must start with {query_type}")
                return

            # Execute query
            cursor.execute(query)

            if query_type == "SELECT":
                rows = cursor.fetchall()
                if rows:
                    # Get column names
                    column_names = [description[0] for description in cursor.description]

                    # Convert to DataFrame
                    df = pd.DataFrame(rows, columns=column_names)
                    st.dataframe(df)
                    st.write(f"Total Rows: {len(rows)}")
                else:
                    st.info("No results found")
            else:
                # For INSERT, UPDATE, DELETE
                conn.commit()
                st.success(f"{query_type} query executed successfully. Rows affected: {cursor.rowcount}")

    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")


def display_database_info():
    """Display detailed information about the database"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        st.subheader("Database Tables")
        for table in tables:
            table_name = table[0]

            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            with st.expander(f"{table_name} - {row_count} rows"):
                st.markdown("**Columns:**")
                column_data = []
                for col in columns:
                    column_data.append({
                        "Name": col[1],
                        "Type": col[2],
                        "Primary Key": "Yes" if col[5] else "No",
                        "Nullable": "Yes" if col[3] == 0 else "No"
                    })
                st.table(column_data)


def sync_database_changes(table_name, columns, original_df, edited_df):
    """
    Comprehensive database synchronization method

    Args:
    - table_name (str): Name of the database table
    - columns (list): List of column names
    - original_df (pd.DataFrame): Original data
    - edited_df (pd.DataFrame): Edited data

    Returns:
    - bool: Indicating if changes were successful
    """
    if not columns:
        st.error("No columns found in the table")
        return False

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        try:
            # Ensure DataFrames have consistent column names and index
            original_df = original_df.reset_index(drop=True)
            edited_df = edited_df.reset_index(drop=True)

            # Rename columns to match the database schema
            original_df.columns = columns
            edited_df.columns = columns

            # Assume first column is primary key
            primary_key = columns[0]

            # Comprehensive change detection
            def detect_changes(orig_df, edit_df):
                # Convert DataFrames to dict for easier comparison
                orig_records = orig_df.to_dict('records')
                edit_records = edit_df.to_dict('records')

                # Separate changes
                to_delete = [
                    record for record in orig_records
                    if record[primary_key] not in edit_df[primary_key].values
                ]

                to_update = [
                    record for record in edit_records
                    if record[primary_key] in orig_df[primary_key].values and
                       any(orig_record[primary_key] == record[primary_key] and
                           orig_record != record
                           for orig_record in orig_records)
                ]

                to_insert = [
                    record for record in edit_records
                    if record[primary_key] not in orig_df[primary_key].values
                ]

                return to_delete, to_update, to_insert

            # Detect changes
            to_delete, to_update, to_insert = detect_changes(original_df, edited_df)

            # Delete rows
            if to_delete:
                for record in to_delete:
                    delete_query = f"DELETE FROM {table_name} WHERE {primary_key} = ?"
                    cursor.execute(delete_query, (record[primary_key],))
                st.success(f"Deleted {len(to_delete)} rows")

            # Update existing rows
            if to_update:
                update_columns = [col for col in columns if col != primary_key]
                for record in to_update:
                    update_query = f"""
                    UPDATE {table_name} 
                    SET {', '.join([f"{col} = ?" for col in update_columns])} 
                    WHERE {primary_key} = ?
                    """
                    update_values = [record[col] for col in update_columns] + [record[primary_key]]
                    cursor.execute(update_query, update_values)
                st.success(f"Updated {len(to_update)} rows")

            # Insert new rows
            if to_insert:
                for record in to_insert:
                    # Remove None/NaN values
                    clean_record = {k: v for k, v in record.items() if pd.notna(v)}

                    # Ensure we have values for all columns
                    insert_columns = list(clean_record.keys())
                    insert_query = f"""
                    INSERT INTO {table_name} ({', '.join(insert_columns)}) 
                    VALUES ({', '.join(['?' for _ in insert_columns])})
                    """
                    cursor.execute(insert_query, list(clean_record.values()))
                st.success(f"Added {len(to_insert)} new rows")

            # Commit changes
            conn.commit()
            st.success("Database updated successfully")
            return True

        except sqlite3.Error as e:
            conn.rollback()
            st.error(f"Database error: {e}")
            return False
        except Exception as e:
            conn.rollback()
            st.error(f"Unexpected error: {e}")
            return False


def reload_users_data():
    """
    Reload users data from the database
    This function helps ensure data consistency across the application
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, password FROM users")
            users_data = cursor.fetchall()

            # Rebuild users dictionary
            users = {}
            for username, role, password in users_data:
                users[username] = {
                    'role': role,
                    'password': password
                }

            return users
    except Exception as e:
        st.error(f"Error reloading users: {e}")
        return {}


def main():
    # Initialize databases if not exists
    init_database()
    init_task_database()

    init_session_state()

    if not st.session_state.authenticated:
        login_page()
    else:
        main_page()


if __name__ == "__main__":
    main()
