from flask_login import LoginManager, UserMixin, current_user
from flask import redirect, url_for, flash, current_app
from functools import wraps

from users_policy import UsersPolicy
import sql_queries


def init_login_manager(app, db):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Для доступа к этой странице нужно авторизироваться.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def user_loader(user_id):
        return load_user(user_id, db)


class User(UserMixin):
    def __init__(self, user_id, user_login, role_id, first_name, last_name, middle_name):
        self.id = user_id
        self.login = user_login
        self.role_id = role_id
        if middle_name:
            self.name = first_name + " " + last_name + " " + middle_name
        else:
            self.name = first_name + " " + last_name

    def is_admin(self):
        return self.role_id == current_app.config['ADMIN_ROLE_ID']

    def is_moder(self):
        return self.role_id == current_app.config['MODER_ROLE_ID']

    def can(self, action, record=None):
        users_policy = UsersPolicy(record)
        method = getattr(users_policy, action, None)
        if method:
            return method()
        return False


def permission_check(action, db):
    def decor(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id')
            user = None
            if user_id:
                user = load_user(user_id, db)
            if not current_user.can(action, user):
                flash('Недостаточно прав для выполнения данного действия.', 'warning')
                return redirect(url_for('index'))
            return function(*args, **kwargs)

        return wrapper

    return decor


def load_user(user_id, db):
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(sql_queries.queryGetUserByID, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(user.id, user.login, user.role_id, user.first_name, user.last_name, user.middle_name)
    return None
