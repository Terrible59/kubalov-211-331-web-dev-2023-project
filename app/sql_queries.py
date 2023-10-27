queryCheckCorrectnessLoginAndPassword = '''
    SELECT * FROM users
    WHERE login = %s AND password_hash = SHA2(%s, 256);
'''

queryGetUserByID = 'SELECT * FROM users WHERE id = %s;'

queryGetBatchBook = '''
    SELECT
        books.id,
        books.title,
        GROUP_CONCAT(genres.name ORDER BY genres.name ASC) AS genres,
        books.year,
        COALESCE(ROUND(AVG(reviews.rating), 1), 0) AS average_rating,
        COALESCE(rc.reviews_count, 0) as reviews_count,
        book_covers.file_name
    FROM
        books
    LEFT JOIN book_genres ON books.id = book_genres.book_id
    LEFT JOIN genres ON book_genres.genre_id = genres.id
    LEFT JOIN reviews ON books.id = reviews.book_id
    LEFT JOIN book_covers ON books.cover_id = book_covers.id
    LEFT JOIN (
        SELECT
            book_id,
            COUNT(id) as reviews_count
        FROM
            reviews
        GROUP BY
            book_id
    ) rc ON books.id = rc.book_id
    GROUP BY
        books.id
    ORDER BY
        books.year DESC
    LIMIT 10 OFFSET %s;
'''

queryGetBatchBookCount = '''SELECT COUNT(DISTINCT books.id) AS total_books
FROM books
LEFT JOIN book_genres ON books.id = book_genres.book_id
LEFT JOIN genres ON book_genres.genre_id = genres.id
LEFT JOIN reviews ON books.id = reviews.book_id
LEFT JOIN book_covers ON books.cover_id = book_covers.id;
'''

queryGetAllGenres = 'SELECT * FROM genres'

queryGetCoverIDAndFileNameByHash = 'SELECT id, file_name FROM book_covers WHERE md5_hash = %s;'

querySetCover = 'INSERT INTO book_covers (file_name, mime_type, md5_hash) VALUES (%s, %s, %s);'

querySetBooks = '''
    INSERT INTO books (title, short_description, year, publisher, author, page_count, cover_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
'''

queryGetLastBookID = 'SELECT LAST_INSERT_ID() AS id;'

querySetBookIDAndGenresID = 'INSERT INTO book_genres (book_id, genre_id) VALUES (%s, %s);'

queryGetCoverIDByBookID = 'SELECT cover_id FROM books WHERE id = %s'

queryGetCoverFileName = 'SELECT file_name FROM book_covers WHERE id = %s;'

queryGetBooksByCoverID = 'SELECT id FROM books WHERE cover_id = %s'

queryDeleteBookByID = 'DELETE FROM books WHERE id = %s;'

queryDeleteFromBookGenres = 'DELETE FROM book_genres WHERE book_id = %s;'

queryDeleteFromBookCoversByCoverID = 'DELETE FROM book_covers WHERE id = %s;'

queryDeleteFromReviews = 'DELETE FROM reviews WHERE book_id = %s;'

queryGetBookByID = '''
    SELECT
    b.*,
    GROUP_CONCAT(genres.name ORDER BY genres.name ASC) AS genres,
    book_covers.file_name,
    COALESCE(ROUND(AVG(reviews.rating), 1), 0) AS average_rating,
    COALESCE(rc.reviews_count, 0) as reviews_count
    FROM books AS b
    LEFT JOIN book_genres ON b.id = book_genres.book_id
    LEFT JOIN genres ON book_genres.genre_id = genres.id
    LEFT JOIN book_covers ON b.cover_id = book_covers.id
    LEFT JOIN reviews ON b.id = reviews.book_id
    LEFT JOIN (
        SELECT
            book_id,
            COUNT(id) as reviews_count
        FROM
            reviews
        GROUP BY
            book_id
    ) rc ON b.id = rc.book_id
    WHERE b.id = %s
'''

queryUpdateBookByID = '''
    UPDATE books
    SET 
        title = %s,
        short_description = %s,
        year = %s,
        publisher = %s,
        author = %s,
        page_count = %s
    WHERE id = %s;
'''

queryUpdateGenres = '''
    UPDATE book_genres
    SET 
        genre_id = %s
    WHERE book_id = %s;
'''

queryGetReviewText = 'SELECT text FROM reviews WHERE user_id = %s AND book_id = %s'

querySetReview = 'INSERT INTO reviews (book_id, user_id, rating, text, created_at) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP);'

queryGetAllYears = 'SELECT DISTINCT year FROM books ORDER BY year'

queryGetBookReviews = '''
    SELECT r.*, u.first_name AS user_name, u.last_name AS user_last_name
    FROM reviews AS r
    LEFT JOIN users AS u ON r.user_id = u.id
    WHERE r.book_id = %s
'''
