from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

db_config = {
    'host': 'localhost',
    'user': 'joy',
    'password': '2318',
    'database': 'dbmstest'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('home.html', students=students)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

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
    return render_template('course_enrollments.html', courses=courses)

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

if __name__ == '__main__':
    app.run(debug=True)
