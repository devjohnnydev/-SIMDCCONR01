"""
Formularios para gestao de empresas.
"""
from django import forms
from .models import Company, Announcement


class CompanySettingsForm(forms.ModelForm):
    """Formulario para edicao de configuracoes da empresa."""
    
    class Meta:
        model = Company
        fields = [
            'nome_fantasia', 'razao_social', 'cnpj', 'website_url',
            'responsavel_nome', 'responsavel_email', 'telefone',
            'endereco', 'cidade', 'estado', 'cep',
            'logo', 'cor_primaria', 'cor_secundaria'
        ]
        widgets = {
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'website_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://exemplo.com'}),
            'responsavel_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'responsavel_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'cor_primaria': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'cor_secundaria': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class CompanyAdminForm(forms.ModelForm):
    """Formulario para ADMIN_MASTER gerenciar planos e faturamento da empresa."""
    
    class Meta:
        model = Company
        fields = [
            'plan', 'custom_price_monthly', 'custom_price_yearly',
            'subscription_status', 'status', 'stripe_customer_id',
            'stripe_subscription_id', 'current_period_end'
        ]
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'custom_price_monthly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'custom_price_yearly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'subscription_status': forms.Select(choices=[
                ('active', 'Ativa'),
                ('trialing', 'Trial'),
                ('past_due', 'Atrasada'),
                ('canceled', 'Cancelada'),
                ('inactive', 'Inativa'),
            ], attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'stripe_customer_id': forms.TextInput(attrs={'class': 'form-control'}),
            'stripe_subscription_id': forms.TextInput(attrs={'class': 'form-control'}),
            'current_period_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }


class AnnouncementForm(forms.ModelForm):
    """Formulario para criacao de comunicados."""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
