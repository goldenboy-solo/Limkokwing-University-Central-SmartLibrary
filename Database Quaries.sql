CREATE SCHEMA IF NOT EXISTS SmartLibrary;
SET search_path = SmartLibrary, public;

CREATE TABLE IF NOT EXISTS ROLES(
ROLE_ID SERIAL PRIMARY KEY,
ROLE_NAME VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS USERS(
USER_ID SERIAL PRIMARY KEY,
USERNAME VARCHAR(50) NOT NULL UNIQUE,
PASSWORD_HASH VARCHAR(10) NOT NULL,
ROLE_ID INTEGER NOT NULL REFERENCES ROLES(ROLE_ID) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS AUTHORS(
AUTHOR_ID SERIAL PRIMARY KEY,
FIRST_NAME VARCHAR(20) NOT NULL,
LAST_NAME VARCHAR(20),
BIO TEXT
);

CREATE TABLE IF NOT EXISTS BOOKS(
BOOK_ID SERIAL PRIMARY KEY,
TITLE VARCHAR(25) NOT NULL,
AUTHOR_ID INTEGER NOT NULL REFERENCES AUTHORS(AUTHOR_ID) ON DELETE CASCADE,
ISBN VARCHAR(15) UNIQUE,
YEAR_PUBLISHED INTEGER,
TOTAL_COPIES INTEGER NOT NULL CHECK (TOTAL_COPIES >= 0),
AVAILABLE_COPIES INTEGER NOT NULL CHECK (available_copies >= 0)
);

CREATE TABLE IF NOT EXISTS MEMBERS(
MEMBER_ID SERIAL PRIMARY KEY,
USER_ID INTEGER UNIQUE REFERENCES USERS(USER_ID) ON DELETE SET NULL,
FULL_NAME VARCHAR(50) NOT NULL,
PHONE VARCHAR(15),
DATE_JOINED DATE DEFAULT CURRENT_DATE,
STATUS VARCHAR(20) DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS BOOK_CLUBS(
CLUB_ID SERIAL PRIMARY KEY,
CLUB_NAME VARCHAR(20) NOT NULL UNIQUE,
DESCRIPTION TEXT,
DATE_CREATED TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS BOOK_CLUB_MEMBERS(
CLUB_ID INTEGER NOT NULL REFERENCES BOOK_CLUBS(CLUB_ID) ON DELETE CASCADE,
MEMBER_ID INTEGER NOT NULL REFERENCES MEMBERS(MEMBER_ID) ON DELETE CASCADE,
CLUB_ROLE VARCHAR(20),
DATE_JOINED DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS LOAN(
LOAN_ID SERIAL PRIMARY KEY,
BOOK_ID INTEGER NOT NULL REFERENCES BOOKS(BOOK_ID) ON DELETE RESTRICT,
MEMBER_ID INTEGER NOT NULL REFERENCES MEMBERS(MEMBER_ID) ON DELETE RESTRICT,
LOAN_DATE TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
DUE_DATE DATE NOT NULL,
RETURN_DATE TIMESTAMP WITH TIME ZONE,
STATUS VARCHAR(20) NOT NULL DEFAULT 'LOANED',
CHECK (STATUS IN ('LOANED','RETURNED','OVERDUE'))
);


INSERT INTO ROLES (ROLE_NAME) VALUES
('ADMIN'), ('LIBRARIAN'), ('MEMBER')
ON CONFLICT (ROLE_NAME) DO NOTHING;

ALTER TABLE USERS
ALTER COLUMN PASSWORD_HASH TYPE VARCHAR(100);

INSERT INTO USERS (USERNAME, PASSWORD_HASH, ROLE_ID) VALUES
('SOLOMON','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='ADMIN')),
('SAIDU','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='LIBRARIAN')),
('JANE','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='MEMBER')),
('MIKE','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='MEMBER')),
('CHRISTIAN','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='MEMBER')),
('ALFRED','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='MEMBER')),
('ANDY','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='MEMBER')),
('AMAX','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='MEMBER')),
('SAJOR','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='MEMBER')),
('ABDUL','pbkdf2_sha256$placeholder', (SELECT ROLE_ID FROM ROLES WHERE ROLE_NAME='MEMBER'))
ON CONFLICT (USERNAME) DO NOTHING;

INSERT INTO AUTHORS (FIRST_NAME, LAST_NAME, BIO) VALUES
('Chinua','Achebe','Nigerian novelist and author of Things Fall Apart.'),
('Ngugi','wa Thiong''o','Kenyan writer known for novels and plays.'),
('Jane','Austen','English novelist known for Pride and Prejudice.'),
('Mark','Twain','American author of Adventures of Huckleberry Finn.'),
('Harper','Lee','Author of To Kill a Mockingbird.'),
('James','Joyce','Irish modernist author.'),
('J.K.','Rowling','British author of the Harry Potter series.'),
('Toni','Morrison','American novelist, Nobel laureate.'),
('Gabriel','Garcia Marquez','Colombian novelist, magic realism.'),
('George','Orwell','English novelist and essayist.')
ON CONFLICT DO NOTHING;

ALTER TABLE BOOKS
ALTER COLUMN TITLE TYPE VARCHAR(200);

INSERT INTO BOOKS (TITLE, AUTHOR_ID, ISBN, YEAR_PUBLISHED, TOTAL_COPIES, AVAILABLE_COPIES) VALUES
('Things Fall Apart', (SELECT author_id FROM authors WHERE first_name='Chinua' AND last_name='Achebe'), '9780141181', 1958, 5, 5),
('A Grain of Wheat', (SELECT author_id FROM authors WHERE first_name='Ngugi' AND last_name='wa Thiong''o'), '9780007022', 1967, 3, 3),
('Pride and Prejudice', (SELECT author_id FROM authors WHERE first_name='Jane' AND last_name='Austen'), '9780141043', 1813, 4, 4),
('Adventures of Huckleberry Finn', (SELECT author_id FROM authors WHERE first_name='Mark' AND last_name='Twain'), '9780143034', 1884, 2, 2),
('To Kill a Mockingbird', (SELECT author_id FROM authors WHERE first_name='Harper' AND last_name='Lee'), '9780061120084', 1960, 6, 6),
('Ulysses', (SELECT author_id FROM authors WHERE first_name='James' AND last_name='Joyce'), '9780199535675', 1922, 1, 1),
('Harry Potter and the Sorcerer''s Stone', (SELECT author_id FROM authors WHERE first_name='J.K.' AND last_name='Rowling'), '9780747532743', 1997, 8, 8),
('Beloved', (SELECT author_id FROM authors WHERE first_name='Toni' AND last_name='Morrison'), '9781400033416', 1987, 2, 2),
('One Hundred Years of Solitude', (SELECT author_id FROM authors WHERE first_name='Gabriel' AND last_name='Garcia Marquez'), '9780060883287', 1967, 3, 3),
('1984', (SELECT author_id FROM authors WHERE first_name='George' AND last_name='Orwell'), '9780451524935', 1949, 5, 5)
ON CONFLICT DO NOTHING;

INSERT INTO MEMBERS (USER_ID, FULL_NAME, PHONE) VALUES
((SELECT user_id FROM users WHERE username='JANE'),'Jane Sesay', '+23276000001'),
((SELECT user_id FROM users WHERE username='MIKE'),'Michael Samura', '+23276000002'),
((SELECT user_id FROM users WHERE username='CHRISTIAN'),'Christian Lalugba', '+23276000003'),
((SELECT user_id FROM users WHERE username='ALFRED'),'Alfred Manso', '+23276000004'),
((SELECT user_id FROM users WHERE username='ANDY'),'Andy Dyfan', '+23276000005'),
((SELECT user_id FROM users WHERE username='AMAX'),'Amax Shine', '+23276000006'),
((SELECT user_id FROM users WHERE username='SAJOR'),'Sajor Jalloh', '+23276000007'),
((SELECT user_id FROM users WHERE username='ABDUL'),'Abdul Kamara', '+23276000008'),
(NULL,'Guest User1', '+23276100009'),
(NULL,'Guest User2', '+23276100010')
ON CONFLICT DO NOTHING;

DELETE FROM MEMBERS
WHERE USER_ID IS NULL;

INSERT INTO BOOK_CLUBS (CLUB_NAME, DESCRIPTION) VALUES
('Fiction Lovers','Monthly meet to discuss fiction'),
('Research Circle','Library research & thesis support'),
('Sci-Fi Enthusiasts','Discuss sci-fi novels and media')
ON CONFLICT (CLUB_NAME) DO NOTHING;

INSERT INTO BOOK_CLUB_MEMBERS (CLUB_ID, MEMBER_ID, CLUB_ROLE) VALUES
((SELECT club_id FROM book_clubs WHERE club_name='Fiction Lovers'), (SELECT member_id FROM members WHERE full_name='Jane Sesay'), 'member'),
((SELECT club_id FROM book_clubs WHERE club_name='Fiction Lovers'), (SELECT member_id FROM members WHERE full_name='Michael Samura'), 'member'),
((SELECT club_id FROM book_clubs WHERE club_name='Fiction Lovers'), (SELECT member_id FROM members WHERE full_name='Christian Lalugba'), 'president'),
((SELECT club_id FROM book_clubs WHERE club_name='Research Circle'), (SELECT member_id FROM members WHERE full_name='Alfred Manso'), 'member'),
((SELECT club_id FROM book_clubs WHERE club_name='Research Circle'), (SELECT member_id FROM members WHERE full_name='Andy Dyfan'), 'secretary'),
((SELECT club_id FROM book_clubs WHERE club_name='Sci-Fi Enthusiasts'), (SELECT member_id FROM members WHERE full_name='Amax Shine'), 'member'),
((SELECT club_id FROM book_clubs WHERE club_name='Sci-Fi Enthusiasts'), (SELECT member_id FROM members WHERE full_name='Sajor Jalloh'), 'treasurer'),
((SELECT club_id FROM book_clubs WHERE club_name='Fiction Lovers'), (SELECT member_id FROM members WHERE full_name='Abdul Kamara'), 'member')
ON CONFLICT DO NOTHING;

INSERT INTO LOAN (BOOK_ID, MEMBER_ID, DUE_DATE, RETURN_DATE, STATUS) VALUES
((SELECT book_id FROM books WHERE title='Things Fall Apart'), (SELECT member_id FROM members WHERE full_name='Jane Sesay'), CURRENT_DATE + INTERVAL '14 days', CURRENT_DATE + INTERVAL '10 days', 'RETURNED'),

((SELECT book_id FROM books WHERE title='Pride and Prejudice'), (SELECT member_id FROM members WHERE full_name='Michael Samura'), CURRENT_DATE + INTERVAL '7 days', NULL, 'LOANED'),

((SELECT book_id FROM books WHERE title='Harry Potter and the Sorcerer''s Stone'), (SELECT member_id FROM members WHERE full_name='Christian Lalugba'), CURRENT_DATE + INTERVAL '21 days', CURRENT_DATE + INTERVAL '20 days', 'RETURNED'),

((SELECT book_id FROM books WHERE title='1984'), (SELECT member_id FROM members WHERE full_name='Alfred Manso'), CURRENT_DATE + INTERVAL '14 days', NULL, 'OVERDUE'),

((SELECT book_id FROM books WHERE title='One Hundred Years of Solitude'), (SELECT member_id FROM members WHERE full_name='Andy Dyfan'), CURRENT_DATE + INTERVAL '10 days', NULL, 'LOANED'),

((SELECT book_id FROM books WHERE title='To Kill a Mockingbird'), (SELECT member_id FROM members WHERE full_name='Amax Shine'), CURRENT_DATE + INTERVAL '7 days', CURRENT_DATE + INTERVAL '6 days', 'RETURNED'),

((SELECT book_id FROM books WHERE title='Adventures of Huckleberry Finn'), (SELECT member_id FROM members WHERE full_name='Sajor Jalloh'), CURRENT_DATE + INTERVAL '14 days', NULL, 'LOANED'),

((SELECT book_id FROM books WHERE title='Beloved'), (SELECT member_id FROM members WHERE full_name='Abdul Kamara'), CURRENT_DATE + INTERVAL '21 days', CURRENT_DATE + INTERVAL '19 days', 'RETURNED')
ON CONFLICT DO NOTHING;


select * from LOAN;





