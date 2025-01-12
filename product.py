from datetime import datetime, timedelta, date
import sqlite3
import os
import dropbox

class Product:
    def __init__(self, db_path="production.db"):
        self.db_path = db_path
        print(f"Initializing database at: {self.db_path}") # Debug
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            print("Connected to database.")

            # Create table for daily target
            c.execute('''
            CREATE TABLE IF NOT EXISTS daily_targets (
                date TEXT PRIMARY KEY,
                target_amount INTEGER,
                completed_amount INTEGER DEFAULT 0
            )''')
            print("Created 'daily_targets' table.")

            # Create table for production records
            c.execute('''
            CREATE TABLE IF NOT EXISTS production_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_timestamp TEXT, -- Renamed from "timestamp"
                completion_time INTEGER, -- time in seconds
                product_type TEXT,
                operator_id TEXT
            )''')
            print("Created 'production_records' table.")
        
            conn.commit()
            print("Database initialized successfully.")
        except sqlite3.OperationalError as e:
            print(f"Database error: {e}")
        finally:
            conn.close()

    def set_daily_target(self, target_amount):
        """"Set the target amount for today"""
        today = date.today().isoformat()
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute('''
            INSERT OR REPLACE INTO daily_targets (date, target_amount, completed_amount)
            VALUES (
                ?,
                ?, 
                COALESCE((SELECT completed_amount FROM daily_targets WHERE date = ?), 0)
            )
            ''',(today, target_amount, today))

            conn.commit()
            print(f"Daily target set for {today}: {target_amount}")
        except sqlite3.OperationalError as e:
            print(f"Error setting daily target: {e}")
        finally:
            conn.close()

    def record_completion(self, completion_time, product_type, operator_id):
        """Record a completed product"""
        current_time = datetime.now()
        today = current_time.date().isoformat()
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Add production record
            c.execute('''
            INSERT INTO production_records (record_timestamp, completion_time, product_type, operator_id)
            VALUES (?, ?, ?, ?)
            ''', (current_time.isoformat(), completion_time, product_type, operator_id))

            # Update completed amount for today
            c.execute('''
            INSERT OR REPLACE INTO daily_targets (date, target_amount, completed_amount)
            VALUES (
                ?,
                COALESCE((SELECT target_amount FROM daily_targets WHERE date = ?), 0)
                COALESCE((SELECT completed_amount FROM daily_targets WHERE date = ?), 0) + 1      
            )
            ''', (today, today, today))

            conn.commit()
            print(f"Product completion recorded for today {today}.")
        except sqlite3.OperationalError as e:
            print(f"Error recording product completion: {e}")
        finally:
            conn.close()

    def calculate_average_from_file(self, file_path,):
        try:
            with open(file_path, 'r') as file:
                data = [float(line.strip()) for line in file if line.strip().replace('.','',1).isdigit()]
                if not data:
                   print("[DEBUG] avg.txt is empty or contains no valid numbers.")
                   return 0  # Return 0 if the file is empty
                avg_time =  round(sum(data) / len(data), 2)  # Calculate an
                print(f"[DEBUG] Calculated average time: {avg_time}")
                return avg_time
        except FileNotFoundError:
          print(f"[ERROR] avg.txt file not found: {file_path}")
          return 0
        except ValueError as e:
          print(f"[ERROR] Error processing file: {e}")
          return 0
        
    def upload_avg_to_dropbox(self, dbx, folder_path='/FLEX'):
       """Upload the `avg.txt` file to Dropbox"""
       file_path = "avg.txt"
       try:
           with open(file_path, 'rb') as file:
               dbx.files_upload(
                  file.read(),
                  f"{folder_path}/{os.path.basename(file_path)}",
                  mode=dropbox.files.WriteMode.overwrite
              )
           print(f"Uploaded {file_path} to Dropbox successfully!")
       except Exception as e:
           print(f"Error uploading {file_path} to Dropbox: {e}")


    def get_daily_stats(self, dbx, folder_path='/FLEX'):
        today = date.today().isoformat()
        stats = {}

        try:
            # Calculate average completion time
            avg_completion_time = self.calculate_average_from_file("avg.txt")

            # Connect to the database and fetch stats
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute('SELECT target_amount, completed_amount FROM daily_targets WHERE date = ?', (today,))
            result = c.fetchone()
            target = result[0] if result else 0
            completed = result[1] if result else 0

            stats = {
                'date': today,
                'target': target,
                'completed': completed,
                'remaining': max(0, target - completed),
                'avg_completion_time': self.calculate_average_from_file("avg.txt")
            }
        except Exception as e:
            print(f"Error retrieving daily stats: {e}")
            stats = {
                'date': today,
                'target': 0,
                'completed': 0,
                'remaining': 0,
                'avg_completion_time': 0,
            }
        finally:
            conn.close()

        return stats


