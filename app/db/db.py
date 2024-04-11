import psycopg2
import secrets
from app.config import PostgresConfig


class Database:
    def __init__(self,
                 logger):
        self.logger = logger

        self.conn = psycopg2.connect(host=PostgresConfig.HOST, port=PostgresConfig.PORT,
                                     user=PostgresConfig.SECRETS['user'],
                                     database=PostgresConfig.DATABASE, password=PostgresConfig.SECRETS['pass'])

    def init_table(self):
        cursor = self.conn.cursor()
        create_tables_commands = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                group_id INTEGER,
                card_number BIGINT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS groups (
                group_id SERIAL PRIMARY KEY,
                admin_id INT REFERENCES users(user_id),
                join_code VARCHAR(16) UNIQUE NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS spending (
                spending_id SERIAL PRIMARY KEY,
                group_id INT REFERENCES Groups(group_id),
                user_id INT REFERENCES Users(user_id),
                amount DECIMAL NOT NULL,
                description TEXT,
                spending_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payer_id INT 
            )
            """
        ]
        # Execute each table creation command
        for command in create_tables_commands:
            self.logger.info(f"Executing command: {command}")
            cursor.execute(command)
            self.conn.commit()
        self.logger.info("Tables created")

        cursor.close()

    def update_user_group(self, telegram_id, group_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute('UPDATE users SET group_id = %s WHERE telegram_id = %s;', (group_id, telegram_id))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating user group: {e}")
            self.conn.rollback()

    def update_card_number(self, telegram_id, card_number):
        cursor = self.conn.cursor()
        try:
            cursor.execute('UPDATE users SET card_number = %s WHERE telegram_id = %s;', (card_number, telegram_id))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating card number: {e}")
            self.conn.rollback()

    def register_user(self, telegram_id, username, card_number):
        self.logger.info(f"Registering user {telegram_id} with username {username}")
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO users (telegram_id, username, card_number) VALUES (%s, %s, %s) ON CONFLICT (telegram_id) DO NOTHING;''',
                (telegram_id, username, card_number))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Error registering user: {e}")
            self.conn.rollback()

    def create_group(self, admin_telegram_id, username):
        self.logger.info(f"Creating group for user {admin_telegram_id} with username {username}")
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Users (telegram_id, username) VALUES (%s, %s) ON CONFLICT (telegram_id) DO NOTHING;",
                (admin_telegram_id, username))
            cursor.execute("SELECT user_id FROM Users WHERE telegram_id = %s;", (admin_telegram_id,))
            admin_id = cursor.fetchone()[0]
            join_code = secrets.token_urlsafe(8)
            cursor.execute(
                "INSERT INTO Groups (admin_id, join_code) VALUES (%s, %s) RETURNING group_id;",
                (admin_id, join_code))
            group_id = cursor.fetchone()[0]
            # self.update_user_group(admin_id, group_id)
            self.conn.commit()
            return join_code, group_id
        except Exception as e:
            self.logger.error(f"Error adding group: {e}")
            self.conn.rollback()
            return None

    def join_group(self, telegram_id, username, join_code):
        self.logger.info(f"Joining group for user {telegram_id} with username {username}")
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT group_id FROM Groups WHERE join_code = %s;", (join_code,))

            result = cursor.fetchone()
            if not result:
                return False  # No such group

            self.update_user_group(telegram_id, result[0])
        except Exception as e:
            self.conn.rollback()  # Rollback in case of an error
            print(f"Error joining group: {e}")  # Log or handle the error as needed
            return False

        return True  # Successfully joined group

    def get_users_in_group(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT group_id FROM users WHERE telegram_id = %s;", (telegram_id,))
        group_id = cursor.fetchone()
        if group_id is None:
            return []  # Return an empty list if the group_id is not found
        group_id = group_id[0]  # Unpack the group_id from the tuple

        cursor.execute("SELECT telegram_id, username FROM Users WHERE group_id = %s;", (group_id,))
        users = cursor.fetchall()
        return users

    def get_username(self, user_id):
        self.logger.info(f"Getting username for user {user_id}")
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users WHERE telegram_id = %s;", (user_id,))
        username = cursor.fetchone()
        self.logger.info(f"Username: {username}")
        if username:
            return username[0]
        else:
            return None

    def get_username_t(self, user_id):
        self.logger.info(f"Getting username for user {user_id}")
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users WHERE user_id = %s;", (user_id,))
        username = cursor.fetchone()
        self.logger.info(f"Username: {username}")
        if username:
            return username[0]
        else:
            return None

    def get_group_id(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT group_id FROM users WHERE telegram_id = %s;", (telegram_id,))
        group_id = cursor.fetchone()
        if group_id:
            self.logger.info(f"Group ID: {group_id[0]}")
            return group_id[0]
        else:
            self.logger.error(f"Group not found for user {telegram_id}")
            return None

    def get_user_id(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = %s;", (telegram_id,))
        user_id = cursor.fetchone()
        if user_id:
            self.logger.info(f"User ID: {user_id[0]}")
            return user_id[0]
        else:
            self.logger.error(f"User not found for telegram ID {telegram_id}")
            return None

    def get_telegram_id(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE user_id = %s;", (user_id,))
        telegram_id = cursor.fetchone()
        if telegram_id:
            self.logger.info(f"Telegram ID: {telegram_id[0]}")
            return telegram_id[0]
        else:
            self.logger.error(f"Telegram ID not found for user ID {user_id}")
            return None

    # def add_spending(self, user_id, group_id, amount, description):
    #     cursor = self.conn.cursor()
    #     try:
    #         cursor.execute(
    #             "INSERT INTO spending (group_id, user_id, amount, description) VALUES (%s, %s, %s, %s);",
    #             (group_id, user_id, amount, description))
    #         self.conn.commit()
    #     except Exception as e:
    #         self.logger.error(f"Error adding spending: {e}")
    #         self.conn.rollback()
    #
    # def update_spending(self, spending_id, amount, description):
    #     cursor = self.conn.cursor()
    #     try:
    #         cursor.execute(
    #             "UPDATE spending SET amount = %s, description = %s WHERE spending_id = %s;",
    #             (amount, description, spending_id))
    #         self.conn.commit()
    #     except Exception as e:
    #         self.logger.error(f"Error updating spending: {e}")
    #         self.conn.rollback()

    def upsert_spending(self, user_id, group_id, amount, description, payer_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                    "INSERT INTO spending (group_id, user_id, amount, description, payer_id) VALUES (%s, %s, %s, %s, %s);",
                    (group_id, user_id, amount, description, payer_id))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Error upserting spending: {e}")
            self.conn.rollback()

    def get_debts(self, payer_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT spending_id, user_id, amount, spending_date FROM spending WHERE payer_id = %s;", (payer_id,))
        debts = cursor.fetchall()
        return debts

    def get_my_debts(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT spending_id, amount, spending_date, payer_id FROM spending WHERE user_id = %s;", (user_id,))
        debts = cursor.fetchall()
        return debts

    def get_card_number(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT card_number FROM users WHERE user_id = %s;", (user_id,))
        card_number = cursor.fetchone()
        if card_number:
            return card_number[0]
        else:
            return None

    def get_id(self, spending_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM spending WHERE spending_id = %s;", (spending_id,))
        user_id = cursor.fetchone()
        if user_id:
            return user_id[0]
        else:
            return None

    def clear_debts(self, spending_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM spending WHERE spending_id = %s;", (spending_id,))
        self.conn.commit()