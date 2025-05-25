--- SK ONLINE VOTING SYSTEM ---
    A web-based Student/Youth Council voting system designed for secure and efficient election management.
    Built with Flask (Python), MySQL, and HTML/CSS/JS.


--- SYSTEM FEATURES ---

👤 USER FUNCTIONALITY (Voters)
  • Login using Voter ID or Email
  • Register (account goes into pending status)
  • View upcoming and ongoing elections
  • View candidate information by position
  • Vote during the election period (one-time voting logic)
  • View election results (if allowed by admin)
  • Edit profile (Voter ID is not editable)
  • Wait for admin approval before gaining full access (if not verified)

🛠 ADMIN FUNCTIONALITY
  • Login with hardcoded admin account (auto-created on first run)
  • View upcoming and ongoing elections
  • Create, edit, delete election events
  • Manage candidates by position (Chairperson, Treasurer, Kagawad) by adding, editing, and deleting.
  • Automatically create new parties
  • Verify or delete user registrations
  • View full voting history logs
  • View and manage result visibility for each position
  • Edit admin profile


--- TECHNOLOGY STACK ---
  Backend:     Python (Flask)
  Frontend:    HTML5, CSS3, JS (vanilla)
  Database:    MySQL
  ORM:         Raw SQL (mysql.connector)
  Session:     Flask sessions
  Validation:  Flash + HTML + JS
  Structure:   Functional Flask app (no blueprints)


--- DATABASE ---
  Database Name: cccs105

Key Tables:
  • users              - Stores voter and admin accounts
  • elections          - Events with title, timeframe, status
  • candidates         - Linked to positions and parties
  • parties            - Party details
  • positions          - Chairperson, Treasurer, Kagawad
  • votes              - User-submitted votes
  • election_results   - Aggregated vote results
  • result_visibility  - Admin control for result display


--- SETUP & RUN ---

Python version required: 3.7+

1. Install dependencies:
     pip install flask mysql-connector-python python-dotenv

2. Create a `.env` file in the root directory with the following content:
     DB_HOST=localhost
     DB_USER=root
     DB_PASSWORD=
     DB_NAME=cccs105
     SECRET_KEY=your_secret_key_here

3. Run the app:
     python new_app.py

4. Access the system in your browser:
     http://127.0.0.1:5000


--- ADMIN ACCOUNT ---
Auto-created on first run:

  • Voter ID: ADMIN001
  • Email:    admin@gmail.com
  • Password: admin12345
  • Role:     admin
  • Status:   verified


--- LIMITATIONS (TO BE IMPROVED) ---
  • No image upload for candidates/profiles
  • Only one admin account supported
  • No password recovery function
  • No blueprints/modular structure

--- CREDITS ---
  NAS, JOHN CARLO E.
  johncarlonas@gmail.com
