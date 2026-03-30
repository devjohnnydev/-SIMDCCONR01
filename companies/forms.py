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
            'nome_fantasia', 'razao_social', 'cnpj',
            'responsavel_nome', 'responsavel_email', 'telefone',
            'endereco', 'cidade', 'estado', 'cep',
            'logo', 'cor_primaria', 'cor_secundaria'
        ]
        widgets = {
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
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
