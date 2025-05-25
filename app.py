import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from flask import make_response
from functools import wraps
import os
from mysql.connector import Error
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') 

# Database connection function
def create_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MariaDB: {e}")
        return None

# Use the connection
db = create_connection()
cursor = db.cursor(dictionary=True)

#function to initialize admin acc
def initialize_admin():
    cursor.execute("SELECT * FROM users WHERE voter_id = 'ADMIN001'")
    admin = cursor.fetchone()
    if not admin:
        cursor.execute("""
            INSERT INTO users (first_name, last_name, age, voter_id, email, password_hash, role, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, ('Admin', '', 21, 'ADMIN001', 'admin@gmail.com', 'admin12345', 'admin', 'verified'))
        db.commit()

initialize_admin()

def hash_password(password):
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def check_password(hashed_password, user_password):
    # Check if the provided password matches the hashed password
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))

def ensure_abstain_candidates():
    cursor.execute("SELECT position_id, name FROM positions")
    positions = cursor.fetchall()

    for pos in positions:
        position_id = pos['position_id']
        cursor.execute("""
            SELECT 1 FROM candidates 
            WHERE first_name = 'Abstain' AND position_id = %s
        """, (position_id,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO candidates (first_name, last_name, position_id)
                VALUES ('Abstain', '', %s)
            """, (position_id,))
            db.commit()
            
@app.route('/')
def redirect_to_login():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_error = ""

    if request.method == 'POST':
        identifier = request.form.get('email_or_voterid', '').strip()
        password = request.form.get('password', '').strip()

        if not identifier or not password:
            login_error = "Please enter both Email/Voter ID and Password."
            return render_template('login.html', login_error=login_error)

        cursor.execute("""
            SELECT * FROM users 
            WHERE voter_id = %s OR email = %s
        """, (identifier, identifier))
        user = cursor.fetchone()
        
        if user:
            if check_password(user['password_hash'], password) is False:
                login_error = "Invalid password or email."
                return render_template('login.html', login_error=login_error)

            if user['status'] != 'verified':
                return render_template('user/user_pending.html', user=user)

            # Set session and redirect
            session['user_id'] = user['user_id']
            session['voter_id'] = user['voter_id']
            session['role'] = user['role']

            return redirect(url_for('admin_home' if user['role'] == 'admin' else 'user_home'))
        else:
            login_error = "Account doesn't exist."
            return render_template('login.html', login_error=login_error)

    return render_template('login.html', login_error=login_error)

@app.route('/register', methods=['POST'])
def register():
    first_name = request.form.get('first_name').strip()
    last_name = request.form.get('last_name').strip()
    voter_id = request.form.get('voter_id').strip()
    age = request.form.get('age')
    email = request.form.get('email').strip()
    password = hash_password(request.form.get('password').strip())

    # Check if voter ID or email already exists
    cursor.execute("SELECT * FROM users WHERE voter_id = %s OR email = %s", (voter_id, email))
    existing_user = cursor.fetchone()

    if existing_user:
        return render_template('login.html', show_form='register', register_error='An account with this Voter ID or Email already exists.')

    # Insert new user
    cursor.execute("""
        INSERT INTO users (first_name, last_name, age, voter_id, email, password_hash, role, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (first_name, last_name, age, voter_id, email, password, 'voter', 'pending'))
    db.commit()

    session['user_id'] = voter_id
    session['role'] = 'voter'

    return render_template('user/user_pending.html', user={'voter_id': voter_id})

# --- ADMIN END ----
@app.route('/admin/home')
def admin_home():
    now = datetime.now()

    cursor.execute("SELECT * FROM elections ORDER BY start_time ASC")
    all_elections = cursor.fetchall()

    visible_elections = []

    for election in all_elections:
        start = election['start_time']
        end = election['end_time']

        if start <= now <= end:
            new_status = 'ongoing'
        elif now < start:
            new_status = 'upcoming'
        else:
            new_status = 'ended'

        # Only update DB if status has changed
        if election['status'] != new_status:
            cursor.execute("UPDATE elections SET status = %s WHERE election_id = %s", (new_status, election['election_id']))
            db.commit()

        if new_status in ['ongoing', 'upcoming']:
            election['status'] = new_status
            visible_elections.append(election)

    return render_template('admin/admin_home.html', elections=visible_elections)

@app.route('/admin/add_election', methods=['GET'])
def show_add_election_form():
    return render_template('admin/add_election.html')

@app.route('/admin/add_election', methods=['POST'])
def submit_add_election():
    title = request.form['title']
    start = request.form['start']
    end = request.form['end']
    created_by = session.get('user_id')

    if not created_by:
        return redirect(url_for('login'))

    try:
        status = 'upcoming'
        cursor.execute("""
            INSERT INTO elections (title, start_time, end_time, status, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, start, end, status, created_by))
        db.commit()
    except Exception as e:
        db.rollback()

    return redirect(url_for('admin_home'))

@app.route('/admin/edit_election/<int:election_id>', methods=['GET', 'POST'])
def edit_election(election_id):
    cursor.execute("SELECT * FROM elections WHERE election_id = %s", (election_id,))
    election = cursor.fetchone()
    if not election:
        return redirect(url_for('admin_home'))

    if request.method == 'POST':
        title = request.form['title']
        start = request.form['start']
        end = request.form['end']

        try:
            cursor.execute("""
                UPDATE elections
                SET title = %s, start_time = %s, end_time = %s
                WHERE election_id = %s
            """, (title, start, end, election_id))
            db.commit()
        except Exception as e:
            db.rollback()

        return redirect(url_for('admin_home'))

    return render_template('admin/edit_election.html', election=election)

@app.route('/admin/delete_election/<int:election_id>')
def delete_election(election_id):
    try:
        cursor.execute("DELETE FROM elections WHERE election_id = %s", (election_id,))
        db.commit()
    except Exception as e:
        db.rollback()

    return redirect(url_for('admin_home'))

@app.route('/admin/manage_candidates')
def manage_candidates():
    cursor.execute("""
    SELECT candidates.*, positions.name AS position, parties.party_name
    FROM candidates
    JOIN positions ON candidates.position_id = positions.position_id
    LEFT JOIN parties ON candidates.party = parties.party_id
    """)

    all_candidates = cursor.fetchall()

    grouped = {'chairperson': [], 'treasurer': [], 'kagawad': []}
    for cand in all_candidates:
        grouped[cand['position']].append(cand)

    return render_template('admin/manage_candidates.html', candidates=grouped)

@app.route('/admin/add_candidate', methods=['GET', 'POST'])
def add_candidate():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        party_name = request.form['party']
        description = request.form['description']
        position_name = request.form['position']

        # Get or insert party
        cursor.execute("SELECT party_id FROM parties WHERE party_name = %s", (party_name,))
        party = cursor.fetchone()

        if party:
            party_id = party['party_id']
        else:
            cursor.execute("INSERT INTO parties (party_name) VALUES (%s)", (party_name,))
            db.commit()
            party_id = cursor.lastrowid

        # Get position_id from position name
        cursor.execute("SELECT position_id FROM positions WHERE name = %s", (position_name,))
        position = cursor.fetchone()
        if not position:
            return redirect(url_for('add_candidate'))
        position_id = position['position_id']

        # Insert candidate
        cursor.execute("""
            INSERT INTO candidates (first_name, last_name, description, party, position_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (first_name, last_name, description, party_id, position_id))
        db.commit()

        return redirect(url_for('manage_candidates'))

    return render_template('admin/add_candidate.html')


@app.route('/admin/edit_candidate/<int:candidate_id>', methods=['GET', 'POST'])
def edit_candidate(candidate_id):
    # Fetch existing candidate
    cursor.execute("""
        SELECT c.*, p.party_name, pos.name AS position_name
        FROM candidates c
        LEFT JOIN parties p ON c.party = p.party_id
        LEFT JOIN positions pos ON c.position_id = pos.position_id
        WHERE c.candidate_id = %s
    """, (candidate_id,))
    candidate = cursor.fetchone()

    if not candidate:
        return redirect(url_for('manage_candidates'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        party_name = request.form['party']
        description = request.form['description']

        # Get or insert the party
        cursor.execute("SELECT party_id FROM parties WHERE party_name = %s", (party_name,))
        party = cursor.fetchone()

        if party:
            party_id = party['party_id']
        else:
            cursor.execute("INSERT INTO parties (party_name) VALUES (%s)", (party_name,))
            db.commit()
            party_id = cursor.lastrowid

        # Update candidate details
        cursor.execute("""
            UPDATE candidates
            SET first_name = %s,
                last_name = %s,
                party = %s,
                description = %s
            WHERE candidate_id = %s
        """, (first_name, last_name, party_id, description, candidate_id))
        db.commit()

        return redirect(url_for('manage_candidates'))

    return render_template('admin/edit_candidate.html', candidate=candidate)


@app.route('/admin/delete_candidate/<int:candidate_id>')
def delete_candidate(candidate_id):
    try:
        cursor.execute("DELETE FROM candidates WHERE candidate_id = %s", (candidate_id,))
        db.commit()
    except Exception as e:
        db.rollback()

    return redirect(url_for('manage_candidates'))

def get_grouped_results(include_visibility=False):
    visibility_condition = ""
    if include_visibility:
        visibility_condition = """
        WHERE EXISTS (
            SELECT 1 FROM result_visibility rv
            WHERE rv.position_name = p.name AND rv.visible = 1
        )
        """

    # Get all candidates with vote counts
    cursor.execute(f"""
        SELECT
            p.name AS position,
            CASE 
                WHEN c.first_name = 'Abstain' THEN 'Abstain'
                ELSE CONCAT_WS(' ', c.first_name, c.last_name)
            END AS full_name,
            c.first_name = 'Abstain' AS is_abstain,
            c.candidate_id,
            COUNT(er.result_id) AS vote_count
        FROM candidates c
        JOIN positions p ON c.position_id = p.position_id
        LEFT JOIN election_results er ON er.candidate_id = c.candidate_id
        {visibility_condition}
        GROUP BY c.candidate_id
        ORDER BY p.name ASC, c.candidate_id ASC
        """)
    rows = cursor.fetchall()

    # Visibility check
    cursor.execute("SELECT * FROM result_visibility")
    vis_rows = cursor.fetchall()
    visibility = {v['position_name'].lower(): v['visible'] for v in vis_rows}

    grouped = {
        'chairperson': {'names': [], 'votes': [], 'visible': visibility.get('chairperson', 0)},
        'treasurer': {'names': [], 'votes': [], 'visible': visibility.get('treasurer', 0)},
        'kagawad': {'names': [], 'votes': [], 'visible': visibility.get('kagawad', 0)}
    }

    for row in rows:
        pos = row['position'].lower()
        if pos in grouped:
            grouped[pos]['names'].append("Abstain" if row['is_abstain'] else row['full_name'])
            grouped[pos]['votes'].append(row['vote_count'])

    return grouped

@app.route('/admin/results')
def admin_results():
    ensure_abstain_candidates()
    results = get_grouped_results(include_visibility=False)
    return render_template('admin/admin_result.html', results=results)

@app.route('/admin/update_visibility', methods=['POST'])
def update_visibility():
    data = request.get_json()
    position = data.get('position')
    visible = data.get('visible')

    if not position:
        return ('', 204)

    cursor.execute("""
        INSERT INTO result_visibility (position_name, visible)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE visible = VALUES(visible)
    """, (position.lower(), visible))
    db.commit()

    return ('', 204)

@app.route('/admin/verify_user')
def verify_user_page():
    cursor.execute("SELECT * FROM users WHERE status = 'pending'")
    pending_users = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE status = 'verified'")
    verified_users = cursor.fetchall()

    return render_template('admin/verify_user.html', pending_users=pending_users, verified_users=verified_users)

@app.route('/admin/verify_user/<int:user_id>')
def verify_user(user_id):
    cursor.execute("UPDATE users SET status = 'verified' WHERE user_id = %s", (user_id,))
    db.commit()
    return redirect(url_for('verify_user_page'))

@app.route('/admin/reject_user/<int:user_id>')
def reject_user(user_id):
    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    db.commit()
    return redirect(url_for('verify_user_page'))

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    db.commit()
    return redirect(url_for('verify_user_page'))

@app.route('/admin/vote_history')
def vote_history():
    cursor.execute("""
        SELECT u.voter_id, MAX(v.timestamp) AS timestamp
        FROM votes v
        JOIN users u ON v.user_id = u.user_id
        GROUP BY u.user_id
        ORDER BY timestamp DESC
    """)
    votes = cursor.fetchall()
    return render_template('admin/vote_history.html', votes=votes)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

@app.route('/admin/profile')
@login_required
def admin_profile():
    admin_id = session.get('user_id')
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (admin_id,))
    admin = cursor.fetchone()
    response = make_response(render_template('admin/admin_profile.html', admin=admin))
    return no_cache(response)

@app.route('/admin/edit_profile')
@login_required
def admin_edit_profile():
    admin_id = session.get('user_id') 
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (admin_id,))
    admin = cursor.fetchone()
    return render_template('admin/admin_edit_profile.html', admin=admin)

@app.route('/admin/update_profile', methods=['POST'])
@login_required
def update_admin_profile():
    admin_id = session.get('user_id')
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    password = hash_password(request.form['password'].strip())

    if password:
        cursor.execute("""
            UPDATE users SET first_name=%s, last_name=%s, email=%s, password_hash=%s
            WHERE user_id=%s
        """, (first_name, last_name, email, password, admin_id))

    else:
        cursor.execute("""
            UPDATE users SET first_name=%s, last_name=%s, email=%s
            WHERE user_id=%s
        """, (first_name, last_name, email, admin_id))

    db.commit()
    return redirect(url_for('admin_profile'))

@app.route('/logout')
def logout():
    session.clear()
    response = redirect(url_for('login'))
    # Prevent going back after logout
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

# --- USER END ---
@app.route('/pending_user')
def user_pending():
    voter_id = session.get('user_pending')
    return render_template('user/user_pending.html', voter_id=voter_id)

@app.route('/user/home')
def user_home():
    user_id = session.get('user_id')

    cursor.execute("""
        SELECT * FROM elections
        WHERE status IN ('ongoing', 'upcoming')
        ORDER BY start_time DESC
    """)
    raw_elections = cursor.fetchall()

    now = datetime.now()
    elections = []

    for election in raw_elections:
        start = election['start_time']
        end = election['end_time']
        if start <= now <= end:
            election['status'] = 'ongoing'
        elif now < start:
            election['status'] = 'upcoming'
        elections.append(election)

    # Get IDs of elections the user has voted in
    cursor.execute("SELECT election_id FROM votes WHERE user_id = %s", (user_id,))
    voted = cursor.fetchall()
    voted_elections = [row['election_id'] for row in voted]

    return render_template('user/user_home.html', elections=elections, voted_elections=voted_elections)

@app.route('/user/vote', methods=['GET', 'POST'])
def vote():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    now = datetime.now()

    # Fetch ongoing election
    cursor.execute("""
        SELECT * FROM elections
        WHERE start_time <= %s AND end_time >= %s
        ORDER BY start_time DESC LIMIT 1
    """, (now, now))
    election = cursor.fetchone()

    if not election:
        return redirect(url_for('user_home'))

    election_id = election['election_id']

    # Check if user already voted in this election
    cursor.execute("SELECT 1 FROM votes WHERE user_id = %s AND election_id = %s", (user_id, election_id))
    if cursor.fetchone():
        return redirect(url_for('vote_success'))

    # Fetch all candidates grouped by position
    cursor.execute("""
        SELECT c.*, p.name AS position_name, pt.party_name
        FROM candidates c
        JOIN positions p ON c.position_id = p.position_id
        LEFT JOIN parties pt ON c.party = pt.party_id
    """)
    raw_candidates = cursor.fetchall()

    grouped = {'chairperson': [], 'treasurer': [], 'kagawad': []}
    for cand in raw_candidates:
        position = cand['position_name'].lower()
        if position in grouped:
            grouped[position].append(cand)

    errors = {}

    if request.method == 'POST':
        chair_id = request.form.get('chairperson')
        treasurer_id = request.form.get('treasurer')
        kagawad_ids = request.form.getlist('kagawad')

        # Validate
        if not chair_id:
            errors['chairperson'] = "You need to choose at least one."
        if not treasurer_id:
            errors['treasurer'] = "You need to choose at least one."
        if not kagawad_ids:
            errors['kagawad'] = "You need to choose at least one."
        elif len(kagawad_ids) > 7:
            errors['kagawad'] = "You can vote for up to 7 councilors only."

        if errors:
            return render_template('user/vote.html', candidates=grouped, errors=errors)

        # Record function
        def record_vote(candidate_id):
            cursor.execute("""
                SELECT c.candidate_id, c.position_id
                FROM candidates c
                JOIN positions p ON c.position_id = p.position_id
                WHERE c.candidate_id = %s
            """, (candidate_id,))
            candidate = cursor.fetchone()
            if not candidate:
                return

            cursor.execute("""
                INSERT INTO votes (user_id, election_id, candidate_id, position_id)
                VALUES (%s, %s, %s, %s)
            """, (user_id, election_id, candidate['candidate_id'], candidate['position_id']))

            cursor.execute("""
                INSERT INTO election_results (election_id, candidate_id, total_votes)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE total_votes = total_votes + 1
            """, (election_id, candidate['candidate_id']))

        # Record votes
        record_vote(chair_id)
        record_vote(treasurer_id)
        for kid in kagawad_ids:
            record_vote(kid)

        db.commit()
        return redirect(url_for('vote_success'))

    return render_template('user/vote.html', candidates=grouped, errors=errors)



@app.route('/user/vote_success')
def vote_success():
    return render_template('user/vote_success.html')

@app.route('/user/candidates')
def user_candidates():
    cursor.execute("""
        SELECT c.*, pos.name AS position, p.party_name
        FROM candidates c
        JOIN positions pos ON c.position_id = pos.position_id
        LEFT JOIN parties p ON c.party = p.party_id
    """)
    all_candidates = cursor.fetchall()

    # Group by position for display
    grouped = {
        'chairperson': [],
        'treasurer': [],
        'kagawad': []
    }

    for cand in all_candidates:
        position = cand['position'].lower()
        if position in grouped:
            grouped[position].append(cand)

    return render_template('user/user_candidate_details.html', candidates=grouped)

@app.route('/user/results')
def user_results():
    ensure_abstain_candidates()
    results = get_grouped_results(include_visibility=True)
    return render_template('user/user_result.html', results=results)

# Middleware to protect user routes
def user_login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'voter':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

@app.route('/user/profile')
@user_login_required
def user_profile():
    user_id = session.get('user_id')
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    response = make_response(render_template('user/user_profile.html', user=user))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/user/edit_profile')
@user_login_required
def user_edit_profile():
    user_id = session.get('user_id')
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    response = make_response(render_template('user/user_edit_profile.html', user=user))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/user/update_profile', methods=['POST'])
@user_login_required
def update_user_profile():
    user_id = session.get('user_id')
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    password = hash_password(request.form['password'].strip())

    if password:
        cursor.execute("""
            UPDATE users SET first_name=%s, last_name=%s, email=%s, password_hash=%s
            WHERE user_id=%s
        """, (first_name, last_name, email, password, user_id))

    else:
        cursor.execute("""
            UPDATE users SET first_name=%s, last_name=%s, email=%s
            WHERE user_id=%s
        """, (first_name, last_name, email, user_id))

    db.commit()
    return redirect(url_for('user_profile'))

if __name__ == '__main__':
    app.run(debug=True)