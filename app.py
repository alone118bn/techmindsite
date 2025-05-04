from flask import Flask, render_template, redirect, url_for, flash, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import feedparser
import os
import uuid
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask_babel import Babel, get_locale

# Инициализация приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Замените на безопасный ключ!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BABEL_DEFAULT_LOCALE'] = 'ru'
bael = Babel(app)

# Инициализация расширений
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
admin = Admin(app, name='TechMind Admin', template_mode='bootstrap4')
migrate = Migrate(app, db)

@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)

# Переводы
translations = {
    'en': {
        'Login': 'Login',
        'Register': 'Register',
        'Logout': 'Logout',
        'Welcome': 'Welcome to TechMind!',
        'Username': 'Username',
        'Password': 'Password',
        'Language': 'Language',
        'Submit': 'Submit',
        'Invalid username or password': 'Invalid username or password',
        'Logged in successfully!': 'Logged in successfully!',
        'Registration successful! Please log in.': 'Registration successful! Please log in.',
        'You have been logged out.': 'You have been logged out.'
    },
    'ru': {
        'Login': 'Войти',
        'Register': 'Регистрация',
        'Logout': 'Выйти',
        'Welcome': 'Добро пожаловать в TechMind!',
        'Username': 'Имя пользователя',
        'Password': 'Пароль',
        'Language': 'Язык',
        'Submit': 'Отправить',
        'Invalid username or password': 'Неверное имя пользователя или пароль',
        'Logged in successfully!': 'Успешный вход!',
        'Registration successful! Please log in.': 'Регистрация прошла успешно! Пожалуйста, войдите.',
        'You have been logged out.': 'Вы вышли из системы.'
    }
}

def _(text):
    lang = request.cookies.get('lang', 'en')
    return translations.get(lang, translations['en']).get(text, text)

# RSS-ленты
RSS_FEEDS = {
    "tech": [
        "https://news.google.com/rss/search?q=android+AI+technology&hl=ru&gl=RU&ceid=RU:ru",
        "https://habr.com/ru/rss/all/all/?fl=ru",
        "https://habr.com/ru/rss/hub/artificial_intelligence/?fl=ru",
        "https://habr.com/ru/rss/hub/android_dev/?fl=ru",
        "https://habr.com/ru/rss/hub/mobile_development/?fl=ru"
    ]
}

def get_news():
    news = []
    seen_titles = set()
    for url in RSS_FEEDS["tech"]:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry.title not in seen_titles:
                seen_titles.add(entry.title)
                news.append({"title": entry.title, "link": entry.link})
            if len(news) >= 10:
                break
        if len(news) >= 10:
            break
    return news

# Модель пользователя
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")  # Роль: user или admin
    avatar_filename = db.Column(db.String(256), nullable=True)

    def repr(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Кастомный доступ к админке
class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == "admin"

admin.add_view(AdminModelView(User, db.session))

# --- Маршруты ---

@app.route("/")
def home():
    articles = get_news()
    return render_template("index.html", articles=articles, _=_)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash(_('Invalid username or password'), 'danger')
            return redirect(url_for('login'))
        login_user(user)
        flash(_('Logged in successfully!'), 'success')
        return redirect(url_for('admin.index') if user.role == "admin" else url_for('home'))
    return render_template("login.html", _=_)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash(_('Username already exists.'), 'danger')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash(_('Registration successful! Please log in.'), 'success')
            return redirect(url_for('login'))
    return render_template("register.html", _=_)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar.filename:
                # Безопасное имя файла
                filename = secure_filename(avatar.filename)
                # Уникальное имя, чтобы не было конфликтов
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join('static', 'uploads', unique_filename)
                avatar.save(filepath)

                # Сохраняем имя файла в базе
                current_user.avatar_filename = unique_filename
                db.session.commit()
                flash(_('Avatar uploaded successfully.'), 'success')
            else:
                flash(_('No file selected.'), 'warning')
    return render_template("profile.html")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = os.path.join(app.root_path, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        file = request.files.get('avatar')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(path)

            # Сжимаем до 300x300
            img = Image.open(path)
            img.thumbnail((300, 300))
            img.save(path)

            # Удаляем старый аватар, если есть
            old_avatar = current_user.avatar_filename
            if old_avatar:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_avatar)
                if os.path.exists(old_path):
                    os.remove(old_path)

            current_user.avatar_filename = unique_name
            db.session.commit()

            flash(_('Profile updated successfully'), 'success')
            return redirect(url_for('profile'))

        flash(_('No file selected or invalid upload'), 'warning')

    return render_template('edit_profile.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out.'), 'info')
    return redirect(url_for('home'))

@app.route('/set_language/<lang>')
def set_language(lang):
    resp = make_response(redirect(request.referrer or url_for('home')))
    resp.set_cookie('lang', lang, max_age=60*60*24*365)
    return resp

@app.route('/admin-panel')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('home'))

    users = User.query.all()
    return render_template('admin_panel.html', users=users)

# --- Запуск приложения ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)