import psycopg2

try:
    conn = psycopg2.connect('postgresql://postgres:YPfnUjpIUvylYcYOXWTiwblsUMmBYaSt@metro.proxy.rlwy.net:55676/railway')
    cur = conn.cursor()
    
    val_code = '62a40c37-38d2-41f6-926c-bf945e59e240'
    cur.execute("SELECT assignment_id FROM reports_employeediagnostic WHERE validation_code = %s", (val_code,))
    res = cur.fetchone()
    
    if res:
        a_id = res[0]
        cur.execute("SELECT form_instance_id FROM forms_builder_formassignment WHERE id = %s", (a_id,))
        form_id = cur.fetchone()[0]
        cur.execute("SELECT title FROM forms_builder_forminstance WHERE id = %s", (form_id,))
        title = cur.fetchone()[0]
        print(f'validation_code {val_code} is assignment {a_id} with title {title}')
    else:
        print('Not found')
except Exception as e:
    print('Error:', e)
