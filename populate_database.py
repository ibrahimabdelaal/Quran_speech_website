import json
import sqlite3

def populate_database(json_file, db_file):
    try:
        # Load JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Connect to the database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS surah (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                surah_number INTEGER,
                surah_name TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                surah_id INTEGER,
                verse_number INTEGER,
                text TEXT,
                syllables TEXT,
                FOREIGN KEY(surah_id) REFERENCES surah(id)
            )
        ''')

        # Insert data into tables
        for surah_name, verses in data.items():
            try:
                # Get surah number from the first verse entry
                surah_number = verses[0]["surah_number"] if verses else None

                # Insert surah data and print debug information
                print(f"Inserting Surah: {surah_name} (Number: {surah_number})")
                cursor.execute("INSERT INTO surah (surah_number, surah_name) VALUES (?, ?)",
                               (surah_number, surah_name))
                surah_id = cursor.lastrowid

                # Insert each verse in the surah
                for verse in verses:
                    verse_number = verse["verse_number"]
                    text = verse["text"]
                    syllables = verse["syllables"]

                    # Basic validation checks
                    if not isinstance(verse_number, int) or not text or not syllables:
                        print(f"Skipping invalid verse data: {verse}")
                        continue

                    # Insert verse data and print debug information
                    print(f"Inserting Verse: Surah ID = {surah_id}, Number = {verse_number}, Text = '{text}', Syllables = '{syllables}'")
                    cursor.execute("INSERT INTO verse (surah_id, verse_number, text, syllables) VALUES (?, ?, ?, ?)",
                                   (surah_id, verse_number, text, syllables))

            except Exception as e:
                print(f"Error processing surah '{surah_name}': {e}")

        # Commit changes
        conn.commit()
        print("Database populated successfully!")
        conn.close()

    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found.")
    except json.JSONDecodeError:
        print("Error: Invalid JSON data.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")

# Usage example

populate_database("quran_data.json", "quran_database.db")

def view_database(db_file):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Fetch and display a few rows from the surah table
        print("Surah Table:")
        cursor.execute("SELECT * FROM surah LIMIT 5")  # Adjust the LIMIT as needed
        surah_rows = cursor.fetchall()
        for row in surah_rows:
            print(row)

        # Fetch and display a few rows from the verse table
        print("\nVerse Table:")
        cursor.execute("SELECT * FROM verse LIMIT 5")  # Adjust the LIMIT as needed
        verse_rows = cursor.fetchall()
        for row in verse_rows:
            print(row)

        # Close the connection
        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
