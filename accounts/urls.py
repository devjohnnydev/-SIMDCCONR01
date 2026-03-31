"""
URLs para autenticacao e dashboards.
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.CompanySignupView.as_view(), name='signup'),
    path('pending-approval/', views.PendingApprovalView.as_view(), name='pending_approval'),
    path('accept-terms/', views.accept_terms, name='accept_terms'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.admin_master_dashboard, name='admin_master_dashboard'),
    path('dashboard/company/', views.company_admin_dashboard, name='company_admin_dashboard'),
    path('dashboard/admin/laudos/', views.admin_laudos, name='admin_laudos'),
    path('dashboard/admin/laudos/generate/<int:assignment_id>/', views.generate_laudo_action, name='generate_laudo'),
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    path('profile/update/', views.profile_update, name='profile_update'),
]
