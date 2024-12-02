import sqlite3
from datetime import datetime
from config import DATABASE_PATH

def init_task_database():
    """Initialize tasks and messages tables"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Create tasks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            assigned_by TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        ''')

        # Create task_assignments table (for many-to-many relationship)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_assignments (
            task_id INTEGER,
            assigned_to TEXT,
            PRIMARY KEY (task_id, assigned_to),
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
        ''')

        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            message_type TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
        ''')

        conn.commit()


def create_task(title, description, assigned_by, assigned_to, due_date):
    """Create a new task"""
    # Remove duplicates and keep the order
    assigned_to = list(dict.fromkeys(assigned_to))

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Insert task
        cursor.execute('''
        INSERT INTO tasks 
        (title, description, assigned_by, due_date, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, assigned_by, due_date, 'pending', datetime.now().isoformat()))

        task_id = cursor.lastrowid

        # Insert task assignments
        for assignee in assigned_to:
            cursor.execute('''
            INSERT OR IGNORE INTO task_assignments (task_id, assigned_to)
            VALUES (?, ?)
            ''', (task_id, assignee))

        conn.commit()
    return task_id


def update_task_status(task_id, status):
    """Update task status"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE tasks SET status = ? WHERE task_id = ?
        ''', (status, task_id))
        conn.commit()
    return True




def get_user_tasks(username, role):
    """Retrieve tasks for a user with message count, sorted by most recent first"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if role == 'boss':
            # Boss sees all tasks, sorted by creation date in descending order
            cursor.execute('''
            SELECT t.*, 
                   GROUP_CONCAT(DISTINCT ta.assigned_to) as assigned_users,
                   COUNT(m.message_id) as message_count
            FROM tasks t
            LEFT JOIN task_assignments ta ON t.task_id = ta.task_id
            LEFT JOIN messages m ON t.task_id = m.task_id
            GROUP BY t.task_id
            ORDER BY t.created_at DESC
            ''')
        else:
            # Member sees tasks they are assigned to or assigned by, sorted by creation date
            cursor.execute('''
            SELECT t.*, 
                   GROUP_CONCAT(DISTINCT ta.assigned_to) as assigned_users,
                   COUNT(m.message_id) as message_count
            FROM tasks t
            JOIN task_assignments ta ON t.task_id = ta.task_id
            LEFT JOIN messages m ON t.task_id = m.task_id
            WHERE ta.assigned_to = ? OR t.assigned_by = ?
            GROUP BY t.task_id
            ORDER BY t.created_at DESC
            ''', (username, username))

        tasks = {}
        for row in cursor.fetchall():
            tasks[str(row['task_id'])] = {
                'title': row['title'],
                'description': row['description'],
                'assigned_by': row['assigned_by'],
                'assigned_to': list(set(row['assigned_users'].split(','))),
                'due_date': row['due_date'],
                'status': row['status'],
                'message_count': row['message_count']
            }
        return tasks



def get_user_task_stats(username):
    """Get task statistics for a user"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'followup_needed' THEN 1 ELSE 0 END) as followup_needed
        FROM tasks t
        JOIN task_assignments ta ON t.task_id = ta.task_id
        WHERE ta.assigned_to = ?
        ''', (username,))

        stats = cursor.fetchone()
        return {
            'total': stats[0],
            'completed': stats[1],
            'in_progress': stats[2],
            'pending': stats[3],
            'followup_needed': stats[4]
        }


def create_message(task_id, sender, message, message_type='user'):
    """Create a new message for a specific task"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        # If it's a system message, prepend the sender to the message
        if message_type == 'system':
            message = f"{sender} updated: {message}"

        cursor.execute('''
        INSERT INTO messages 
        (task_id, sender, message, timestamp, message_type)
        VALUES (?, ?, ?, ?, ?)
        ''', (task_id, sender, message, datetime.now().isoformat(), message_type))
        conn.commit()
    return True

def get_task_messages(task_id):
    """Retrieve all messages for a specific task"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM messages 
        WHERE task_id = ? 
        ORDER BY timestamp
        ''', (task_id,))
        messages = [dict(row) for row in cursor.fetchall()]
    return messages