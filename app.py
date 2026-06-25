from flask import Flask, render_template, request, redirect
from flask import url_for, session, send_from_directory
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secretkey"

app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="smart_study"
)

cursor = conn.cursor(dictionary=True)


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        query = """
        INSERT INTO login(email, password)
        VALUES(%s, %s)
        """

        values = (email, password)

        cursor.execute(query, values)
        conn.commit()

        return """
        <script>
            alert('Login Successful');
            window.location.href='/user_dashboard';
        </script>
        """

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        query = """
        INSERT INTO register(name, email, password, role)
        VALUES(%s, %s, %s, %s)
        """

        values = (name, email, password, role)

        cursor.execute(query, values)
        conn.commit()

        return """
        <script>
            alert('Registration Successful');
            window.location.href='/login';
        </script>
        """

    return render_template('register.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():

    if request.method == 'POST':

        name = request.form['name']
        course = request.form['course']
        subject = request.form['subject']
        year = request.form['year']
        semester = request.form['semester']

        file = request.files['file']

        filename = secure_filename(file.filename)

        filepath = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )

        file.save(filepath)

        query = """
        INSERT INTO materials
        (name, course, subject, year, semester, file_name)

        VALUES(%s, %s, %s, %s, %s, %s)
        """

        values = (
            name,
            course,
            subject,
            year,
            semester,
            filename
        )

        cursor.execute(query, values)

        conn.commit()

        return """
        <script>
            alert('Material Uploaded Successfully');
            window.location.href='/view';
        </script>
        """

    return render_template('upload.html')

@app.route('/view')
def view():

    query = "SELECT * FROM materials"

    cursor.execute(query)

    materials = cursor.fetchall()

    return render_template(
        'view.html',
        materials=materials
    )

@app.route('/download/<filename>')
def download(filename):

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )


@app.route('/logout')
def logout():

    session.clear()

    return """
    <script>
        alert('Logged Out Successfully');
        window.location.href='/login';
    </script>
    """


@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        query = """
        SELECT * FROM register
        WHERE email=%s AND password=%s AND role='admin'
        """

        values = (email, password)
        cursor.execute(query, values)

        admin = cursor.fetchone()

        if admin:

            session['admin_id'] = admin['id']

            return """
            <script>
                alert('Admin Login Successful');
                window.location.href='/admin_dashboard';
            </script>
            """

        else:

            return """
            <script>
                alert('Invalid Admin Email or Password');
                window.location.href='/admin_login';
            </script>
            """

    return render_template('admin_login.html')

@app.route('/user')
def users():

    query = "SELECT * FROM register"

    cursor.execute(query)

    users = cursor.fetchall()

    return render_template(
        'user.html',
        users=users
    )


@app.route('/delete_user/<int:id>')
def delete_user(id):

    query = "DELETE FROM register WHERE id=%s"

    values = (id,)

    cursor.execute(query, values)

    conn.commit()

    return redirect('/user')


@app.route('/admin_logout')
def admin_logout():

    session.pop('admin_id', None)

    return """
    <script>
        alert('Admin Logged Out Successfully');
        window.location.href='/admin_login';
    </script>
    """

@app.route('/admin_dashboard')
def admin_dashboard():

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM register")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM materials")
    total_materials = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM materials")
    total_downloads = cur.fetchone()[0]

    cur.execute("""
        SELECT id, name, course, semester, file_name
        FROM materials
        ORDER BY id DESC
        LIMIT 10
    """)

    materials = cur.fetchall()

    cur.close()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_materials=total_materials,
        total_downloads=total_downloads,
        materials=materials
    )

@app.route('/delete_material/<int:id>')
def delete_material(id):

    cur = conn.cursor()

    cur.execute(
        "SELECT file_name FROM materials WHERE id=%s",
        (id,)
    )

    file = cur.fetchone()

    if file and file[0]:

        filepath = os.path.join(
            app.config['UPLOAD_FOLDER'],
            file[0]
        )

        if os.path.isfile(filepath):
            os.remove(filepath)

        cur.execute(
            "DELETE FROM materials WHERE id=%s",
            (id,)
        )

        conn.commit()

    cur.close()

    return redirect('/admin_dashboard')
@app.route('/user_dashboard')
def user_dashboard():

    cur = conn.cursor(dictionary=True)

    # TOTAL USERS
    cur.execute(
        "SELECT COUNT(*) AS total_users FROM register"
    )

    users = cur.fetchone()['total_users']

    # TOTAL MATERIALS
    cur.execute(
        "SELECT COUNT(*) AS total_materials FROM materials"
    )

    materials = cur.fetchone()['total_materials']

    cur.execute(
        "SELECT COUNT(*) AS total_downloads FROM materials"
    )

    downloads = cur.fetchone()['total_downloads']

    cur.execute("""
        SELECT *
        FROM materials
        ORDER BY id DESC
        LIMIT 5
    """)

    recent_materials = cur.fetchall()

    cur.close()

    return render_template(
        'user_dashboard.html',
        users=users,
        materials=materials,
        downloads=downloads,
        recent_materials=recent_materials
    )
if __name__ == '__main__':
    app.run(debug=True)