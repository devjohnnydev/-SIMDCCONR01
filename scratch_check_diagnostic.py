import psycopg2
import json

try:
    conn = psycopg2.connect('postgresql://postgres:YPfnUjpIUvylYcYOXWTiwblsUMmBYaSt@metro.proxy.rlwy.net:55676/railway')
    cur = conn.cursor()
    
    val_code = '62a40c37-38d2-41f6-926c-bf945e59e240'
    cur.execute("SELECT diagnostic_data FROM reports_employeediagnostic WHERE validation_code = %s", (val_code,))
    res = cur.fetchone()
    
    if res:
        print(json.dumps(res[0], indent=2, ensure_ascii=False))
    else:
        print('Not found')
except Exception as e:
    print('Error:', e)
