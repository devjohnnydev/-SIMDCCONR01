import psycopg2

try:
    conn = psycopg2.connect('postgresql://postgres:YPfnUjpIUvylYcYOXWTiwblsUMmBYaSt@metro.proxy.rlwy.net:55676/railway')
    cur = conn.cursor()
    
    cur.execute("SELECT id, nome FROM employees_employee WHERE id = 9")
    emps = cur.fetchall()
    print('Employees:', emps)
    
    if emps:
        emp_id = emps[0][0]
        cur.execute("SELECT id, form_instance_id, status FROM forms_builder_formassignment WHERE employee_id = %s", (emp_id,))
        assigns = cur.fetchall()
        for a in assigns:
            a_id = a[0]
            cur.execute("SELECT title FROM forms_builder_forminstance WHERE id = %s", (a[1],))
            title = cur.fetchone()[0]
            print(f'-- Assign: {a_id}, Title: {title}')
            
            cur.execute("SELECT id, question_id, numeric_value, text_value FROM forms_builder_formanswer WHERE assignment_id = %s", (a_id,))
            answers = cur.fetchall()
            for ans in answers:
                cur.execute("SELECT question_type, text FROM forms_builder_formquestion WHERE id = %s", (ans[1],))
                q = cur.fetchone()
                print(f'   Ans ID: {ans[0]}, QType: {q[0]}, Numeric: {ans[2]}, Text: {ans[3]}')
                
    cur.close()
    conn.close()
except Exception as e:
    print('Error:', e)
