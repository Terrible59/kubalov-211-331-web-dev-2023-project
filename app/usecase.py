from werkzeug.utils import secure_filename
import sql_queries
import mysql.connector
import uuid
import hashlib
import os
import math

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def get_years(db):
    db_conn = db.connection()
    try:
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(sql_queries.queryGetAllYears, ())
        years = cursor.fetchall()
        cursor.close()
        return years
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return []

def get_reviews(db, book_id):
    db_conn = db.connection()
    try:
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(sql_queries.queryGetBookReviews, (book_id,))
        reviews = cursor.fetchall()
        cursor.close()
        return reviews
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        raise err
        return []

def get_genres(db):
    db_conn = db.connection()
    try:
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(sql_queries.queryGetAllGenres)
        genres = cursor.fetchall()
        cursor.close()
        return genres
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        db_conn.rollback()
        return []

def get_books(db, page):
    db_conn = db.connection()
    books_per_page = 10
    try:
        offset = (page - 1) * books_per_page
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(sql_queries.queryGetBatchBook, (offset,))
        books = cursor.fetchall()
        cursor.close()
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(sql_queries.queryGetBatchBookCount, ())
        books_count = cursor.fetchall()
        cursor.close()
        return books, int(math.ceil(float(books_count[0].total_books) / float(books_per_page)))
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        db_conn.rollback()
        raise err
        return [], 0

def get_book(db, book_id):
    db_conn = db.connection()
    try:
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(sql_queries.queryGetBookByID, (book_id,))
        book = cursor.fetchall()
        cursor.close()
        return book
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        db_conn.rollback()
        return []

def create_book(file, title, short_description, year, publisher, author, page_count, genres_ids, db, save_path) -> bool:
    db_conn = db.connection()

    file.name = uuid.uuid4()
    if _allowed_file(file.filename):
        try:
            md5_hash = hashlib.md5()
            for batch in iter(lambda: file.stream.read(4096), b""):
                md5_hash.update(batch)
            file.stream.seek(0)

            filename = secure_filename(file.filename)
            hex_hash = md5_hash.hexdigest()
            mime_type = file.mimetype

            cursor = db_conn.cursor(named_tuple=True)
            cursor.execute(sql_queries.queryGetCoverIDAndFileNameByHash, (hex_hash,))

            existing_record = cursor.fetchone()
            if not existing_record:
                try:
                    if not os.path.exists(save_path):
                        os.makedirs(save_path)
                    file.save(os.path.join(save_path, filename))
                except Exception as e:
                    raise e
                    return False

                cursor.execute(sql_queries.querySetCover, (filename, mime_type, hex_hash))
                db_conn.commit()

                cursor.execute(sql_queries.queryGetCoverIDAndFileNameByHash, (hex_hash,))
                cover_record = cursor.fetchone()
            else:
                cover_record = existing_record

            cursor.execute(
                sql_queries.querySetBooks,
                (title, short_description, year, publisher, author, page_count, cover_record[0])
            )
            db_conn.commit()

            cursor.execute(sql_queries.queryGetLastBookID)
            last_book_id = cursor.fetchone()[0]

            for genres_id in genres_ids:
                cursor.execute(sql_queries.querySetBookIDAndGenresID, (last_book_id, genres_id))
                db_conn.commit()

            cursor.close()

        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
            db_conn.rollback()
            return False
    else:
        return False

    return True

def search_books(db, page, title, genres, years, volume_from, volume_to, author):
    db_conn = db.connection()
    books_per_page = 10
    offset = (page - 1) * books_per_page

    searchQuerySelect = '''
        SELECT books.*, GROUP_CONCAT(genres.name ORDER BY genres.name ASC) as genres, COALESCE(ROUND(AVG(reviews.rating), 1), 0) as average_rating,
        COUNT(reviews.id) as reviews_count, book_covers.file_name
    '''

    countQuerySelect = '''
        SELECT COUNT(DISTINCT books.id) AS total_books
    '''

    query = """
            FROM books
            LEFT JOIN book_genres ON books.id = book_genres.book_id
            LEFT JOIN genres ON book_genres.genre_id = genres.id
            LEFT JOIN reviews ON books.id = reviews.book_id
            LEFT JOIN book_covers ON books.cover_id = book_covers.id
            WHERE 1=1
        """

    params = []

    if title:
        query += " AND books.title LIKE %s"
        params.append('%' + title + '%')

    if genres:
        query += " AND book_genres.genre_id IN (%s)" % ','.join(['%s'] * len(genres))
        params.extend(genres)

    if years:
        query += " AND books.year IN (%s)" % ','.join(['%s'] * len(years))
        params.extend(years)

    if volume_from:
        query += " AND books.page_count >= %s"
        params.append(volume_from)

    if volume_to:
        query += " AND books.page_count <= %s"
        params.append(volume_to)

    if author:
        query += " AND books.author LIKE %s"
        params.append('%' + author + '%')

    searchQueryEnding = " GROUP BY books.id LIMIT 10 OFFSET " + str(offset)

    try:
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(searchQuerySelect + query + searchQueryEnding, params)
        books = cursor.fetchall()
        cursor.close()
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(countQuerySelect + query, params)
        books_count = cursor.fetchall()
        cursor.close()
        return books, int(math.ceil(float(books_count[0].total_books) / float(books_per_page)))
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return [], 0

def delete_book(book_id, db, save_path) -> bool:
    db_conn = db.connection()
    try:
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(sql_queries.queryGetCoverIDByBookID, (book_id,))
        cover_id = cursor.fetchone()[0]

        cursor.execute(sql_queries.queryGetCoverFileName, (cover_id,))
        cover_file_name = cursor.fetchone()[0]

        cursor.execute(sql_queries.queryGetBooksByCoverID, (cover_id,))
        books = cursor.fetchall()

        cursor.execute(sql_queries.queryDeleteFromBookGenres, (book_id,))
        db_conn.commit()

        cursor.execute(sql_queries.queryDeleteFromReviews, (book_id,))
        db_conn.commit()

        cursor.execute(sql_queries.queryDeleteBookByID, (book_id,))
        db_conn.commit()

        if len(books) <= 1:
            cursor.execute(sql_queries.queryDeleteFromBookCoversByCoverID, (cover_id,))
            db_conn.commit()

        cursor.close()

        if len(books) <= 1 and os.path.exists(f"{save_path}/{cover_file_name}"):
            os.remove(f"{save_path}/{cover_file_name}")

    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        db_conn.rollback()
        return False

    return True

def update_book(db, title, short_description, year, publisher, author, page_count, book_id, genres_ids) -> bool:
    db_conn = db.connection()
    try:
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(
            sql_queries.queryUpdateBookByID,
            (title, short_description, year, publisher, author, page_count, book_id)
        )
        db_conn.commit()

        cursor.execute(
            sql_queries.queryDeleteFromBookGenres,
            (book_id,)
        )
        db_conn.commit()

        for genres_id in genres_ids:
            cursor.execute(
                sql_queries.querySetBookIDAndGenresID,
                (book_id, genres_id)
            )
            db_conn.commit()

        cursor.close()

    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        db_conn.rollback()
        return False

    return True

def is_reviewed(book_id, user_id, db):
    db_conn = db.connection()
    try:
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(sql_queries.queryGetReviewText, (user_id, book_id))
        text = cursor.fetchone()
        cursor.close()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        db_conn.rollback()
        return []

    return text

def set_review(db, book_id, user_id, rating, text):
    db_conn = db.connection()
    try:
        cursor = db_conn.cursor(named_tuple=True)
        cursor.execute(sql_queries.querySetReview, (book_id, user_id, rating, text))
        db_conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        db_conn.rollback()
        return False

    return True

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS