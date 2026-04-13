import sqlite3

conn = sqlite3.connect('student_db.db')
cur = conn.cursor()

tables = ['authorized_users', 'academic_records', 'student_courses', 'cgpa_records', 'financial_records']

print("=== Database Population Summary ===\n")
for table in tables:
    cur.execute(f'SELECT COUNT(*) FROM {table}')
    count = cur.fetchone()[0]
    print(f"{table}: {count} records")

conn.close()
