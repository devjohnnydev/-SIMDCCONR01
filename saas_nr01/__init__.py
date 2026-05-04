"""
Inicialização do projeto SIMDCCONR01.
Importa o Celery para que seja registrado no startup do Django.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
