"""
Formularios para gestao de funcionarios.
"""
from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    """Formulario para criacao/edicao de funcionario."""
    
    class Meta:
        model = Employee
        fields = [
            'nome', 'email', 'cpf', 'setor', 'cargo',
            'turno', 'data_admissao', 'data_nascimento',
            'data_demissao', 'matricula', 'centro_de_custo',
            'gestor', 'status'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000000000'}),
            'setor': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'data_admissao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_demissao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'centro_de_custo': forms.TextInput(attrs={'class': 'form-control'}),
            'gestor': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['gestor'].queryset = Employee.objects.filter(
                company=company,
                status='ACTIVE'
            )
    
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            cpf = ''.join(filter(str.isdigit, cpf))
            if cpf and len(cpf) != 11:
                raise forms.ValidationError('CPF deve conter 11 digitos.')
        return cpf


class EmployeeImportForm(forms.Form):
    """Formulario para upload de CSV de funcionarios."""
    
    file = forms.FileField(
        label='Arquivo CSV',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.endswith('.csv'):
                raise forms.ValidationError('O arquivo deve ser um CSV.')
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('O arquivo deve ter no maximo 5MB.')
        return file
