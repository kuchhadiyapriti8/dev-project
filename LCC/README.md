# Campground Issue Tracker: A Flask Python Web App for Community Issue Management

## Overview

Campground Issue Tracker is a Flask-based web application designed to track and manage issues at a local community campground. The app implements a secure login system with different levels of access for three user roles: visitors, helpers, and administrators. Each role has access to specific features, ensuring a tailored and efficient experience for users.

## Features

- **User Roles**: Visitors, Helpers, Administrators
- **Secure Login and Registration**: Password hashing with salting
- **Session Handling**: Access control based on user roles
- **Issue Management**: Report issues, view issues, update and resolve issues
- **Profile Management**: Edit personal profile details
- **Admin Features**: Manage users, assign roles, and handle system settings

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
   git clone https://github.com/yourusername/campground-issue-tracker.git
   cd campground-issue-tracker
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python app.py
   ```

4. **Access the Application**:
   Open your web browser and navigate to http://localhost:5000.

## Usage

- **Visitors**: Can report new issues and view existing ones
- **Helpers**: Can view and update issue statuses, add comments
- **Administrators**: Full access to manage issues, users, and system settings

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request via GitHub.

