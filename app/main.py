from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import markdown

from mysql_db import MySQL
import sql_queries
import usecase
from auth import init_login_manager, permission_check, User
from flaskext.markdown import Markdown
import bleach

app = Flask(__name__)
Markdown(app)

app.config.from_pyfile('config.py')
app.secret_key = '3f611345ffbe00868b337e423e771e600d80fba91d1a32ea8e9dc4c67abb277a'

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице нужно авторизироваться.'
login_manager.login_message_category = 'warning'

UPLOAD_FOLDER = './static'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = MySQL(app)

init_login_manager(app, db)

@app.route('/')
def index():
    page = request.args.get('page', default=1, type=int)

    books_list, pages_count = usecase.get_books(db, page)

    genres = usecase.get_genres(db)
    years = usecase.get_years(db)

    if len(request.args) > 1 or (len(request.args) == 1 and not page):
        books_list, pages_count = usecase.search_books(
            db,
            page,
            request.args.get('title'),
            request.args.getlist('genres'),
            request.args.getlist('years'),
            request.args.get('volume_from'),
            request.args.get('volume_to'),
            request.args.get('author')
        )
        app.logger.info(pages_count)

    return render_template('index.html', books=books_list, pages_count=pages_count, genres=genres, years=years)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        remember = request.form.get('remember_me') == 'on'

        with db.connection().cursor(named_tuple=True) as cursor:
            cursor.execute(sql_queries.queryCheckCorrectnessLoginAndPassword, (login, password))
            print(cursor.statement)
            user = cursor.fetchone()

        if user:
            login_user(User(user.id, user.login, user.role_id, user.first_name, user.last_name, user.middle_name), remember=remember)
            flash('Вы успешно прошли аутентификацию!', 'success')
            param_url = request.args.get('next')
            return redirect(param_url or url_for('index'))

        flash('Невозможно аутентифицироваться с указанными логином и паролем', 'danger')
    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/books/add', methods=['POST', 'GET'])
@login_required
@permission_check('create', db)
def add_book():
    if request.method == 'GET':
        return render_template('create-book.html', genres=usecase.get_genres(db))

    file = request.files['book_cover']

    title = bleach.clean(request.form['title'])
    short_description = bleach.clean(request.form['short_description'])
    year = bleach.clean(request.form['year'])
    publisher = bleach.clean(request.form['publisher'])
    author = bleach.clean(request.form['author'])
    page_count = bleach.clean(request.form['page_count'])
    genres_id = request.form.getlist('genres_id')

    is_insert = usecase.create_book(
        file, title, short_description,
        year, publisher, author, page_count,
        genres_id, db, app.config['UPLOAD_FOLDER']
    )
    if is_insert:
        flash('Вы успешно добавили книгу!', 'success')
    else:
        flash('Что-то пошло не так, повторите попытку позже', 'danger')

    return redirect(url_for('index'))


@app.route('/books/delete/<int:book_id>', methods=['POST'])
@login_required
@permission_check('delete', db)
def delete_book(book_id):
    is_delete = usecase.delete_book(book_id, db, app.config['UPLOAD_FOLDER'])
    if is_delete:
        flash('Вы успешно удалили книгу!', 'success')
    else:
        flash('Что-то пошло не так, повторите попытку позже', 'success')

    return redirect(url_for('index'))


@app.route('/books/edit/<int:book_id>', methods=['POST', 'GET'])
@login_required
@permission_check('edit', db)
def edit_book(book_id):
    if request.method == 'GET':
        book = usecase.get_book(db, book_id)[0]
        genres = usecase.get_genres(db)
        return render_template('edit-book.html', genres=genres, book=book)

    title = bleach.clean(request.form['title'])
    short_description = bleach.clean(request.form['short_description'])
    year = bleach.clean(request.form['year'])
    publisher = bleach.clean(request.form['publisher'])
    author = bleach.clean(request.form['author'])
    page_count = bleach.clean(request.form['page_count'])
    genres_id = request.form.getlist('genres_id')

    is_update = usecase.update_book(db, title, short_description, year, publisher, author, page_count, book_id, genres_id)
    if is_update:
        flash('Вы успешно отредактировали книгу!', 'success')
    else:
        flash('Что-то пошло не так, повторите попытку позже', 'danger')

    return redirect(url_for('index'))


@app.route('/books/view/<int:book_id>', methods=['GET'])
def view_book(book_id):
    book = usecase.get_book(db, book_id)[0]
    if not book or not book.short_description:
        abort(404)
    description_html = markdown.markdown(book.short_description)
    reviews = usecase.get_reviews(db, book_id)
    if current_user and current_user.is_authenticated:
        review = usecase.is_reviewed(book_id, current_user.id, db)
    else:
        review = ()
    return render_template('view-book.html', book=book, description=description_html, reviews=reviews, review=review)


@app.route('/books/review/<int:book_id>', methods=['POST', 'GET'])
@login_required
@permission_check('review', db)
def review_book(book_id):
    user_id = getattr(current_user, 'id', None)
    if request.method == 'GET':
        scores = {
            5: "отлично",
            4: "хорошо",
            3: "удовлетворительно",
            2: "неудовлетворительно",
            1: "плохо",
            0: "ужасно",
        }
        return render_template("create-feedback.html", scores=scores)

    rating = request.form['rating']
    text = request.form['text']

    is_update = usecase.set_review(db, book_id, user_id, rating, text)
    if is_update:
        flash('Вы успешно добавили рецензию!', 'success')
    else:
        flash('Что-то пошло не так, повторите попытку позже', 'danger')

    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(error):
   return render_template('404.html', title = '404'), 404

if __name__ == '__main__':
    app.run(debug=True)
