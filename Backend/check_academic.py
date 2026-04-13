import sqlite3

conn = sqlite3.connect('student_db.db')
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM academic_records')
count = cur.fetchone()[0]
print(f'academic_records count: {count}')

cur.execute('SELECT reg_id, semester, cgpa, credits_completed FROM academic_records LIMIT 3')
print('\nSample records:')
for row in cur.fetchall():
    print(f'  {row}')

conn.close()
