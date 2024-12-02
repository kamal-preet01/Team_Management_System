import streamlit as st
from datetime import date
import datetime
from auth_utils import init_database, authenticate_user, add_user, load_users
from task_utils import init_task_database, create_task, update_task_status, get_user_tasks, get_user_task_stats,get_task_messages,create_message


def main_page():
    st.sidebar.title(f"Welcome, {st.session_state.username}")

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    if st.session_state.role == 'boss':
        menu = st.sidebar.selectbox(
            "Menu",
            ["Tasks", "Create Task", "Team Overview", "Self-Assign Task"]
        )
    else:
        menu = st.sidebar.selectbox(
            "Menu",
            ["Tasks", "Create Task", "Self-Assign Task"]
        )

    if menu == "Tasks":
        st.title("Tasks Dashboard")
        tasks = get_user_tasks(st.session_state.username, st.session_state.role)

        for task_id, task in tasks.items():
            with st.expander(f"{task['title']} - {task['status'].upper()} (Messages: {task['message_count']})"):
                display_task_card(task_id, task)

    elif menu == "Create Task":
        st.title("Create New Task")
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
        st.title("Team Overview")
        users = load_users()
        team_members = [user for user, data in users.items() if data['role'] == 'member']

        selected_member = st.selectbox("Select Team Member", team_members)
        if selected_member:
            view_member_profile(selected_member)

    elif menu == "Self-Assign Task":
        st.title("Self-Assign Task")
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
                        "Shammi Kapoor",  # Boss assigns task
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
    page_title="Team Task Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.write("""
<style>
    :root {
        --primary-color: #0077B6;
        --secondary-color: #00A8E8;
        --background-color: #F5F7FA;
        --text-color: #2C3E50;
        --border-radius: 12px;
    }

    body {
        font-family: 'Roboto', 'Segoe UI', sans-serif;
        color: var(--text-color);
        background-color: var(--background-color);
        margin: 0;
        padding: 0;
    }

    .container {
        @apply max-w-6xl mx-auto px-8 py-12;
    }

    /* Sidebar Styles */
    .sidebar {
        @apply bg-white border-r border-gray-300 p-8;
    }

    .sidebar h1 {
        @apply text-primary-color mb-8;
    }

    .sidebar-menu {
        @apply list-none p-0 m-0;
    }

    .sidebar-menu li {
        @apply mb-4;
    }

    .sidebar-menu li a {
        @apply text-text-color transition-colors duration-300 hover:text-primary-color;
    }

    /* Main Content Styles */
    .main-content {
        @apply bg-white rounded-lg shadow-md p-8 mb-8;
    }

    .main-content h2 {
        @apply text-primary-color mb-6;
    }

    /* Task Card Styles */
    .task-card {
        @apply bg-gray-100 rounded-lg shadow-md p-6 mb-6 border border-gray-300;
    }

    .task-card:hover {
        @apply shadow-lg;
    }

    .task-card h3 {
        @apply text-primary-color mb-2;
    }

    .task-info {
        @apply flex justify-between items-center mb-4;
    }

    .task-status {
        @apply font-semibold py-2 px-4 rounded-full;
    }

    .status-pending {
        @apply bg-yellow-200 text-yellow-800;
    }

    .status-in-progress {
        @apply bg-blue-200 text-blue-800;
    }

    .status-completed {
        @apply bg-green-200 text-green-800;
    }

    .status-followup {
        @apply bg-red-200 text-red-800;
    }

    /* Chat Styles */
    .chat-container {
        @apply bg-gray-100 rounded-lg shadow-md p-6 max-h-96 overflow-y-auto;
    }

    .message-bubble {
        @apply flex flex-col mb-4;
    }

    .message-sender {
        @apply font-semibold text-primary-color mb-2;
    }

    .message-content {
        @apply bg-gray-200 rounded-lg p-4 max-w-4/5 break-words;
    }

    .message-timestamp {
        @apply text-gray-600 text-sm mt-2 self-end;
    }

    .user-message {
        @apply self-start;
    }

    .system-message {
        @apply bg-gray-300 !important font-italic text-gray-700;
    }

    /* Form Styles */
    .form-control {
        @apply w-full py-3 px-4 border border-gray-400 rounded-lg text-base transition-colors duration-300 focus:border-secondary-color focus:outline-none;
    }

    .form-submit-button {
        @apply bg-primary-color text-white border-none rounded-lg py-3 px-6 text-base cursor-pointer transition-colors duration-300 hover:bg-secondary-color;
    }

    /* Responsive Styles */
    @media (max-width: 768px) {
        .container {
            @apply px-4 py-8;
        }

        .sidebar {
            @apply p-6;
        }

        .main-content {
            @apply p-6;
        }

        .task-card {
            @apply p-5;
        }

        .chat-container {
            @apply p-5 max-h-72;
        }

        .form-control {
            @apply text-sm;
        }

        .form-submit-button {
            @apply text-sm;
        }
    }
</style>
""", unsafe_allow_html=True)


def format_timestamp(timestamp):
    """Convert timestamp to a more readable format"""
    try:
        # Parse the ISO format timestamp manually
        dt = datetime.strptime(timestamp.split('.')[0], "%Y-%m-%dT%H:%M:%S")
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
    st.markdown(f"""
        <div class="member-profile">
            <h2>{username}'s Profile</h2>
        </div>
    """, unsafe_allow_html=True)

    tasks = get_user_tasks(username, "member")
    stats = get_user_task_stats(username)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
            <div class="stats-card">
                <h4>Total Tasks</h4>
                <h2>{}</h2>
            </div>
        """.format(stats['total']), unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class="stats-card">
                <h4>Completed</h4>
                <h2>{}</h2>
            </div>
        """.format(stats['completed']), unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div class="stats-card">
                <h4>In Progress</h4>
                <h2>{}</h2>
            </div>
        """.format(stats['in_progress']), unsafe_allow_html=True)
    with col4:
        st.markdown("""
            <div class="stats-card">
                <h4>Pending</h4>
                <h2>{}</h2>
            </div>
        """.format(stats['pending']), unsafe_allow_html=True)

    st.subheader("Assigned Tasks")
    for task_id, task in tasks.items():
        with st.expander(f"{task['title']} - {task['status'].upper()}"):
            display_task_card(task_id, task, context=f"profile_{username}")

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
    with st.container():
        st.markdown(f"## {task['title']}")
        st.markdown(f"**Status:** {task['status'].replace('_', ' ').title()}")
        st.markdown(f"**Description:** {task['description']}")
        st.markdown(f"**Assigned By:** {task['assigned_by']}")
        st.markdown(f"**Assigned To:** {', '.join(task['assigned_to'])}")
        st.markdown(f"**Due Date:** {task['due_date']}")

        # Chat Section
        st.subheader("Task Chat")

        messages = get_task_messages(task_id)
        for msg in messages:
            message_class = "message-card"
            if msg['message_type'] == 'system':
                message_class += " system-message"

            # Use the new format_timestamp function
            formatted_timestamp = format_timestamp(msg['timestamp'])

            st.markdown(f"""
            <div class="{message_class}">
                <strong>{msg['sender']}</strong> at {formatted_timestamp}
                <p>{msg['message']}</p>
            </div>
            """, unsafe_allow_html=True)

        # Message input form
        with st.form(key=f'chat_form_{task_id}', clear_on_submit=True):
            message = st.text_area("Type your message", key=f'chat_input_{task_id}')
            submit_message = st.form_submit_button("Send")

            if submit_message and message:
                create_message(
                    task_id,
                    st.session_state.username,
                    message
                )
                st.rerun()

        # Status Change Section (for boss or task assignees)
        if st.session_state.role == 'boss' or st.session_state.username in task['assigned_to']:
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