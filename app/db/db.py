import psycopg2

from app.config import PostgresConfig


class Database:
    def __init__(self,
                 logger):
        self.logger = logger

        self.conn = psycopg2.connect(host=PostgresConfig.HOST, port=PostgresConfig.PORT, user=PostgresConfig.SECRETS['user'],
                                     database=PostgresConfig.DATABASE, password=PostgresConfig.SECRETS['pass'])

    def init_table(self):
        cursor = self.conn.cursor()
        create_tables_commands = [
            """
            CREATE TABLE IF NOT EXISTS groups (
                group_id SERIAL PRIMARY KEY,
                group_name VARCHAR(255) UNIQUE NOT NULL,
                telegram_id BIGINT UNIQUE NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                group_id INTEGER,
                FOREIGN KEY (group_id) REFERENCES groups (group_id)
    );
            """,
            """
            CREATE TABLE IF NOT EXISTS costs (
                cost_id SERIAL PRIMARY KEY,
                amount DECIMAL NOT NULL,
                description TEXT,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """
        ]
        # Execute each table creation command
        for command in create_tables_commands:
            cursor.execute(command)
        self.logger.info("Tables created")
        self.conn.commit()
        cursor.close()

    def update_user_group(self, telegram_id, group_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute('UPDATE users SET group_id = %s WHERE telegram_id = %s;', (group_id, telegram_id))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating user group: {e}")
            self.conn.rollback()

    def register_user(self, telegram_id, username):
        self.logger.info(f"Registering user {telegram_id} with username {username}")
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO users (telegram_id, username) VALUES (%s, %s) ON CONFLICT (telegram_id) DO NOTHING;''',
                (telegram_id, username))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Error registering user: {e}")
            self.conn.rollback()

    def get_groups(self):
        self.logger.info("Fetching groups")
        cursor = self.conn.cursor()
        try:
            cursor.execute('SELECT group_id, group_name FROM groups;')
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error fetching groups: {e}")
            return None

    def add_group(self, group_name, telegram_id):
        self.logger.info(f"Adding group {group_name} with telegram_id {telegram_id}")
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO groups (group_name, telegram_id) VALUES (%s, %s) RETURNING group_id;',
                           (group_name, telegram_id))
            group_id = cursor.fetchone()[0]
            self.update_user_group(telegram_id, group_id)
            self.conn.commit()
            return group_id
        except Exception as e:
            self.logger.error(f"Error adding group: {e}")
            self.conn.rollback()
            return None

