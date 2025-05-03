<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Вход</title>
</head>
<body>
    <h1>Вход</h1>
    <form method="POST">
        <input type="text" name="username" placeholder="Имя пользователя" required><br>
        <input type="password" name="password" placeholder="Пароль" required><br>
        <button type="submit">Войти</button>
    </form>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <p style="color:red;">{{ message }}</p>
        {% endfor %}
      {% endif %}
    {% endwith %}
</body>
</html># create_user.py

from app import db, User
from werkzeug.security import generate_password_hash

# Создаём таблицы (если их ещё нет)
db.create_all()

# Создание первого администратора
admin = User(username='admin', password=generate_password_hash('yourpassword'), role='admin')

# Добавляем в базу данных
db.session.add(admin)
db.session.commit()

print("Администратор создан успешно!")