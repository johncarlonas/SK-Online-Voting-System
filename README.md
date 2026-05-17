# SK Online Voting System

A web-based Student/Youth Council voting system designed for secure and efficient election management. Built with Flask (Python), MySQL, and HTML/CSS/JS.

---

## System Features

### User Functionality (Voters)
* **Secure Authentication:** Log in using a unique Voter ID or registered Email.
* **Registration Workflow:** New user registrations default to a pending status awaiting verification.
* **Election Tracking:** View schedules for upcoming and ongoing election events.
* **Candidate Information:** Browse candidate profiles organized strictly by position.
* **One-Time Voting Logic:** Enforces strict compliance to ensure voters can only submit one ballot per election.
* **Dynamic Results:** View election results instantly (subject to admin visibility settings).
* **Profile Management:** Edit personal profile details (Voter ID remains locked and non-editable).

### Admin Functionality
* **Administrative Access:** Log in using a master admin account, automatically generated on the first system run.
* **Election Management:** Monitor ongoing events and fully create, edit, or delete election cycles.
* **Candidate & Party Control:** Manage candidates by designated positions (Chairperson, Treasurer, Kagawad) and automatically generate political parties.
* **User Verification:** Review, approve, or reject pending user registration requests.
* **Audit Logs:** View the complete, immutable voting history logs for transparency.
* **Result Visibility Toggle:** Manage and fine-tune whether results are visible or hidden for specific positions.

---

## Technology Stack

| Component | Technology Used |
| :--- | :--- |
| **Backend** | Python (Flask) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Database** | MySQL |
| **Database Access** | Raw SQL via `mysql.connector` |
| **Session Management** | Flask Sessions |
| **Validation** | Flask Flash messaging, HTML5 constraints, and client-side JavaScript |
| **Architecture** | Monolithic / Functional Flask application (no blueprint routing) |

---

## Database Structure

**Database Name:** `cccs105`

### Key Tables
* `users`: Stores core voter credentials, personal data, and admin accounts.
* `elections`: Tracks distinct election events, historical timeframes, and active statuses.
* `candidates`: Maps candidate profiles directly to their contested positions and parties.
* `parties`: Contains political party identification details.
* `positions`: Defines available roles (e.g., Chairperson, Treasurer, Kagawad).
* `votes`: Records individual user-submitted ballots.
* `election_results`: Holds aggregated voting metrics for analytical compilation.
* `result_visibility`: Controls admin-defined toggles for public result data display.

---

## Setup and Installation

### Prerequisites
* Python 3.7+

### Step-by-Step Guide

1. **Install dependencies:**
   ```bash
   pip install flask mysql-connector-python python-dotenv
