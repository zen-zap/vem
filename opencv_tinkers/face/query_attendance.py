import sqlite3
import csv

def export_attendance(date=None):
    with sqlite3.connect('face.db') as conn:
        c = conn.cursor()
        if date:
            c.execute('''
                SELECT users.name, attendance.timestamp
                FROM attendance
                JOIN users ON users.id = attendance.user_id
                WHERE DATE(attendance.timestamp) = ?
                ORDER BY attendance.timestamp
            ''', (date,))
        else:
            c.execute('''
                SELECT users.name, attendance.timestamp
                FROM attendance
                JOIN users ON users.id = attendance.user_id
                ORDER BY attendance.timestamp
            ''')
        rows = c.fetchall()
        with open('attendance_export.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Timestamp'])
            writer.writerows(rows)
    print("Attendance exported to attendance_export.csv")

if __name__ == "__main__":
    # Use YYYY-MM-DD or None for all
    export_attendance(date=None)
