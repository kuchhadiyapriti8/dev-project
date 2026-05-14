# Tree Talk: A Flask Python Web App for Tree Discussion

## Overview

Tree Talk is a Flask-based message board designed for discussing tree-related issues. The app features a secure login system with different levels of access for three user roles: members, moderators, and administrators. Each role has access to specific features, ensuring a tailored experience for users.

## Features

- **User Roles**: Members, Moderators, Administrators
- **Secure Login and Registration**: Password hashing with salting
- **Session Handling**: Access control based on user roles
- **Profile Management**: Profile photo upload and editing
- **Message Board**: Post messages, reply to messages, edit and delete messages and replies
- **Admin Features**: Manage users, change roles and statuses

## Installation

### Prerequisites

- Python 3.x
- Flask
- MySQL
- Flask-MySQLdb
- Flask-Hashing
- Werkzeug

### Setting Up

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/treetalk.git
   cd treetalk

2. **Install Dependencies**:
   ```bash 
   pip install -r requirements.txt

3. **Run the Application**:
  ```bash
  python app.py

4.  **Access the Application**:
  ```bash 
  Open your web browser and navigate to http://localhost:5000.

