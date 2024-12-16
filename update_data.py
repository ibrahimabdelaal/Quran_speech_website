import sqlite3
import os
import base64

def populate_audio(audio_folder, db_file):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Ensure the audio column exists in the verse table
    #     cursor.execute('''
    #         ALTER TABLE verse ADD COLUMN audio BLOB
    #     ''')
    #     conn.commit()
    except sqlite3.OperationalError:
        # The column already exists
        print("Audio column already exists in the verse table.")

    try:
        # Iterate through all audio files in the folder
        for file_name in os.listdir(audio_folder):
            # Validate the file name format (e.g., 001001.mp3)
            if len(file_name) == 10 and file_name.endswith('.mp3'):
                surah_number = int(file_name[:3])  # First 3 digits for surah number
                verse_number = int(file_name[3:6])  # Next 3 digits for verse number
                file_path = os.path.join(audio_folder, file_name)

                # Read and encode the audio file in base64
                with open(file_path, 'rb') as audio_file:
                    audio_data = base64.b64encode(audio_file.read()).decode('utf-8')

                # Update the verse table with the audio data
                cursor.execute('''
                    UPDATE verse
                    SET audio_file = ?
                    WHERE verse_number = ? AND surah_id = (
                        SELECT id FROM surah WHERE surah_number = ?
                    )
                ''', (audio_data, verse_number, surah_number))

                print(f"Added audio for Surah {surah_number}, Verse {verse_number}")

        # Commit changes
        conn.commit()
        print("Audio files populated successfully!")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the connection
        conn.close()

# Usage Example
audio_folder = "000_versebyverse"  # Replace with the path to your audio files
db_file = "quran.db"  # Replace with your database file name
populate_audio(audio_folder, db_file)
