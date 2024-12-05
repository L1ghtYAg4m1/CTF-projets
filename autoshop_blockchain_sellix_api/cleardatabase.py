import sqlite3

def clear_database(db_path):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get a list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Iterate through the tables and clear them
        for table_name in tables:
            print(f"Clearing table {table_name[0]}")
            cursor.execute(f"DELETE FROM {table_name[0]}")

        # Commit the changes
        conn.commit()
        print("All tables cleared successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        if conn:
            conn.close()

def main():
    db_path = 'bot_database.db'  # Replace with your actual database path
    clear_database(db_path)

if __name__ == "__main__":
    main()
