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
    
    # Assinaturas
    path('dashboard/admin/laudos/bulk-sign/', views.bulk_sign_laudos, name='bulk_sign_laudos'),
    path('dashboard/admin/laudos/assign-signatory/', views.assign_signatory, name='assign_signatory'),
    path('dashboard/admin/laudos/sign-internal/<int:diagnostic_id>/', views.sign_laudo_internal, name='sign_laudo_internal'),
    path('dashboard/admin/laudos/sign-govbr/<int:diagnostic_id>/', views.sign_laudo_govbr, name='sign_laudo_govbr'),
    
    # Gerenciar Signatários
    path('dashboard/admin/signatarios/', views.manage_signatarios, name='manage_signatarios'),
    path('dashboard/admin/signatarios/<int:pk>/delete/', views.delete_signatario, name='delete_signatario'),
    path('dashboard/admin/signatarios/<int:pk>/edit/', views.edit_signatario, name='edit_signatario'),

    # Relatórios de Departamento (Empresa)
    path('dashboard/company/department-reports/', views.department_reports_list, name='department_reports_list'),
    path('dashboard/company/department-report/<str:setor>/<int:form_id>/', views.view_department_report, name='view_department_report'),
    path('dashboard/company/department-report/generate/', views.generate_department_report_action, name='generate_department_report'),
]

