SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE TABLE genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE book_covers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(255) NOT NULL,
    md5_hash VARCHAR(255) NOT NULL
);

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    login VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    middle_name VARCHAR(255),
    role_id INT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    short_description TEXT NOT NULL,
    year INT NOT NULL CHECK (year BETWEEN 1000 AND 2024),
    publisher VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    page_count INT NOT NULL,
    cover_id INT NOT NULL,
    FOREIGN KEY (cover_id) REFERENCES book_covers(id)
);

CREATE TABLE book_genres (
    book_id INT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (book_id, genre_id),
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
);

CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 0 AND 5),
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT INTO roles (name, description) VALUES
    ('administrator', 'superuser'),
    ('moderator', 'can modify book description'),
    ('user', 'can make reviews');

INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role_id) VALUES
    ('admin', SHA2('admin_hash', 256), 'Гулькин', 'Иван', 'Павлович', (SELECT id FROM roles WHERE name = 'administrator')),
    ('moder', SHA2('moder_hash', 256), 'Петров', 'Генадий', 'Петрович', (SELECT id FROM roles WHERE name = 'moderator')),
    ('user', SHA2('user_hash', 256), 'Сидоров', 'Аркадий', NULL, (SELECT id FROM roles WHERE name = 'user'));

INSERT INTO genres (name) VALUES
    ('Фантастика'),
    ('Детектив'),
    ('Фэнтези'),
    ('Роман'),
    ('Научно-популярная'),
    ('Приключения'),
    ('Драма'),
    ('Комедия'),
    ('Триллер'),
    ('Историческая');

INSERT INTO book_covers (file_name, mime_type, md5_hash) VALUES
    ('cover1.jpg', 'image/jpeg', 'md5_hash_1'),
    ('cover2.jpg', 'image/jpeg', 'md5_hash_2'),
    ('cover3.jpg', 'image/jpeg', 'md5_hash_3'),
    ('cover4.jpg', 'image/jpeg', 'md5_hash_4'),
    ('cover5.jpg', 'image/jpeg', 'md5_hash_5');

INSERT INTO books (title, short_description, year, publisher, author, page_count, cover_id) VALUES
    ('Война и мир', 'Великая русская классика', 1869, 'Издательство ABC', 'Лев Толстой', 1225, 1),
    ('Преступление и наказание', 'История Раскольникова', 1866, 'Издательство XYZ', 'Фёдор Достоевский', 430, 2),
    ('Анна Каренина', 'Драма о любви и судьбе', 1877, 'Издательство 123', 'Лев Толстой', 864, 3),
    ('Мастер и Маргарита', 'Сатирический роман', 1967, 'Издательство ZZZ', 'Михаил Булгаков', 576, 4),
    ('1984', 'Антиутопия о тоталитаризме', 1949, 'Издательство Big Brother', 'Джордж Оруэлл', 328, 5),
    ('Маленький принц', 'Философская сказка', 1943, 'Издательство Planet B-612', 'Антуан де Сент-Экзюпери', 96, 1),
    ('Гарри Поттер и философский камень', 'Магические приключения', 1997, 'Издательство Hogwarts', 'Джоан Роулинг', 352, 2),
    ('Три товарища', 'Роман о дружбе и любви', 1936, 'Издательство Good Friends', 'Эрих Мария Ремарк', 432, 3),
    ('Зеленая миля', 'Сверхъестественная драма', 1996, 'Издательство Correctional', 'Стивен Кинг', 416, 4),
    ('Маленькие женщины', 'Семейная драма', 1868, 'Издательство Sisters', 'Луиза Мэй Олкотт', 648, 5),
    ('Метро 2033', 'Постапокалиптическая сага', 2005, 'Издательство Post-Apocalyptic', 'Дмитрий Глуховский', 458, 1),
    ('Игры разума', 'История гениального математика', 1998, 'Издательство Mathematics', 'Сильвия Нассар', 335, 2),
    ('Архипелаг ГУЛАГ', 'Исследование сталинских лагерей', 1973, 'Издательство Prison', 'Александр Солженицын', 704, 3),
    ('Игра престолов', 'Эпическая фэнтези-сага', 1996, 'Издательство Iron Throne', 'Джордж Мартин', 694, 4),
    ('Гарри Поттер и Кубок огня', 'Магические приключения', 2000, 'Издательство Hogwarts', 'Джоан Роулинг', 624, 5);

INSERT INTO book_genres (book_id, genre_id) VALUES
    (1, 4),
    (1, 7),
    (2, 2),
    (3, 4),
    (4, 6),
    (4, 7),
    (5, 1),
    (6, 3),
    (7, 3),
    (8, 4),
    (9, 6),
    (10, 4),
    (11, 1),
    (12, 2),
    (13, 4),
    (14, 7),
    (15, 2);