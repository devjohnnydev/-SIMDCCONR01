from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.landing_page, name='home'),
    path('editor/', views.landing_editor, name='editor'),
    path('testimonial/<int:pk>/approve/', views.approve_testimonial, name='approve_testimonial'),
    path('testimonial/<int:pk>/reject/',  views.reject_testimonial,  name='reject_testimonial'),
    path('announcement/create/',          views.create_announcement,  name='create_announcement'),
    path('announcement/<int:pk>/toggle/', views.toggle_announcement,  name='toggle_announcement'),
    path('announcement/<int:pk>/delete/', views.delete_announcement,  name='delete_announcement'),
]
