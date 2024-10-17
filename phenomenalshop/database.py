import sqlite3

def create_db():
    conn = sqlite3.connect('bot_database.db')  # Creates a new database file
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_wallets (
    user_id INTEGER PRIMARY KEY,
    eth_wallet_address TEXT,
    ltc_wallet_address TEXT,
    sol_wallet_address TEXT,
    eth_balance REAL DEFAULT 0.0,
    ltc_balance REAL DEFAULT 0.0,
    sol_balance REAL DEFAULT 0.0
);
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_db()
