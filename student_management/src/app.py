from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = '12345'

# Database connection
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',  
        password='',  
        database='student_management'
    )
    return connection

@app.route('/')
def index():
    if 'role' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    if session['role'] == 'staff':
        return render_template('staff_dashboard.html')  # Render staff dashboard
    elif session['role'] == 'student':
        return render_template('student_dashboard.html')  # Render student dashboard
    else:
        return "Unauthorized access."

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']  # Role can be 'staff' or 'student'

        # Check if passwords match
        if password != confirm_password:
            return render_template('signup.html', message="Passwords do not match")

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Insert into the database
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                       (username, hashed_password, role))
        connection.commit()
        cursor.close()
        connection.close()

        # After successful signup, redirect to the login page
        return redirect(url_for('login'))  # Go to login page after signup

    return render_template('signup.html')  # Render the signup page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user and check_password_hash(user[2], password):  # user[2] is the password column
            session['user_id'] = user[0]  # Store the user ID in session
            session['username'] = user[1]  # Store the username in session
            session['role'] = user[3]  # Store the user role in session (assumes role is stored in column 3)

            # Redirect based on role (either 'student' or 'staff')
            if user[3] == 'student':
                return redirect(url_for('student_dashboard'))  # Redirect to student dashboard
            elif user[3] == 'staff':
                return redirect(url_for('staff_dashboard'))  # Redirect to staff dashboard
            else:
                return redirect(url_for('index'))  # Default redirect (in case of unknown role)

        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')  # Render login page if GET request

# LOGOUT Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name FROM departments")
    departments = cursor.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        department_id = request.form['department_id']

        cursor.execute("INSERT INTO students (name, age, department) VALUES (%s, %s, %s)", 
                       (name, age, department_id))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))

    cursor.close()
    connection.close()
    return render_template('add_student.html', departments=departments)

# View Students
@app.route('/view_students')
def view_students():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('view_students.html', students=students)

# Add Course
@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        course_name = request.form['course_name']
        course_code = request.form['course_code']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO courses (course_name, course_code) VALUES (%s, %s)", (course_name, course_code))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))
    return render_template('add_course.html')

@app.route('/enroll_student', methods=['GET', 'POST'])
def enroll_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        course_id = request.form['course_id']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))
    
    # Fetch all students and courses for dropdowns
    connection = get_db_connection()
    cursor = connection.cursor()

    # Get students
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    # Get courses
    cursor.execute("SELECT id, course_name FROM courses")
    courses = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('enroll_student.html', students=students, courses=courses)


@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Fetch all students (student_id and student_name)
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()
    
    # Fetch all courses (course_id and course_name)
    cursor.execute("SELECT id, course_name FROM courses")
    courses = cursor.fetchall()

    if request.method == 'POST':
        student_id = request.form['student_id']
        course_id = request.form['course_id']
        date = request.form['date']
        status = request.form['status']
        
        # Insert attendance record into the database
        cursor.execute("INSERT INTO attendance (student_id, course_id, date, status) VALUES (%s, %s, %s, %s)", 
                       (student_id, course_id, date, status))
        connection.commit()
        
        cursor.close()
        connection.close()
        return redirect(url_for('index'))

    cursor.close()
    connection.close()
    
    return render_template('mark_attendance.html', students=students, courses=courses)

# Record Performance
@app.route('/record_performance', methods=['GET', 'POST'])
def record_performance():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Fetch all students and courses from the database
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    cursor.execute("SELECT id, course_name FROM courses")
    courses = cursor.fetchall()

    if request.method == 'POST':
        # Handle form submission
        student_id = request.form['student_id']
        course_id = request.form['course_id']
        grade = request.form['grade']

        # Insert academic performance into the database
        cursor.execute("INSERT INTO academic_performance (student_id, course_id, grade) VALUES (%s, %s, %s)", 
                       (student_id, course_id, grade))
        connection.commit()

        cursor.close()
        connection.close()
        return redirect(url_for('index'))

    cursor.close()
    connection.close()

    return render_template('record_performance.html', students=students, courses=courses)



# Route for adding departments
@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        name = request.form['name']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO departments (name) VALUES (%s)", (name,))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))
    return render_template('add_department.html')

# Route for adding staff
@app.route('/add_staff', methods=['GET', 'POST'])
def add_staff():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        department_id = request.form['department_id']
        email = request.form['email']
        phone = request.form['phone']
        
        cursor.execute("INSERT INTO staff (name, position, department_id, email, phone) VALUES (%s, %s, %s, %s, %s)", 
                       (name, position, department_id, email, phone))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))
    
    return render_template('add_staff.html', departments=departments)

# Route for adding exams
@app.route('/add_exam', methods=['GET', 'POST'])
def add_exam():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    
    if request.method == 'POST':
        course_id = request.form['course_id']
        exam_date = request.form['exam_date']
        
        cursor.execute("INSERT INTO exams (course_id, exam_date) VALUES (%s, %s)", 
                       (course_id, exam_date))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))
    
    return render_template('add_exam.html', courses=courses)

# Route for giving feedback
@app.route('/give_feedback', methods=['GET', 'POST'])
def give_feedback():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        course_id = request.form['course_id']
        feedback_text = request.form['feedback_text']
        submission_date = request.form['submission_date']
        
        cursor.execute("INSERT INTO feedback (student_id, course_id, feedback_text, submission_date) VALUES (%s, %s, %s, %s)", 
                       (student_id, course_id, feedback_text, submission_date))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))
    
    return render_template('give_feedback.html', students=students, courses=courses)

# Route for adding extracurricular activities
@app.route('/add_extracurricular', methods=['GET', 'POST'])
def add_extracurricular():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        activity_name = request.form['activity_name']
        activity_description = request.form['activity_description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        cursor.execute("INSERT INTO extracurricular_activities (student_id, activity_name, activity_description, start_date, end_date) VALUES (%s, %s, %s, %s, %s)", 
                       (student_id, activity_name, activity_description, start_date, end_date))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))
    
    return render_template('add_extracurricular.html', students=students)

# Staff Dashboard Route
@app.route('/staff_dashboard')
def staff_dashboard():
    if 'role' in session and session['role'] == 'staff':
        return render_template('staff_dashboard.html',  username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/student_dashboard')
def student_dashboard():
    if 'role' in session and session['role'] == 'student':
        return render_template('student_dashboard.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    user_id = session['user_id']

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch the current profile data
    cursor.execute("SELECT * FROM profile WHERE user_id = %s", (user_id,))
    student = cursor.fetchone()

    if request.method == 'POST':
        # Capture the form inputs and update the database
        admission_no = request.form['admission_no']
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        blood_group = request.form['blood_group']
        father_name = request.form['father_name']
        mother_name = request.form['mother_name']
        parent_phone = request.form['parent_phone']
        aadhaar = request.form['aadhaar']
        plus_two_percentage = request.form['plus_two_percentage']

        cursor.execute("""
            UPDATE profile
            SET admission_no = %s, name = %s, dob = %s, gender = %s, email = %s, phone = %s, 
                address = %s, blood_group = %s, father_name = %s, mother_name = %s, 
                parent_phone = %s, aadhaar = %s, plus_two_percentage = %s
            WHERE user_id = %s
        """, (admission_no, name, dob, gender, email, phone, address, blood_group, father_name, mother_name, parent_phone, aadhaar, plus_two_percentage, user_id))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for('student_profile'))  # Redirect after saving data

    cursor.close()
    connection.close()


    return render_template('student_profile_edit.html', student=student)


if __name__ == '__main__':
    app.run(debug=True)
