import sqlite3

DATABASE = 'bot_database.db'

def setup_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Create or update user_wallets table with separate columns for each cryptocurrency wallet address
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_wallets (
            user_id INTEGER PRIMARY KEY,
            sol_wallet_address TEXT,
            eth_wallet_address TEXT,
            ltc_wallet_address TEXT
        )
    ''')

    # Create or update user_balances table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_balances (
            user_id INTEGER PRIMARY KEY,
            sol_balance REAL DEFAULT 0,
            eth_balance REAL DEFAULT 0,
            ltc_balance REAL DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == '__main__':
    setup_database()
