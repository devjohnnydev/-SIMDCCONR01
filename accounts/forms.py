"""
Formularios para autenticacao e gestao de usuarios.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Formulario de login customizado."""
    
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua senha'
        })
    )


class CompanySignupForm(forms.ModelForm):
    """Formulario de cadastro de empresa com usuario admin."""
    
    admin_email = forms.EmailField(
        label='Email do Administrador',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    admin_first_name = forms.CharField(
        label='Nome',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    admin_last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    admin_password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    admin_password_confirm = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    accept_terms = forms.BooleanField(
        label='Aceito os Termos de Uso e Politica de Privacidade',
        required=True
    )
    
    class Meta:
        model = Company
        fields = [
            'nome_fantasia', 'razao_social', 'cnpj',
            'responsavel_nome', 'responsavel_email', 'telefone',
            'endereco', 'cidade', 'estado', 'cep'
        ]
        widgets = {
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000000000000'}),
            'responsavel_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'responsavel_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '11999999999'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000000'}),
        }
    
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        cnpj = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj) != 14:
            raise forms.ValidationError('CNPJ deve conter 14 digitos.')
        if Company.objects.filter(cnpj=cnpj).exists():
            raise forms.ValidationError('Este CNPJ ja esta cadastrado.')
        return cnpj
    
    def clean_admin_email(self):
        email = self.cleaned_data.get('admin_email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email ja esta em uso.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('admin_password')
        password_confirm = cleaned_data.get('admin_password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('As senhas nao coincidem.')
        
        return cleaned_data
    
    def save(self, commit=True):
        company = super().save(commit=False)
        company.status = 'PENDING'
        
        if commit:
            company.save()
            
            user = User.objects.create_user(
                email=self.cleaned_data['admin_email'],
                password=self.cleaned_data['admin_password'],
                first_name=self.cleaned_data['admin_first_name'],
                last_name=self.cleaned_data['admin_last_name'],
                role='COMPANY_ADMIN',
                company=company,
                terms_accepted=True,
                privacy_accepted=True
            )
            user.accept_terms()
            user.accept_privacy()
        
        return company


class UserProfileForm(forms.ModelForm):
    """Formulario para edicao de perfil do usuario."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': True}),
        }


class TermsAcceptanceForm(forms.Form):
    """Formulario para aceite de termos."""
    
    accept_terms = forms.BooleanField(
        label='Aceito os Termos de Uso',
        required=True
    )
    accept_privacy = forms.BooleanField(
        label='Aceito a Politica de Privacidade',
        required=True
    )
