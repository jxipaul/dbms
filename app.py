from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'joy',
    'password': '2318',
    'database': 'dbmstest'
}

# Function to get a database connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/add-student', methods=['POST'])
def add_student():
    from flask import request
    full_name = request.form['full_name']
    email = request.form['email']
    status = request.form['status']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Students (full_name, email, status)
        VALUES (%s, %s, %s)
    """, (full_name, email, status))
    conn.commit()
    cursor.close()
    conn.close()

    return dashboard()


@app.route('/delete-student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete the student's data from related tables first
    cursor.execute("DELETE FROM Grades WHERE student_id = %s", (student_id,))
    cursor.execute("DELETE FROM Enrollment WHERE student_id = %s", (student_id,))

    # Delete the student from the Students table
    cursor.execute("DELETE FROM Students WHERE student_id = %s", (student_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return dashboard()



@app.route('/filter-students', methods=['GET'])
def filter_students():
    from flask import request
    min_score = request.args.get('min_score', type=float)
    max_score = request.args.get('max_score', type=float)
    sort_order = request.args.get('sort_order', default='desc')
    limit = request.args.get('limit', type=int)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT s.student_id, s.full_name, s.email, s.status, AVG(g.score) AS average_score
        FROM Students s
        LEFT JOIN Grades g ON s.student_id = g.student_id
        GROUP BY s.student_id
        HAVING 1=1
    """
    params = []

    if min_score is not None:
        query += " AND AVG(g.score) >= %s"
        params.append(min_score)
    if max_score is not None:
        query += " AND AVG(g.score) <= %s"
        params.append(max_score)

    query += f" ORDER BY average_score {sort_order}"

    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)

    cursor.execute(query, params)
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('dashboard.html', students=students)

# Route: Home
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('home.html', students=students)

# Route: Dashboard
@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dashboard.html', students=students)

# Route: Top Students
@app.route('/top-students')
def top_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.full_name, s.email, AVG(g.score) AS average_score
        FROM Students s
        JOIN Grades g ON s.student_id = g.student_id
        GROUP BY s.student_id
        ORDER BY average_score DESC
        LIMIT 5
    """)
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('top_students.html', students=students)

# Route: Above Average Scores
@app.route('/above-average')
def above_average():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.full_name, c.course_title, g.score
        FROM Grades g
        JOIN Students s ON g.student_id = s.student_id
        JOIN Courses c ON g.course_id = c.course_id
        WHERE g.score > (
            SELECT AVG(g2.score)
            FROM Grades g2
            WHERE g2.course_id = g.course_id
        )
    """)
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('above_average.html', students=students)

# Route: Course Enrollments
@app.route('/course-enrollments')
def course_enrollments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.course_title, d.department_name, COUNT(e.student_id) AS student_count
        FROM Courses c
        JOIN Departments d ON c.department_id = d.department_id
        LEFT JOIN Enrollment e ON c.course_id = e.course_id
        GROUP BY c.course_id
    """)
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('course_popularity.html', courses=courses)

# Route: Active Students
@app.route('/active-students')
def active_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.full_name, c.course_title, g.score
        FROM Students s
        LEFT JOIN Enrollment e ON s.student_id = e.student_id
        LEFT JOIN Courses c ON e.course_id = c.course_id
        LEFT JOIN Grades g ON s.student_id = g.student_id AND c.course_id = g.course_id
        WHERE s.status = 'Active'
    """)
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('active_students.html', students=students)

# Route: Active Students and Grades
@app.route('/active-students-grades')
def active_students_grades():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            s.full_name AS student_name,
            c.course_title,
            COALESCE(g.score, 'No Grade') AS grade
        FROM Students s
        LEFT JOIN Enrollment e ON s.student_id = e.student_id
        LEFT JOIN Courses c ON e.course_id = c.course_id
        LEFT JOIN Grades g ON s.student_id = g.student_id AND c.course_id = g.course_id
        WHERE s.status = 'Active';
    """)
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('active_students_grades.html', students=students)

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)