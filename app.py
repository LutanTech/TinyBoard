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
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SECRET_KEY'] = 'not_a_secret'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.config['JWT_SECRET_KEY'] = 'not_really_a_secret_key'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = '/'
migrate = Migrate(app, db)
jwt = JWTManager(app)




CORS(app)


def generate_rand_id(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_short_rand_id(length=3):
    characters = string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

class School(UserMixin, db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)
    name = db.Column(db.String(300), nullable=False)
    motto = db.Column(db.String(300), nullable=False)
    abr = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    phone2 = db.Column(db.String(30), nullable=True)
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


class NewYearDetails(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    year = db.Column(db.String(10), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

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
    year_id = db.Column(db.String, db.ForeignKey('new_year_details.id'))


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

from sqlalchemy.ext.hybrid import hybrid_property

class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    adm = db.Column(db.String, unique=True)
    email = db.Column(db.String(100), unique=False, nullable=False)
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
    year_id = db.Column(db.String, db.ForeignKey('new_year_details.id'))

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

    subject = db.relationship('Subject', back_populates='grades')

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
    id = db.Column(db.Integer, primary_key=True, default=generate_short_rand_id, unique=True)
    name = db.Column(db.String(300), nullable=False)
    abr = db.Column(db.String(50), nullable=False)
    teacher_id = db.Column(db.String, db.ForeignKey('teacher.id'), nullable=False)
    grade = db.Column(db.String, db.ForeignKey('teacher.grade'))
    grades = db.relationship('Grade', back_populates='subject', cascade='all, delete-orphan')


class Receipt(db.Model):
    id = db.Column(db.String, primary_key=True, default=generate_rand_id)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    billed = db.Column(db.Integer, nullable=False)
    paid = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    amount_paid = db.Column(db.Integer, nullable=False)
    receipt_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_type = db.Column(db.String(50), nullable=True)
    transaction_code = db.Column(db.String(100), nullable=True)

    
    
    student = db.relationship('Student', backref=db.backref('receipts', lazy=True))
class PendingTransfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    from_teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    to_teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    status = db.Column(db.String(10), default='pending') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subject = db.relationship('Subject', backref='pending_transfers')
    from_teacher = db.relationship('Teacher', foreign_keys=[from_teacher_id])
    to_teacher = db.relationship('Teacher', foreign_keys=[to_teacher_id])

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

def clone_model_instance(instance, **overrides):
    """Clone a SQLAlchemy model instance with optional overrides."""
    data = {c.name: getattr(instance, c.name) for c in instance.__table__.columns if c.name != 'id'}
    data.update(overrides)
    return instance.__class__(**data)

@app.route('/add_academic_year', methods=['POST'])
@login_required
def add_academic_year():
    year = request.form.get('year')
    if not year:
        flash("Please provide a year.", "danger")
        return redirect(url_for("dashboard"))

    if NewYearDetails.query.filter_by(year=year).first():
        flash("That year already exists!", "warning")
        return redirect(url_for("dashboard"))

    new_year = NewYearDetails(year=year)
    db.session.add(new_year)
    db.session.flush()  

    latest_year = NewYearDetails.query.order_by(NewYearDetails.date_created.desc()).first()
    if not latest_year:
        flash("No base year to clone from.", "danger")
        return redirect(url_for("dashboard"))

    old_teachers = Teacher.query.filter_by(year_id=latest_year.id).all()
    for t in old_teachers:
        new_teacher = clone_model_instance(t, year_id=new_year.id)
        db.session.add(new_teacher)

    old_students = Student.query.filter_by(year_id=latest_year.id).all()
    for s in old_students:
        new_student = clone_model_instance(s, year_id=new_year.id)
        db.session.add(new_student)


    try:
        db.session.commit()
        flash(f"Year {year} created with cloned data from {latest_year.year}.", "success")
    except Exception as e:
        db.session.rollback()
        print("Cloning error:", e)
        flash("Error during year setup. Please try again.", "danger")

    return redirect(url_for("dashboard"))


@app.route('/cashier_login', methods=['POST'])
def cashier_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    otp = data.get('otp')

    print("Received OTP:", otp if otp else 'No Otp')

    user = Teacher.query.filter_by(name=username).first()


    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": f"Invalid credentials. Real one: {user.is_admin}"}), 401

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

    student_list = []
    for s in students:
        receipts = Receipt.query.filter_by(student_id=s.id).order_by(Receipt.created_at.desc()).limit(2).all()

        latest = receipts[0] if len(receipts) > 0 else None
        previous = receipts[1] if len(receipts) > 1 else None

        student_list.append({
            'id': s.id,
            'name': s.name,
            'adm': s.adm,
            'grade': s.grade,
            'billed': s.billed,
            'paid': s.paid,
            'balance': s.balance,
            'latest_id': latest.id if latest else None,
            'latest_balance': latest.balance if latest else None,
            'previous_id': previous.id if previous else None,
            'previous_balance': previous.balance if previous else None,
        })

    return jsonify({
        "school": school.to_dict() if school else {},
        "students": student_list
    })






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
    
    available_ids = [generate_rand_id() for _ in range(6)]

    return render_template(
        'profile.html',
        school=school,
        teacher=teacher,
        dest=dest if dest else None,
        available_ids=available_ids
    )




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
    teachers = Teacher.query.all()
    print(f"School is: {school}")
    if teacher.name == 'Default' and (not school or school is None):
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

@app.route("/update_school", methods=["POST"])
@login_required
def update_school():
    school = School.query.filter_by(admin_id=current_user.id).first()
    if not school:
        flash("School not found.", "danger")
        return redirect(url_for("staff_dashboard")) 
    school.name = request.form.get("school-name", school.name)
    school.motto = request.form.get("school-motto", school.motto)
    school.phone = request.form.get("school-tel1", school.phone)
    school.phone2 = request.form.get("school-tel2", school.phone2)
    school.email = request.form.get("school-email", school.email)
    school.address = request.form.get("school-address", school.address)

    new_logo = request.form.get("school-logo")
    if new_logo:
        school.logo = new_logo

    try:
        db.session.commit()
        flash("School profile updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print("Error updating school:", e)
        flash("Something went wrong while updating. Please try again.", "danger")

    return redirect(url_for("profile")) 

@app.route('/test_generate_receipt')
def test_generate():
    student = Student.query.first()
    return str(generate_receipt(student.id, generate_rand_id(), student.adm, 5000, 3000))


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
    p_type = data.get('payment_type')
    tr_code = data.get('transaction_code')
    print('Ptype:', p_type,' and TR ID', tr_code)
    prevdata = data.get('prevBalance')
    prev = int(prevdata) if prevdata else int(paid)


    if adm is None or billed is None or paid is None:
        return jsonify({'message': '❌ Missing adm, billed, or paid', 'icon':'error'}), 400

    student = Student.query.filter_by(adm=adm).first()
    if not student:
        return jsonify({'message': '🚫 Student not found', 'icon': 'error'}), 404

    try:
        student.billed = int(billed)
        student.paid = int(paid)
        db.session.commit()
        paid_amount = int(prev - student.balance)
        receipt_id = generate_rand_id()
        generate_receipt(student.id, receipt_id, adm, billed, paid, p_type, tr_code, paid_amount)
        print(f'Generating Receipt...{paid_amount}')
        return jsonify({
            'message': '✅ Student finance updated successfully',
            'icon': 'success',
            'receipt_url': f'/receipt/{adm}/{receipt_id}',
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
        return jsonify({'icon': 'error', 'message': f'❌ Error updating finances: {str(e)}'}), 500


from flask import render_template, abort
from datetime import datetime

from flask import send_file, flash
from io import BytesIO
import qrcode
import json


def generate_receipt(st_id, receipt_id, adm, billed, paid, p_type, transaction_code, amount_paid):
    print(f"📬 Entered generate_receipt() with data {st_id, receipt_id, adm, billed, paid, p_type, transaction_code }")
    try:
        billed=int(billed)
        paid=int(paid)
        balance = int(billed - paid)


        qr_data_dict = {
            "receipt_id": receipt_id,
            "adm": adm,
            "billed": billed,
            "paid": paid,
            "balance": balance,
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_code":transaction_code,
            "payment type": p_type,
            "Amount Paid":amount_paid
        }

        if p_type and transaction_code:
            qr_data_dict["transaction_code"] = transaction_code

        qr_data = json.dumps(qr_data_dict)

        img = qrcode.make(qr_data)
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        encoded_qr = base64.b64encode(buf.getvalue()).decode('utf-8')
        student = Student.query.filter_by(adm=adm).first()
        print('prev bal',student.balance)
        print('balance',balance)
        if p_type:
            print(f"Payment: {p_type}")
            new_receipt = Receipt(
                student_id=st_id,
                id=receipt_id,
                billed=billed,
                paid=paid,
                balance=balance,
                receipt_data=encoded_qr,
                payment_type=p_type,           
                transaction_code=transaction_code or None, 
                created_at=datetime.utcnow(), 
                amount_paid=amount_paid
            )

            db.session.add(new_receipt)
            db.session.commit()
            print("Receipt generated successfully!", "success")
            return new_receipt

    except Exception as e:
        db.session.rollback()
        flash(f"Error saving receipt: {str(e)}", "error")
        print(f"Error saving receipt: {str(e)}")
        return "Error generating receipt", 500


@app.route('/receipt/<adm>/<id>')
def show_receipt(adm, id):
    receipt = Receipt.query.filter_by(id=id).first()
    student = Student.query.filter_by(adm=adm).first()

    if not receipt:
        abort(404, "Receipt not found")
    if not student:
        abort(404, "Student not found")

    school = School.query.first()
    billed = receipt.billed
    paid = receipt.paid
    balance = receipt.balance

    return render_template('receipt.html',
                           student=student,
                           school=school,
                           billed=billed,
                           receipt=receipt,
                           paid=paid,
                           balance=balance,
                           date=datetime.now().strftime("%d %B %Y, %I:%M %p"))

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
            if staff.is_active:
                login_user(staff)
                session["staff_id"] = staff.id
                return redirect(url_for('staff_dashboard'))
            flash('Your account is inactive. Please visit IT office', 'info')
            return redirect(url_for('staff_portal'))

        flash("Invalid ID or password!", "error")
    staff = Teacher.query.get(session.get('staff_id'))
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
        email=data['email'],
        motto=data['motto']



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
        try:
            print(f"Class: {data['grade']}")
            db.session.add(student)
            print(f"Saved grade: {student.grade}")
            for subject in subjects:
                new_grade = Grade(subject_id=subject.id, student_adm=student.adm, teacher_id=teacher.id, exam1=0, exam2=0)
                db.session.add(new_grade)
                print('commited')
            db.session.commit()
            print('final commit')
            flash("Student added successfully!", "success")
            return render_template('add_student.html', school=school)
        except Exception as e:
            flash(f'Failed to add student. Error {str(e)}', 'error')
            return render_template('add_student.html', school=school)

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
    tr_id = data.get('trId')
    grade_val = data.get('grade')

    if not all([student_adm, subject_id, tr_id, grade_val]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        subject_id = int(subject_id)
        tr_id = tr_id
        new_grade = int(grade_val)
    except ValueError:
        return jsonify({"error": "Grade, subject ID must be integers"}), 400


    subject = Subject.query.filter_by(id=subject_id, teacher_id=tr_id).first()
    if not subject:
        return jsonify({"error": "Subject not found or not authorized"}), 403

    grade = Grade.query.filter_by(student_adm=student_adm, subject_id=subject_id).first()
    if not grade:
        return jsonify({"error": "Grade record not found"}), 404

    try:
        grade.exam1 = new_grade
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to update grade: {e}")
        return jsonify({"error": "Database error during grade update"}), 500
    all_grades = Grade.query.filter_by(student_adm=student_adm).all()
    total = sum(g.exam1 for g in all_grades if g.exam1 is not None)

    return jsonify({
        "success": True,
        "grade": new_grade,
        "adm": student_adm,
        "tr": tr_id,
        "total": total
    }), 200



@app.route('/finances')
@login_required
def finances():
    school = School.query.first()
    student = Student.query.get(session.get('student_id'))

    return render_template('finance.html', student=student, school=school)

@app.route('/finances/receipts', methods=['POST', 'GET'])
def get_receipts():
    if request.method == 'POST':
        student = Student.query.get(session.get('student_id'))
        receipts = Receipt.query.filter_by(student_id=student.id).all()
        old_bal = student.balance
        print(old_bal)
        school = School.query.first()
        print(receipts, student.id)
        receipt_list = [{
            'id': r.id,
            'billed': r.billed,
            'paid': r.paid,
            'balance': r.balance,
            'receipt_data': r.receipt_data,
            'tr_code':r.transaction_code,
            'type':r.payment_type or 'Cash',
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'amount_paid':r.amount_paid
        } for r in receipts]

        school_dets = {
            'name': school.name,
            'id': school.id,
            'logo': school.logo,
            'motto': school.motto,
            'address': school.address,  
            'email': school.email,
            'phone': school.phone,
            'phone2': getattr(school, 'phone2', '')  
        }

        return jsonify({
            'student': {
                'id': student.id,
                'name': student.name,
                'adm': student.adm,
                'grade': student.grade
            },
            'receipts': receipt_list,
            'school': school_dets 
        })

    return render_template('receipts.html')

    
@app.route("/subjects")
def subjects():
    school = School.query.first()
    teacher_id = session.get('staff_id')
    student_id = session.get('student_id')
    id2 = session.get('student_id')

    # If a teacher is logged in and it's a GET request
    if teacher_id and request.method == 'GET':
        teacher = Teacher.query.get(teacher_id)
        students = Student.query.filter_by(grade=teacher.grade).all()
        subjects = Subject.query.filter_by(teacher_id=teacher_id).all()
        subject_list = [{"id": sub.id, "abr": sub.abr, "grade": sub.grade} for sub in subjects]

        pending_transfers = PendingTransfer.query.filter_by(to_teacher_id=teacher.id, status='pending').all()

        return render_template(
            "subjects.html",
            teacher=teacher,
            students=students,
            subjects=subject_list,
            school=school,
            pending_transfers=pending_transfers
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
        grade_entries = [
            Grade(subject_id=new_subject.id, teacher_id=teacher.id, student_adm=student.adm)
            for student in students
        ]
        db.session.add_all(grade_entries)
        db.session.commit()

        flash(f'Subject "{name}" added with grade entries for students.', 'success')
    except Exception as e:
        db.session.rollback()
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

    subjects_to_update = Subject.query.filter_by(teacher_id=teacher.id, grade=old_grade).all()
    for subject in subjects_to_update:
        subject.grade = new_grade

    try:
        db.session.commit()
        flash(f"Grade changed to '{new_grade}'. {len(students_to_update)} students moved and {len(subjects_to_update)} subjects updated.", "success")
        return redirect(url_for('profile'))

    except Exception as e:
        db.session.rollback()
        flash('An error occured.', 'error')
    return redirect(url_for('profile'))

@app.route('/actions/<string:action>/<string:tr_id>')
def actions(action, tr_id):
    teacher = Teacher.query.filter_by(id=tr_id).first()
    allowed_actions = ['delete', 'suspend', 'activate']

    if not teacher:
        flash('Teacher not found. Are they hiding? 👀', 'error')
        return redirect(url_for('staff_dashboard'))

    if action in allowed_actions:
        if action == "delete":
            db.session.delete(teacher)  
            db.session.commit()
            flash(f"{teacher.name} deleted successfully ", 'success')
        elif action == "suspend":
            teacher.is_active = False
            db.session.commit()
            flash(f"{teacher.name} suspended indefinitely ", 'success')
        elif action == "activate":
            teacher.is_active = True
            db.session.commit()
            flash(f"{teacher.name} activated succesfully ", 'success')
    else:
        flash('Action not allowed ', 'error')
    
    return redirect(url_for('staff_dashboard'))

@app.route('/change_id/<string:id>', methods=["POST"])
def change_ID(id):
    new_id=request.form.get("new_id")
    teacher = Teacher.query.filter_by(id=id).first()
    if teacher.is_admin:
        teacher.id=new_id
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'An error occured. {str(e)}', 'error')
            return redirect(url_for('profile'))
        flash('ID changed succesfully. Please login again with your ned ID', 'success')
        return redirect(url_for('profile'))
    flash('Action performed by only ADMIN', 'info')
    return redirect(url_for('profile'))


@app.route('/drop_subject/<int:subject_id>/<teacher_id>', methods=['POST'])
def drop_subject(subject_id, teacher_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        return jsonify({'status': 'error', 'message': 'Subject not found.'})

    if str(subject.teacher_id) != str(teacher_id):
        return jsonify({'status': 'error', 'message': 'Unauthorized drop attempt.'})

    try:
        Grade.query.filter_by(subject_id=subject_id).delete()
        db.session.delete(subject)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Subject dropped successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to drop subject: {str(e)}'})

@app.route('/transfer_subject', methods=['POST'])
def transfer_subject():
    data = request.form
    current_teacher = data.get('current_teacher')
    s_id = data.get('s_id')
    to_id = data.get('to_id')

    try:
        s_id = int(s_id)
    except ValueError:
        flash('Invalid subject ID.', 'error')
        return redirect(url_for('subjects'))

    subject = Subject.query.get(s_id)
    if not subject:
        flash('No subject found.', 'error')
        return redirect(url_for('subjects'))

    if str(subject.teacher_id) != str(current_teacher):
        flash('Teacher ID mismatch.', 'error')
        return redirect(url_for('subjects'))

    new_teacher = Teacher.query.get(to_id)
    if not new_teacher:
        flash('The new teacher does not exist.', 'error')
        return redirect(url_for('subjects'))

    existing = PendingTransfer.query.filter_by(
        subject_id=s_id, from_teacher_id=current_teacher, to_teacher_id=to_id, status='pending'
    ).first()

    if existing:
        flash('A pending transfer already exists for this subject.', 'info')
        return redirect(url_for('subjects'))

    transfer = PendingTransfer(
        subject_id=s_id,
        from_teacher_id=current_teacher,
        to_teacher_id=to_id,
    )
    db.session.add(transfer)
    db.session.commit()
    flash('Transfer request sent! Awaiting new teacher\'s approval.', 'success')
    return redirect(url_for('subjects'))

@app.route('/respond_transfer/<int:transfer_id>/<action>')
def respond_transfer(transfer_id, action):
    transfer = PendingTransfer.query.get_or_404(transfer_id)
    if transfer.status != 'pending':
        flash('This transfer request has already been processed.', 'info')
        return redirect(url_for('subjects'))

    if action == 'accept':
        subject = Subject.query.get(transfer.subject_id)
        grades = Grade.query.filter_by(subject_id=subject.id).all()
        subject.teacher_id = transfer.to_teacher_id
        for grade in grades:
            grade.teacher_id = transfer.to_teacher_id
        transfer.status = 'accepted'
        flash('You have accepted the transfer.', 'success')
    elif action == 'decline':
        transfer.status = 'declined'
        flash('You have declined the transfer.', 'info')
    else:
        flash('Invalid action.', 'error')
        return redirect(url_for('subjects'))

    db.session.commit()
    return redirect(url_for('subjects'))


@app.route("/update_teacher", methods=["POST"])
@login_required
def update_teacher():
    teacher = Teacher.query.get(current_user.id)
    teacher.phone1 = request.form.get("phone", teacher.phone1)
    teacher.name = request.form.get("name", teacher.name)
    teacher.email = request.form.get("email", teacher.email)

    new_pic = request.form.get("pic")
    if new_pic:
        teacher.pic = new_pic

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
