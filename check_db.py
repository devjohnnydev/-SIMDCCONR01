import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'saas_nr01.settings'
os.environ['DATABASE_URL'] = 'postgresql://postgres:YPfnUjpIUvylYcYOXWTiwblsUMmBYaSt@metro.proxy.rlwy.net:55676/railway'
sys.path.insert(0, '.')
django.setup()
from documents.models import Document
print(f"Has arquivo_db: {hasattr(Document, 'arquivo_db')}")
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='documents_document'")
print([r[0] for r in cursor.fetchall()])
