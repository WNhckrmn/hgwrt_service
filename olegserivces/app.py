import tarfile
from flask import Flask, render_template, request, redirect, url_for, flash, abort, render_template_string, send_from_directory
from flask_login import LoginManager, login_user, logout_user, current_user,UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_migrate import Migrate
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students_teachers.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
migrate = Migrate(app, db)

app.config['UPLOAD_FOLDER'] = 'uploads/'

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'zip', 'tar.gz'}


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    students = db.relationship('Student', backref='teacher', lazy=True)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    grades = db.relationship('Grade', backref='student', lazy=True)
    notes = db.relationship('Note', backref='student', lazy=True)
    is_active = True

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.id


class Grade(db.Model, UserMixin):
    __tablename__ = 'grades'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    note = db.Column(db.Text)  # Добавляем поле для заметок


class Note(db.Model, UserMixin):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    note = db.Column(db.Text)  # Добавляем поле с текстом
    is_encrypted = db.Column(db.Boolean, default=False)


class Resume(db.Model, UserMixin):
    __tablename__ = 'Resume'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gobletoffire')
def gobletoffire():
    return render_template('gobletoffire.html')


@app.route('/upload', methods=['GET','POST'])
def upload_file():
    if request.method == 'POST':
        # Проверка, есть ли файл в запросе
        if 'file' not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files['file']
        filename = file.filename
        if file.filename == '':
            flash("No selected file")
            return redirect(request.url)
        if Resume.query.filter_by(student_id=current_user.id).first() is not None or Resume.query.filter_by(filename = filename).first() is not None:
            flash("Yor are download your resume")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Сохранение файла
            print(file)
            student_name = Student.query.filter_by(id=current_user.id).first().name

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], student_name)
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            file.save(file_path)
            resume = Resume(student_id=current_user.id, filename=filename)
            db.session.add(resume)
            db.session.commit()
            # Если это tar, распаковать его
            if file.filename.endswith('.tar.gz'):
                with tarfile.open(file_path, 'r:gz') as tar:
                    tar.extractall(path=app.config['UPLOAD_FOLDER'])

            return f"File {file.filename} uploaded successfully!"
    return render_template('upload.html')


@login_manager.user_loader
def load_user(user_id):
    student = Student.query.get(int(user_id))
    return student


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password_hash = request.form['password_hash']
        student = Student.query.filter_by(name=name).first()
        data = request.headers.get('Referer')
        if student and check_password_hash(student.password_hash, password_hash):
            print("+")
            login_user(student)
            return redirect(url_for('index'))
        flash(f'Invalid username or password on {data[22:]}', 'error')
    return render_template('login.html')


@app.route('/dambldoor')
def dambldoor():
    return render_template('dabmldoor.html')


@app.route('/profile/<int:student_id>/grades', methods=['GET', 'POST'])
def grades(student_id):
    student = Student.query.get_or_404(student_id)
    grads = student.grades
    return render_template('grades.html', grades=grads, student=student)


@app.route('/profile/<int:student_id>/notes', methods=['GET', 'POST'])
def notes(student_id):
    student = Student.query.get_or_404(student_id)
    nots = student.notes
    return render_template('notes.html', notes=nots, student=student)


@app.route("/profile/<int:student_id>/notes/add_note/", methods=['GET', 'POST'])
def add_note(student_id):
    if current_user.is_authenticated:
        if request.method == 'POST':
            text = request.form['data']

            is_encrypted = bool(request.form['is_encrypted'])

            if is_encrypted:
                cipher = AES.new(get_random_bytes(16), AES.MODE_ECB)
                plaintxt = pad(text.encode(),AES.block_size)
                text = cipher.encrypt(plaintxt)
            new_note = Note(note=text.decode('utf-8'), is_encrypted=is_encrypted, student_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            return redirect(url_for('notes', student_id=current_user.id))
        return render_template('add_note.html', student_id = current_user.id)
    else:
        abort(404)


@app.route('/profile/<int:student_id>')
def profile(student_id):
    if current_user.is_authenticated:
        if current_user.id == student_id or current_user.name == 'dambldoor':
            student = Student.query.get_or_404(student_id)
            return render_template('profile.html', student=student)
    abort(404)


@app.route('/teachers', methods=['GET'])
def teachers_list():
    if request.method == 'GET':
        teachers = Teacher.query.all()
        return render_template('teachers_list.html', teachers=teachers)


@app.route('/students')
def students_list():
    if current_user.is_authenticated:
        if current_user.id == 9:
            students = Student.query.all()
            return render_template('students_list.html', students=students)
    abort(404)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        teacher_id = request.form['teacher']
        password_hash = request.form['password_hash']
        student = Student.query.filter_by(name=name).first()
        if student:
            flash('this name is already use', 'error')
        else:
            new_student = Student(name=name, teacher_id=teacher_id, password_hash =generate_password_hash(password_hash))
            db.session.add(new_student)
            db.session.commit()
            return redirect(url_for('index'))
        return render_template('register.html')
    else:
        teachers = Teacher.query.all()
        return render_template('register.html', teachers=teachers)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template_string(f'404 страница url {request.host+request.path} не найдена')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)



