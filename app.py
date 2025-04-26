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
    id = db.Column(db.String, primary_key=True,  unique=True, default=generate_rand_id)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    pic = db.Column(db.String(10000000), nullable=True, default="https://i.ibb.co/wNQGbTGf/default.jpg")
    grade = db.Column(db.String(100), nullable=False)
    phone1 = db.Column(db.String(500), nullable=False)
    phone2 = db.Column(db.String(500), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    adm = db.Column(db.String, unique=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    pic = db.Column(db.String(10000000), nullable=True, default="https://i.ibb.co/wNQGbTGf/default.jpg")
    subjects = db.Column(db.Text(), nullable=True)
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
    balance = db.Column(db.Integer, nullable=True, default=0)

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
    sender = db.Column(db.String(500), db.ForeignKey('teacher.grade'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)

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
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.grade'), nullable=False)


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
        ('subjects', 'Subjects'),
    ])

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    students_query = Student.query
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_count = 0

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if form.validate_on_submit() or request.method == 'GET':
        query = form.query.data if form.validate_on_submit() else request.args.get('query', '')
        filter_type = form.filter_type.data if form.validate_on_submit() else request.args.get('filter_type', '')

        if filter_type == 'grade':
            students_query = Student.query.filter(Student.grade.ilike(f'%{query}%'))
        elif filter_type == 'st_gender':
            students_query = Student.query.filter(Student.st_gender.ilike(f'%{query}%'))
        elif filter_type == 'subjects':
            students_query = Student.query.filter(Student.subjects.ilike(f'%{query}%'))
        else:
            students_query = Student.query.filter(
                (Student.name.ilike(f'%{query}%')) |
                (Student.adm.ilike(f'%{query}%')) |
                (Student.email.ilike(f'%{query}%')) |
                (Student.grade.ilike(f'%{query}%'))
            )

        total_count = students_query.count()
        students = students_query.paginate(page=page, per_page=per_page, error_out=False)

        if is_ajax:
            student_list = []
            for student in students.items:
                student_list.append({
                    'id': student.id,
                    'name': student.name,
                    'adm': student.adm,
                    'email': student.email,
                    'grade': student.grade,
                    'st_gender': student.st_gender,
                    'subjects': student.subjects
                })
            return jsonify({
                'students': student_list,
                'total_count': total_count,
                'page': page,
                'per_page': per_page
            })
        else:
            return render_template('search_results.html', form=form, students=students, total_count=total_count)

    if is_ajax:
        return jsonify({
            'students': [],
            'total_count': 0,
            'page': page,
            'per_page': per_page
        })

    return render_template('search_results.html', form=form, students=[], total_count=0)


@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(user_id) or Teacher.query.get(user_id)

@app.route('/')
def index():
    return redirect(url_for('portal'))


def calculate(id):
    student = Student.query.filter_by(id=id).first()
    
    if not student:
        flash(f"something went wrong calculating balance", "error")
        return

    try:
        student.balance = int(student.billed) - int(student.paid)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f" Something went wrong: {e}", "error")


@app.route('/default_teacher')
def default():
    def_teacher = Teacher(name='Default',id=1000, email='default@mail.com', password_hash=generate_password_hash('default'), grade='1', phone1='0712345678', is_admin=True)
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
    return render_template("dashboard.html", student=student)

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
        calculate(student.id)
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
    
    flash('Student information updated successfully! 🎉', 'success')
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
            calculate(student.id)
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
    student = Student.query.get(session.get('staff_id'))
    if student:
        flash("Auto Recovered Session!", "success")
        return redirect(url_for('staff_dashboard'))
    return render_template("staff_login.html")



@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        data = request.form
        if Student.query.filter_by(adm=data['adm']).first():
            flash("Student already in Database", "error")
            return redirect(url_for('add_student'))
        student = Student(
            name=data['name'], adm=data['adm'], email=data['email'],
            st_gender=data['st_gender'], grade=data['grade'],
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


@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('portal'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=7100)
