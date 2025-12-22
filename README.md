# WebSocket Messenger - Python Edition

A modern real-time messaging application built with Flask, Flask-SocketIO, and SQLAlchemy.

## Features

- 🔐 User authentication (registration/login)
- 💬 Real-time private messaging
- 👥 Group chat functionality
- 📜 Message history
- 🚪 Soft-leave groups (can't see messages after leaving)
- 🎨 Modern dark-themed UI with gradients and animations
- ⚡ WebSocket communication using Socket.IO

## Technology Stack

- **Backend**: Flask 3.0
- **Real-time**: Flask-SocketIO (Socket.IO)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript (Socket.IO client)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Navigate to the project directory**
   ```bash
   cd python_messenger
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create environment file**
   ```bash
   copy .env.example .env
   ```
   
   Edit `.env` and set your secret key:
   ```
   SECRET_KEY=your-random-secret-key-here
   DATABASE_URL=sqlite:///messenger.db
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and navigate to: `http://localhost:5000`

## Project Structure

```
python_messenger/
├── app.py                 # Main application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── models/               # Database models
│   ├── __init__.py
│   ├── user.py           # User model
│   ├── message.py        # Message model
│   ├── group.py          # Group model
│   └── group_member.py   # GroupMember model
├── routes/               # API routes
│   ├── __init__.py
│   ├── auth.py           # Authentication routes
│   ├── chat.py           # Chat API routes
│   └── home.py           # Home routes
├── events/               # WebSocket events
│   ├── __init__.py
│   └── chat_events.py    # Socket.IO event handlers
├── templates/            # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   └── index.html
└── static/               # Static files
    ├── css/
    │   └── style.css
    └── js/
        └── chat.js
```

## Usage

### Register a New Account

1. Navigate to the registration page
2. Enter username, email, and password
3. Click "Register"

### Login

1. Navigate to the login page
2. Enter your email and password
3. Click "Login"

### Private Messaging

1. Click on a user from the "Users" tab
2. Type your message in the input field
3. Press Enter or click "Send"

### Group Chat

1. Click the "+ Create Group" button
2. Enter a group name
3. Select members to add
4. Click "Create"
5. Click on the group to start chatting

### Leave a Group

1. Click on a group
2. Click the "Leave" button
3. You will no longer receive new messages from that group

## API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /login` - Login user
- `POST /logout` - Logout user

### Chat API
- `GET /api/chat/users` - Get all users
- `GET /api/chat/groups` - Get user's groups
- `GET /api/chat/history/private/<email>` - Get private message history
- `GET /api/chat/history/group/<group_id>` - Get group message history

## WebSocket Events

### Client → Server
- `send_private_message` - Send a private message
- `send_group_message` - Send a group message
- `create_group` - Create a new group
- `leave_group` - Leave a group
- `delete_group_data` - Delete group membership
- `join_channel` - Join a group channel

### Server → Client
- `receive_private_message` - Receive a private message
- `receive_group_message` - Receive a group message
- `group_created` - Notification of new group
- `group_left` - Confirmation of leaving group
- `error` - Error notification

## Database Schema

### Users
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- created_at

### Messages
- id (Primary Key)
- sender_id (Foreign Key → Users)
- receiver_id (Foreign Key → Users, nullable)
- group_id (Foreign Key → Groups, nullable)
- content
- timestamp

### Groups
- id (Primary Key)
- name

### GroupMembers
- group_id (Primary Key, Foreign Key → Groups)
- user_id (Primary Key, Foreign Key → Users)
- has_left (Boolean)
- left_at (DateTime, nullable)

## Development

### Running in Development Mode

The application runs in debug mode by default when using the `.env` file with `FLASK_DEBUG=True`.

### Database Migrations

To create database migrations:

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Security Notes

- Change the `SECRET_KEY` in production
- Use HTTPS in production
- Consider using PostgreSQL or MySQL for production
- Implement rate limiting for API endpoints
- Add input validation and sanitization

## License

This project is provided as-is for educational purposes.

## Support

For issues or questions, please refer to the Flask and Flask-SocketIO documentation:
- Flask: https://flask.palletsprojects.com/
- Flask-SocketIO: https://flask-socketio.readthedocs.io/
