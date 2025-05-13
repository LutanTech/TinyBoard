from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,SelectField
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
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from functools import wraps
from flask import request, Response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from io import BytesIO
import json
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SECRET_KEY'] = 'not_a_secret'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.config['JWT_SECRET_KEY'] = 'not_really_a_secret_key'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'portal'
migrate = Migrate(app, db)
jwt = JWTManager(app)




CORS(app)


def generate_rand_id(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

class School(UserMixin, db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    name = db.Column(db.String(300), nullable=False)
    motto = db.Column(db.String(300), nullable=False)
    abr = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    phone2 = db.Column(db.String(30), nullable=False)
    logo = db.Column(db.Text, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'abr': self.abr,
            'address': self.address,
            'email': self.email,
            'phone': self.phone,
            'logo': self.logo,
            'admin_id': self.admin_id,
        }

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
    twofa_secret = db.Column(db.String(32), nullable=True)

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
    pic = db.Column(db.Text, nullable=True)
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
    date = db.Column(db.String(100), nullable=False)
    pdf = db.Column(db.Text, nullable=True)


class Grade(db.Model):
    __tablename__ = 'grade'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    student_adm = db.Column(db.String(30), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    exam1 = db.Column(db.Integer, nullable=True, default=0)
    exam2 = db.Column(db.Integer, nullable=True, default=0)

    subject = db.relationship('Subject', backref='grades')

    @hybrid_property
    def total(self):
        return (self.exam1 or 0) + (self.exam2 or 0)

class Transcript(db.Model):
    id = db.Column(db.String, primary_key=True,  unique=True, default=generate_rand_id)
    student_id = db.Column(db.String(500), nullable=False)
    hash = db.Column(db.String(500), nullable=False)
    grades_json = db.Column(db.JSON, nullable=False) 


class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    abr = db.Column(db.String(50), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    grade = db.Column(db.String, db.ForeignKey('teacher.grade'))



class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    filter_type = SelectField('Filter By', choices=[
        ('', 'Select Filter'),
        ('adm', 'ADM No.'),
        ('grade', 'Grade'),
        ('st_gender', 'Gender'),
        ('name', 'Name'),
    ])

import pyotp
import qrcode
from io import BytesIO


def generate_2fa_secret():
    raw_secret = pyotp.random_base32()
    return base64.b64encode(raw_secret.encode()).decode()

def get_totp(secret_b64):
    raw_secret = base64.b64decode(secret_b64).decode()
    return pyotp.TOTP(raw_secret)

@app.route('/generate_qr/<user_id>')
def generate_qr(user_id):
    user = Teacher.query.get(user_id)
    if not user or not user.twofa_secret:
        return jsonify({'message': 'User not found or 2FA not set up'}), 404

    totp = get_totp(user.twofa_secret)
    uri = totp.provisioning_uri(name=user.name, issuer_name="LutanTech Cashier")

    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/cashier_login', methods=['POST'])
def cashier_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    otp = data.get('otp')

    print("Received OTP:", otp if otp else 'No Otp')

    user = Teacher.query.filter_by(name=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.twofa_secret:
        return jsonify({"message": "2FA not set up"}), 403

    decoded_secret = base64.b64decode(user.twofa_secret).decode()
    totp = pyotp.TOTP(decoded_secret)

    if not totp.verify(otp, valid_window=1):
        return jsonify({"message": "Invalid 2FA code"}), 403

    access_token = create_access_token(identity=user.id)

    return jsonify({
        "message": "Login successful",
        "user": user.name,
        "access_token": access_token
    }), 200

@app.route('/cashier', methods=['POST'])
@jwt_required()
def cashier():
    user_id = get_jwt_identity()
    print(f"User ID from token: {user_id}")

    school = School.query.first()
    students = Student.query.all()

    return jsonify({
        "school": school.to_dict() if school else {},
        "students": [{
            'id': s.id,
            'name': s.name,
            'adm': s.adm,
            'grade': s.grade,
            "billed": s.billed,
            "paid": s.paid,
            "balance": s.balance
        } for s in students]
    })


from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route('/update_finances', methods=['POST'])
@jwt_required()
def update_finances():
    user_id = get_jwt_identity()
    print(f"🔐 Authenticated user ID: {user_id}")

    data = request.get_json()
    adm = data.get('adm')
    billed = data.get('billed')
    paid = data.get('paid')

    if adm is None or billed is None or paid is None:
        return jsonify({'message': '❌ Missing adm, billed, or paid'}), 400

    student = Student.query.filter_by(adm=adm).first()
    if not student:
        return jsonify({'message': '🚫 Student not found'}), 404

    try:
        student.billed = int(billed)
        student.paid = int(paid)
        student.balance = student.billed - student.paid

        db.session.commit()

        print(f"✅ User {user_id} updated finances for ADM {adm}")
        return jsonify({
            'message': '✅ Student finance updated successfully',
            'student': {
                'adm': student.adm,
                'billed': student.billed,
                'paid': student.paid,
                'balance': student.balance
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating finances for ADM {adm}: {e}")
        return jsonify({'message': f'❌ Error updating finances: {str(e)}'}), 500


@app.route('/create_bursar')
def generate_TFA():
    user = Teacher.query.get(1000)
    if user:
        user.twofa_secret = generate_2fa_secret()  
        db.session.commit()
        return jsonify(f"2FA secret set: {user.twofa_secret}")
    return jsonify('no user')


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    students_query = Student.query
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_count = 0

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if form.validate_on_submit():
        query = form.query.data.strip()
        filter_type = form.filter_type.data
    else:
        query = (request.args.get('query') or '').strip()
        filter_type = request.args.get('filter_type', '')

    if query:
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
            'pic': s.pic
        } for s in students.items]

        return jsonify({
            'students': student_list,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'ft': filter_type,
            'value': query
        })
    school = School.query.first()
    return render_template('search.html', form=form, students=students.items, total_count=total_count, query=query, school=school)

@login_manager.user_loader
def load_user(user_id):
    student = Student.query.get(user_id)
    if student:
        return student
    teacher = Teacher.query.get(user_id)
    return teacher

@app.route('/')
def index():
    school = School.query.first()
    return render_template('index.html',school=school )




@app.route('/profile')
def profile():
    dest = request.args.get('dest')
    teacher = Teacher.query.get(session.get('staff_id'))
    school = School.query.first()
    return render_template('profile.html', school=school, teacher=teacher, dest=dest if dest else None )



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
    if student:
        teacher = Teacher.query.filter_by(grade=student.grade).first()
        notifs = Notification.query.filter_by(grade=student.grade).all()
        school = School.query.first()
        return render_template("dashboard.html", school=school, student=student, teacher=teacher, notifs=notifs)
    flash('No student found', 'error')
    return redirect(url_for('logout'))


@app.route('/staff_dashboard')
@login_required
def staff_dashboard():
    school = School.query.first()

    teacher = Teacher.query.get(session.get('staff_id'))

    if not teacher:
        flash("Teacher not found in session!", "danger")
        return redirect(url_for('staff_logout'))

    students = Student.query.filter_by(grade=teacher.grade).all()
    teachers = Teacher.query.filter_by(is_active=True).all()
    print(f"School is: {school}")
    if teacher.name == 'Lutan' and (not school or school is None):
        flash('Add School Details First', 'info')
        return render_template(
            'staff_dashboard.html',
            teacher=teacher,
            school=school
        )
    return render_template(
        'staff_dashboard.html',
        teacher=teacher,
        students=students,
        teachers=teachers,
        school=school
    )


@app.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    school = School.query.first()

    staff_id = session.get('staff_id')
    teacher = Teacher.query.get(staff_id)

    if not teacher:
        flash("Teacher not found. Are you logged in properly?", "error")
        return redirect(url_for('staff_portal'))

    students = Student.query.filter_by(grade=teacher.grade).all()
    if request.method == 'POST':
        data = [{
        "id" : s.id,
        "name": s.name,
        "phone": s.phone1,
        "email": s.email,
        "balance": s.balance,
        "adm": s.adm,
        "gender" : s.st_gender

        } for s in students]
        return jsonify({'students' : data})

    return render_template(
            "students.html",
            teacher=teacher,
            students=students, school=school
        )

@app.route('/areas', methods=['POST'])
@login_required
def areasi():
    uncleared = Student.query.filter(
        Student.grade == current_user.grade,
        Student.billed - Student.paid > 0
    ).all()

    data = [{
        "name": s.name,
        "phone": s.phone1,
        "balance": s.balance
    } for s in uncleared]

    return jsonify({'students' : data})

@app.route('/student')
@login_required
def student():
    school = School.query.first()
    teacher = Teacher.query.get(session.get('staff_id'))
    id = request.args.get('id')
    student = Student.query.filter_by(id=id).first()
    print(f'looking for student with id {id}')
    if not student:
        flash(f'Student with adm {id} not found. Please check the admission number.', 'warning')
        return redirect(url_for('staff_dashboard'))

    if student.grade == teacher.grade:
        return render_template('student.html', student=student, school=school)
    else:
        flash(f'You do not have permission to view this student\'s info. Please contact the class teacher for {student.grade}.', 'info')
        return redirect(url_for('staff_dashboard'))

@app.route('/areas', methods=['POST'])
@login_required
def areas():
    uncleared = Student.query.filter(
        Student.grade == current_user.grade,
        Student.billed - Student.paid > 0
    ).all()

    data = [{
        "name": s.name,
        "phone": s.phone1,
        "balance": s.balance
    } for s in uncleared]

    return jsonify({'students' : data})






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

    db.session.commit()

    flash('Student information updated successfully! ', 'success')
    return redirect(url_for('students'))

@app.route('/portal', methods=['GET', 'POST'])
def portal():
    school = School.query.first()
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
    return render_template("student_login.html", school=school)

@app.route('/staff_portal', methods=['GET', 'POST'])
def staff_portal():
    school = School.query.first()
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
    return render_template("staff_login.html", school=school)

@app.route('/add_school', methods=['POST'])
def add_school():
    data = request.form

    school = School(
        name=data['name'],
        abr=data['abr'],
        admin_id = current_user.id,
        logo=data['pic'],
        address=data['address'],
        phone=data['phone'],
        email=data['email']


    )
    school.set_password(data['password'])
    db.session.add(school)
    db.session.commit()
    flash("School Added Successfully!", "success")
    return redirect(url_for('staff_dashboard'))

import base64

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    school = School.query.first()
    teacher = Teacher.query.get(session.get('staff_id'))
    print('accesing student')
    if request.method == 'POST':
        data = request.form

        if Student.query.filter_by(adm=data['adm']).first():
            flash("Student already in Database", "error")
            return redirect(url_for('add_student'))

        student = Student(
            name=data['name'],
            adm=data['adm'],
            email=data['email'],
            st_gender=data['st_gender'],
            grade=data['grade'],
            g_name=data['g_name'],
            g_type=data['g_type'],
            g_gender=data['g_gender'],
            phone1=data['phone1'],
            phone2=data.get('phone2'),
            phone3=data.get('phone3'),
            pic=data.get('pic') or "https://i.ibb.co/wNQGbTGf/default.jpg"
        )
        student.set_password(f"student{data['adm']}")
        subjects = Subject.query.filter_by(grade=student.grade).all()
        db.session.add(student)
        for subject in subjects:
            new_grade = Grade(subject_id=subject.id, student_adm=student.adm, teacher_id=teacher.id, exam1=0, exam2=0)
            db.session.add(new_grade)
            db.session.commit()
        flash("Student added successfully!", "success")
        return redirect(url_for('add_student'))

    return render_template('add_student.html', school=school)

@app.route('/exams')
def exams():
    school = School.query.first()
    staff_id = session.get('staff_id')
    teacher = Teacher.query.get(staff_id)

    if not teacher:
        flash("Teacher not found. Are you logged in properly?", "error")
        return redirect(url_for('staff_portal'))

    students = Student.query.filter_by(grade=teacher.grade).all()
    subjects = Subject.query.filter_by(grade=teacher.grade).all()

    grades_map = {}
    student_totals = {}
    for student in students:
        grades_map[student.adm] = {}
        total = 0
        for subject in subjects:
            grade = Grade.query.filter_by(student_adm=student.adm, subject_id=subject.id).first()
            grades_map[student.adm][subject.id] = grade
            if grade:
                total += grade.total

        student_totals[student.adm] = total

    return render_template(
        'exams.html',
        teacher=teacher,
        students=students,
        subjects=subjects,
        school=school,
        grades_map=grades_map,
        student_totals=student_totals
    )

from datetime import datetime

@app.route('/transcript')
@login_required
def transcript():
    school = School.query.first()
    student = Student.query.get(current_user.id)

    if not student:
        flash("Student not found!", "error")
        return redirect(url_for('student_portal'))

    subjects = Subject.query.filter_by(grade=student.grade).all()

    grades_map = {}
    total = 0
    grades = []

    for subject in subjects:
        grade = Grade.query.filter_by(student_adm=student.adm, subject_id=subject.id).first()
        grades_map[subject.id] = grade
        if grade:
            grades.append({
                'subject': subject.name,
                'marks': grade.total
            })
            total += grade.total

    total_score = total
    subject_count = len(subjects)
    mean_score = round(total_score / subject_count, 4) if subject_count > 0 else 0

    teacher = Teacher.query.filter_by(grade=student.grade).first()

    grades_json = json.dumps(grades)
    transcript_hash = hashlib.sha256((str(student.id) + str(total_score)).encode()).hexdigest()


    transcript = Transcript(
        student_id=student.id,
        grades_json=grades_json,
        hash=transcript_hash
    )
    db.session.add(transcript)
    db.session.commit()

    qr_url = url_for('view_transcript', transcript_id=transcript.id, _external=True)
    qr_img = qrcode.make(qr_url)
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_data = base64.b64encode(buffered.getvalue()).decode()

    return render_template(
        'transcript.html',
        student=student,
        teacher=teacher,
        subjects=subjects,
        grades_map=grades_map,
        school=school,
        now=datetime.now(),
        mean_score=mean_score,
        total_score=total_score,
        qr_data=qr_data
    )

@app.route('/transcript/<transcript_id>')
def view_transcript(transcript_id):
    transcript = Transcript.query.get_or_404(transcript_id)
    student = Student.query.get(transcript.student_id)
    grades = json.loads(transcript.grades_json)

    return render_template(
        'transcript_view.html',
        student=student,
        grades=grades,
        transcript=transcript
    )

@app.route('/scan')
def scan():
    return render_template('scan_qr.html')

@app.route('/update_grade', methods=['POST'])
def update_grade():
    data = request.get_json()
    student_adm = data.get('student_adm')
    subject_id = data.get('subject_id')
    trId = data.get('trId')

    try:
        new_grade = int(data.get('grade'))
        trId = int(trId)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid grade or teacher ID format"}), 400

    subject = Subject.query.filter_by(teacher_id=trId).first()

    print(f"Received data: student_adm={student_adm}, subject_id={subject_id}, new_grade={new_grade}")

    if subject and student_adm and subject_id is not None and trId == subject.teacher_id:
        grade = Grade.query.filter_by(student_adm=student_adm, subject_id=subject_id).first()
        if grade:
            grade.exam1 = new_grade
            db.session.commit()

            all_grades = Grade.query.filter_by(student_adm=student_adm).all()
            total = sum(g.exam1 for g in all_grades if g.exam1 is not None)

            return jsonify({
                "success": True,
                "grade": new_grade,
                "adm": student_adm,
                "tr": trId,
                "total": total
            }), 200
        else:
            print('Grade not found, returning 400')
            return jsonify({"error": "Grade not found"}), 400

    return jsonify({"error": "Invalid data or unauthorized"}), 400




@app.route('/finances')
@login_required
def finances():
    school = School.query.first()
    student = Student.query.get(session.get('student_id'))
    dest = request.args.get('dest')
    return render_template('finance.html', dest=dest, student=student, school=school)

@app.route("/subjects")
def subjects():
    school = School.query.first()
    id = session.get('staff_id')
    id2 = session.get('student_id')
    if id and request.method == 'GET':
        teacher = Teacher.query.get(session.get('staff_id'))
        students = Student.query.filter_by(grade=teacher.grade).all()
        subjects = Subject.query.filter_by(teacher_id=id).all()
        subject_list = [{"id": subject.id, "abr": subject.abr, 'grade' : subject.grade} for subject in subjects]

        return render_template(
            "subjects.html",
            teacher=teacher,
            students=students,
            subjects=subject_list,
            school=school
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
                    'abr': subject.abr,
                    'grade': subject.grade,
                    'teacher': teacher.name,
                    'teacher_id': teacher.id,
                    'teacher_phone': teacher.phone1,
                    'studentId': student.adm
                })

            flash('Updated subjects','success')
            return jsonify({
                'subjects': subjects_list
            })
        flash('success', 'success')
        return redirect(url_for('dashboard'))
from collections import Counter

def checkUser():
    if not current_user.is_authenticated:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('index'))

@app.route('/subject')
def subject():
    school = School.query.first()
    stId = request.args.get('sdId')
    sbId = request.args.get('sbId')

    if not stId or not sbId:
        flash('Missing subject details', 'error')
        return redirect(url_for('dashboard'))

    if not current_user.is_authenticated:
        flash('You must be logged in to view subject details', 'error')
        return redirect(url_for('dashboard'))

    student = Student.query.filter_by(adm=stId).first()
    current_student = Student.query.get(current_user.id)

    if not student or student.adm != current_student.adm:
        flash('Student not found or access denied', 'error')
        return redirect(url_for('dashboard'))

    subject_grade = Grade.query.filter_by(student_adm=student.adm, subject_id=sbId).first()
    if not subject_grade:
        flash('Subject grade not found', 'error')
        return redirect(url_for('dashboard'))

    subject_info = Subject.query.filter_by(id=sbId).first()
    class_grades = Grade.query.filter_by(subject_id=sbId).all()
    grade_values = [g.exam1 for g in class_grades if g.exam1 is not None]

    grade_numeric = []
    for g in grade_values:
        try:
            grade_numeric.append(float(g))
        except ValueError:
            continue

    if grade_numeric:
        class_mean = round(sum(grade_numeric) / len(grade_numeric), 2)
        highest_grade = max(grade_numeric)
        lowest_grade = min(grade_numeric)
    else:
        class_mean = highest_grade = lowest_grade = 'N/A'

    range_buckets = [0] * 11
    for g in grade_numeric:
        index = min(int(g) // 10, 10)
        range_buckets[index] += 1
    range_labels = [f"{i*10}-{i*10+9}" if i < 10 else "100" for i in range(11)]

    student_score = None
    try:
        student_score = float(subject_grade.exam1)
    except ValueError:
        pass

    position = None
    total_students = len(grade_numeric)
    if student_score is not None and total_students > 0:
        sorted_scores = sorted(grade_numeric, reverse=True)
        position = sorted_scores.index(student_score) + 1 if student_score in sorted_scores else None

    return render_template('subject.html',
                           subject=subject_grade,
                           student=student,
                           school=school,
                           subject_array=subject_info,
                           class_mean=class_mean,
                           highest_grade=highest_grade,
                           lowest_grade=lowest_grade,
                           range_labels=range_labels,
                           range_counts=range_buckets,
                           position=position,
                           total_students=total_students)





@app.route('/add_subject', methods=['POST'])
def add_subject():
    name = request.form.get('name')
    abr = request.form.get('abr')
    grade = request.form.get('grade')
    teacher = Teacher.query.get(session.get('staff_id'))

    if not teacher:
        flash('Teacher not found. Please log in again.', 'error')
        return redirect(url_for('subjects'))

    grade = grade if grade else teacher.grade

    existing_subject = Subject.query.filter_by(name=name, grade=grade).first()
    if existing_subject:
        flash(f'Subject "{name}" already exists in grade {grade}.', 'error')
        return redirect(url_for('subjects'))

    new_subject = Subject(
        name=name,
        abr=abr,
        teacher_id=teacher.id,
        grade=grade
    )

    try:
        db.session.add(new_subject)
        db.session.flush()

        students = Student.query.filter_by(grade=grade).all()
        for student in students:
            new_grade = Grade(
                subject_id=new_subject.id,
                teacher_id=teacher.id,
                student_adm=student.adm
            )
            db.session.add(new_grade)

        db.session.commit()

        flash(f'Subject "{name}" added with grade entries for students.', 'success')
        return redirect(url_for('subjects'))

    except Exception as e:
        db.session.rollback()
        # Log the error and show a more detailed message to the user
        flash(f'Failed to add subject "{name}". Error: {str(e)}', 'error')
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

@app.route('/drop_subject/<int:subject_id>/<teacher_id>', methods=['POST'])

def drop_subject(subject_id, teacher_id):
    subject = Subject.query.get(subject_id)

    if not subject:
        return jsonify({'status': 'error', 'message': 'Subject not found.'})

    try:
        db.session.delete(subject)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Subject dropped successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Failed to drop subject.'})



@app.route("/update_teacher", methods=["POST"])
@login_required
def update_teacher():
    teacher = Teacher.query.get(current_user.id)
    teacher.phone1 = request.form.get("phone", teacher.phone1)
    teacher.name = request.form.get("name", teacher.name)
    teacher.pic = request.form.get("pic", teacher.pic)
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
    token = ""
    failed = []

    for student in students:
        if not student.phone1:
            continue

        message = f"Hi {student.name}, your balance is Ksh {student.balance:,}. Please clear it at your earliest convenience. - Lutan Tech "

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
    school = School.query.first()
    if request.method == 'POST':
        data = request.form
        if Teacher.query.filter_by(email=data['email']).first():
            flash("Email already in use!", "error")
            return redirect(url_for('add_teacher'))
        teacher = Teacher(
            name=data['name'], email=data['email'], grade=data['grade'],
            phone1=data['phone1'], phone2=data.get('phone2'),
            is_admin=bool(data.get('admin')), pic=data.get('pic', 'https://i.ibb.co/wNQGbTGf/default.jpg')
        )
        teacher.set_password(data['password'])
        db.session.add(teacher)
        db.session.commit()
        flash("Teacher added successfully!", "success")
        return redirect(url_for('add_teacher'))
    return render_template('add_teacher.html', school=school)



@app.route('/add_notification', methods=['POST'])
def add_notification():
    teacher = Teacher.query.get(session.get('staff_id'))
    title = request.form.get('title')
    priority = request.form.get('priority')
    content= request.form.get('content')
    date= request.form.get('date')
    pdf= request.form.get('pdf')
    if request.method == 'POST' and content or pdf:
        new_notif = Notification(name=title, priority=priority, content=content, sender=teacher.name, grade=teacher.grade, date=date, pdf=pdf if pdf else None)
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
    print_all_routes()
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


#Error Handlers
@app.errorhandler(413)
def handle_large_files(e):
    print(app.config["MAX_CONTENT_LENGTH"])
    return "Please upload something smaller", 413


#backup
import os
import schedule
import time
from datetime import datetime
import threading
from backup import  schedule

def run_backup_scheduler():
    print('backup thread running...')
    while True:
        schedule.run_pending()
        time.sleep(60)

# Run scheduler in background thread
threading.Thread(target=run_backup_scheduler, daemon=True).start()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("Go Filter the Kids Lutan!. TinyBoard is running")
    app.run(debug=True, port=7100, host='0.0.0.0')

