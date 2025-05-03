from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename, send_from_directory
from flask import send_file
from flask_migrate import Migrate
from sqlalchemy import JSON
import uuid
import shortuuid
import string
import secrets
import base64
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'portal'
migrate = Migrate(app, db)

def generate_rand_id(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

class School(UserMixin, db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    name = db.Column(db.String(300), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Teacher(UserMixin, db.Model):
    __tablename__ = 'teacher'
    id = db.Column(db.String, primary_key=True,  unique=True, default=generate_rand_id)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    pic = db.Column(db.Text, nullable=True, default="https://i.ibb.co/wNQGbTGf/default.jpg")
    grade = db.Column(db.String(100), nullable=False)
    phone1 = db.Column(db.String(500), nullable=False)
    phone2 = db.Column(db.String(500), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

from sqlalchemy.ext.hybrid import hybrid_property

class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    adm = db.Column(db.String, unique=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    pic = db.Column(db.Text, nullable=True, default="https://i.ibb.co/wNQGbTGf/default.jpg")
    st_gender = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(100), nullable=False)
    g_name = db.Column(db.String(500), nullable=True)
    phone1 = db.Column(db.String(500), nullable=False)
    phone2 = db.Column(db.String(500), nullable=True)
    phone3 = db.Column(db.String(500), nullable=True)
    g_type = db.Column(db.String(50), nullable=False)
    g_gender = db.Column(db.String(50), nullable=False)
    billed = db.Column(db.Integer, nullable=False, default=5000)
    paid = db.Column(db.Integer, nullable=False, default=0)
    subjects = db.Column(JSON, nullable=True)

    @hybrid_property
    def balance(self):
        return self.billed - self.paid

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.String(50), nullable=True)
    content = db.Column(db.Text, nullable=True)
    read_by = db.Column(JSON, nullable=True)
    sender = db.Column(db.String(500), nullable=False)
    grade = db.Column(db.String(100), nullable=False)

class Grade(db.Model):
    __tablename__ = 'grade'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    abr = db.Column(db.String(50), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.grade'), nullable=False)

class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    abr = db.Column(db.String(50), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    grade = db.Column(db.String, db.ForeignKey('teacher.grade'))

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    filter_type = SelectField('Filter By', choices=[
        ('', 'Select Filter'),
        ('adm', 'ADM No.'),  
        ('grade', 'Grade'),
        ('st_gender', 'Gender'),
        ('name', 'Name'),
    ])

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    students_query = Student.query
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_count = 0

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    query = value = form.query.data.strip() if form.validate_on_submit() else request.args.get('query', '').strip()
    filter_type = form.filter_type.data if form.validate_on_submit() else request.args.get('filter_type', '')

    if value != '':
        if filter_type == 'grade':
            students_query = students_query.filter(Student.grade.ilike(f'%{query}%'))
        elif filter_type == 'adm':
            students_query = students_query.filter(Student.adm.ilike(f'%{query}%'))
        elif filter_type == 'st_gender':
            students_query = students_query.filter(Student.st_gender.ilike(f'%{query}%'))
        elif filter_type == 'name':
            students_query = students_query.filter(Student.name.ilike(f'%{query}%'))
        else:
            students_query = students_query.filter(
                (Student.name.ilike(f'%{query}%')) |
                (Student.adm.ilike(f'%{query}%')) |
                (Student.email.ilike(f'%{query}%')) |
                (Student.grade.ilike(f'%{query}%'))
            )

    total_count = students_query.count()
    students = students_query.paginate(page=page, per_page=per_page, error_out=False)

    if is_ajax and request.method == 'GET':
        student_list = [{
            'id': s.id,
            'name': s.name,
            'adm': s.adm,
            'email': s.email,
            'grade': s.grade,
            'st_gender': s.st_gender,
            'subjects': s.subjects
        } for s in students.items]

        return jsonify({
            'students': student_list,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'ft': filter_type,
            'value': value
        })

    return render_template('search.html', form=form, students=students.items, total_count=total_count, query=query)


@login_manager.user_loader
def load_user(user_id):
    student = Student.query.get(user_id)
    if student:
        return student
    teacher = Teacher.query.get(user_id)
    return teacher

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile')
def profile():
    dest = request.args.get('dest')
    teacher = Teacher.query.get(session.get('staff_id'))
    return render_template('profile.html', teacher=teacher, dest=dest if dest else None )



@app.route('/default_teacher')
def default():
    def_teacher = Teacher(name='Default', id=1000, email='default@mail.com', password_hash=generate_password_hash('default'), grade='1', phone1='0712345678', is_admin=True)
    try:
        db.session.add(def_teacher)
        db.session.commit()
        flash('default teacher created', 'success')
        return redirect(url_for('staff_portal'))
    except Exception as e:
        flash('Error occured creating default teacher', 'error')
        return redirect(url_for('staff_portal'))


@app.route('/dashboard')
@login_required
def dashboard():
    student = Student.query.get(session.get('student_id'))
    teacher = Teacher.query.filter_by(grade=student.grade).first()
    notifs = Notification.query.filter_by(grade=student.grade).all()
    return render_template("dashboard.html", student=student, teacher=teacher, notifs=notifs)

@app.route('/staff_dashboard')
@login_required
def staff_dashboard():
    teacher = Teacher.query.get(session.get('staff_id'))
    students = Student.query.filter_by(grade=teacher.grade).all()  
    teachers = Teacher.query.filter_by(is_active=True).all() 
    return render_template(
        "staff_dashboard.html",
        teacher=teacher,
        students=students,
        teachers=teachers
    )



@app.route('/students')
@login_required
def students():
    teacher = Teacher.query.get(session.get('staff_id'))
    students = Student.query.filter_by(grade=teacher.grade).all()  
    return render_template(
        "students.html",
        teacher=teacher,
        students=students
    )

@app.route('/student')
@login_required
def student():
    teacher = Teacher.query.get(session.get('staff_id'))
    id = request.args.get('id')
    student = Student.query.filter_by(id=id).first()
    print(f'looking for student with id {id}')
    if not student:
        flash(f'Student with adm {id} not found. Please check the admission number.', 'warning')
        return redirect(url_for('staff_dashboard'))

    if student.grade == teacher.grade:
        return render_template('student.html', student=student)
    else:
        flash(f'You do not have permission to view this student\'s info. Please contact the class teacher for {student.grade}.', 'info')
        return redirect(url_for('staff_dashboard'))


@app.route('/update_student', methods=['POST'])
@login_required
def update_student():
    adm = request.args.get('adm')
    student = Student.query.filter_by(adm=adm).first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('staff_dashboard'))

    student.name = request.form['name']
    student.email = request.form['email']
    student.grade = request.form['grade']
    student.st_gender = request.form['st_gender']
    student.g_name = request.form['g_name']
    student.g_type = request.form['g_type']
    student.g_gender = request.form['g_gender']
    student.phone1 = request.form['phone1']
    student.phone2 = request.form.get('phone2', None)
    student.phone3 = request.form.get('phone3', None)
    student.billed = int(request.form['billed'])
    student.paid = int(request.form['paid'])
    student.balance = int(student.billed) - int(student.paid)
    db.session.commit()
    
    flash('Student information updated successfully! ', 'success')
    return redirect(url_for('students'))



@app.route('/portal', methods=['GET', 'POST'])
def portal():
    if request.method == 'POST':
        adm = request.form.get('adm')
        password = request.form.get('password')
        student = Student.query.filter_by(adm=adm).first()
        if student and student.check_password(password):
            login_user(student)
            session["student_id"] = student.id
            return redirect(url_for('dashboard'))
        flash("Invalid Reg No. or password!", "error")
    student = Student.query.get(session.get('student_id'))
    if student:
        flash("Auto Recovered Session!", "success")
        return redirect(url_for('dashboard'))
    return render_template("student_login.html")

@app.route('/staff_portal', methods=['GET', 'POST'])
def staff_portal():
    if request.method == 'POST':
        id = request.form.get('id')
        password = request.form.get('password')
        staff = Teacher.query.filter_by(id=id).first()
        if staff and staff.check_password(password):
            login_user(staff)
            session["staff_id"] = staff.id
            return redirect(url_for('staff_dashboard'))
        flash("Invalid ID or password!", "error")
    staff = Teacher.query.get(session.get('staff_id'))
    if staff:
        flash("Auto Recovered Session!", "success")
        return redirect(url_for('staff_dashboard'))
    return render_template("staff_login.html")



@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    teacher = Teacher.query.get(session.get('staff_id'))
    if request.method == 'POST':
        data = request.form
        if Student.query.filter_by(adm=data['adm']).first():
            flash("Student already in Database", "error")
            return redirect(url_for('add_student'))
        student = Student(
            name=data['name'], adm=data['adm'], email=data['email'],
            st_gender=data['st_gender'], grade=data['grade'] or teacher.grade,
            g_name=data['g_name'], g_type=data['g_type'], g_gender=data['g_gender'],
            phone1=data['phone1'], phone2=data.get('phone2'), phone3=data.get('phone3'),
            pic=data.get('pic', 'default.png')
        )
        student.set_password(f"student{data['adm']}")
        db.session.add(student)
        db.session.commit()
        flash("Student added successfully!", "success")
        return redirect(url_for('add_student'))
    return render_template('add_student.html')

@app.route('/finances')
@login_required
def finances():
    student = Student.query.get(session.get('student_id'))
    dest = request.args.get('dest')
    return render_template('finance.html', dest=dest, student=student)

@app.route("/subjects")
def subjects():
    id = session.get('staff_id')
    id2 = session.get('student_id')
    if id and request.method == 'GET':
        teacher = Teacher.query.get(session.get('staff_id'))
        students = Student.query.filter_by(grade=teacher.grade).all()  
        subjects = Subject.query.filter_by(teacher_id=id).all()
        subject_list = [{"id": subject.id, "name": subject.name, 'grade' : subject.grade} for subject in subjects]

        return render_template(
            "subjects.html",
            teacher=teacher,
            students=students,
            subjects=subject_list
        )
    if id2:
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        postMethod = request.headers.get('method') == 'POST'
        student = Student.query.get(session.get('student_id'))
        subjects = Subject.query.filter_by(grade=student.grade).all()
        if is_ajax and postMethod:
            subjects_list = []
            for subject in subjects:
                teacher = Teacher.query.filter_by(id=subject.teacher_id).first()
                subjects_list.append({
                    'id': subject.id,
                    'name': subject.name,
                    'grade': subject.grade,
                    'teacher': teacher.name,
                    'teacher_phone': teacher.phone1
                })

            flash('Updated subjects','success')
            return jsonify({
                'subjects': subjects_list
            })
        flash('success', 'success')
        return redirect(url_for('dashboard'))

@app.route('/add_subject', methods=['POST'])
def add_subject():
    name = request.form.get('name')
    abr = request.form.get('abr')
    grade = request.form.get('grade')
    teacher = Teacher.query.get(session.get('staff_id'))
    new_subject = Subject(name=name, abr=abr, teacher_id=teacher.id, grade=grade if grade else teacher.grade)
    try:
        db.session.add(new_subject)
        db.session.commit()
        flash(f'{name} subject added','success' )
        return redirect(url_for('subjects'))
    except Exception as e:
        db.session.rollback()
        flash(f'{name} subject add failed. Error `{str(e)}`','error' )
        return redirect(url_for('subjects'))
    

@app.route('/change_class/<teacher_id>', methods=['POST'])
def change_teacher_class(teacher_id):
    new_grade = request.form.get('new_grade')

    if not new_grade:
        return jsonify({'status': 'error', 'message': 'New grade is required'}), 400

    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({'status': 'error', 'message': 'Teacher not found'}), 404

    old_grade = teacher.grade
    if old_grade == new_grade:
        return jsonify({'status': 'error', 'message': 'Teacher is already assigned to this grade'}), 400

    teacher.grade = new_grade


    students_to_update = Student.query.filter_by(grade=old_grade).all()
    for student in students_to_update:
        student.grade = new_grade

    subjects_to_delete = Subject.query.filter_by(teacher_id=teacher.id, grade=old_grade).all()
    for subject in subjects_to_delete:
        db.session.delete(subject)

    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f"Grade changed to '{new_grade}'. {len(students_to_update)} students moved 🚀 and previous class' {len(subjects_to_delete)} subjects deleted ."
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Commit failed: {str(e)}'}), 500

@app.route('/drop_subject/<int:subject_id>/<int:teacher_id>', methods=['POST'])
def drop_subject(subject_id, teacher_id):
    subject = Subject.query.filter_by(id=subject_id, teacher_id=teacher_id).first()

    if not subject:
        return jsonify({'status': 'error', 'message': 'Subject not found or not owned by this teacher'}), 404

    try:
        db.session.delete(subject)
        db.session.commit()
        flash('subject dropped succesfully', 'success')
        return redirect(url_for('subjects'))
    except Exception as e:
        db.session.rollback()
        flash('subject drop failed', 'error')
        return redirect(url_for('subjects'))


@app.route("/update_teacher", methods=["POST"])
@login_required
def update_teacher():
    teacher = Teacher.query.get(current_user.id)
    teacher.phone1 = request.form.get("phone", teacher.phone1)
    teacher.email = request.form.get("email", teacher.email)
    try:
        db.session.commit()
        flash("Profile updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error updating profile. Try again.", "danger")
        print(e)

    return redirect(url_for("profile"))

@app.route('/send-bulk-whatsapp')
def send_bulk_whatsapp():
    students = Student.query.filter(Student.balance > 0).all()
    token = "WA3KnRnybEhsZ1x6NVgv"
    failed = []

    for student in students:
        if not student.phone1:
            continue  

        message = f"Hi {student.name}, your balance is Ksh {student.balance:,}. Please clear it at your earliest convenience. - Lutan Tech 💼"

        response = requests.post(
            'https://api.fonnte.com/send',
            headers={"Authorization": token},
            data={
                'target': student.phone1,
                'message': message,
                'countryCode': '254',
            }
        )

        result = response.json()
        if not result.get('status'):
            failed.append(student.name)
    if failed:
        flash(f"Some messages failed to send: {', '.join(failed)}", "danger")
    else:
        flash(f"Successfully sent WhatsApp messages to {len(students)} students!", "success")

    return redirect(url_for('students')) 

@app.route('/add_teacher', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        data = request.form
        if Teacher.query.filter_by(email=data['email']).first():
            flash("Email already in use!", "error")
            return redirect(url_for('add_teacher'))
        teacher = Teacher(
            name=data['name'], email=data['email'], grade=data['grade'],
            phone1=data['phone1'], phone2=data.get('phone2'),
            is_admin=bool(data.get('admin')), pic=data.get('pic')
        )
        teacher.set_password(data['password'])
        db.session.add(teacher)
        db.session.commit()
        flash("Teacher added successfully!", "success")
        return redirect(url_for('add_teacher'))
    return render_template('add_teacher.html')



@app.route('/add_notification', methods=['POST'])
def add_notification():
    teacher = Teacher.query.get(session.get('staff_id'))
    title = request.form.get('title')
    priority = request.form.get('priority')
    content= request.form.get('content')
    if request.method == 'POST':
        new_notif = Notification(name=title, priority=priority, content=content, sender=teacher.name, grade=teacher.grade)
        try:
            db.session.add(new_notif)
            db.session.commit()
            flash('Notification Posted Succesfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occured. Try again!', 'error')
            print(f'error occured adding notification. {str(e)}')
        return redirect(url_for('profile'))
    flash('Wrong input method. Try again!', 'error')
    return redirect(url_for('profile'))

def print_all_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'Endpoint': rule.endpoint,
            'URL': str(rule),
            'Methods': ', '.join(rule.methods)
        })
    # Print or return the routes list
    for route in routes:
        print(f"Endpoint: {route['Endpoint']}, URL: {route['URL']}, Methods: {route['Methods']}")

@app.route('/print_routes')
def show_routes():
    print_all_routes()  # Print all routes to the console
    return "Check your console for the list of routes."


@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('portal'))

@app.route('/staff_logout')
def staff_logout():
    logout_user()
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('staff_portal'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=7100)
