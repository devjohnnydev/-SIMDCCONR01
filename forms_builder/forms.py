"""
Formularios para o modulo de formularios.
"""
from django import forms
from django.forms import formset_factory
from .models import FormTemplate, FormQuestion, FormInstance


class FormInstanceForm(forms.ModelForm):
    """Formulario para criar/editar instancia de formulario."""
    
    class Meta:
        model = FormInstance
        fields = [
            'title', 'description', 'is_anonymous',
            'start_date', 'end_date',
            'target_sectors', 'target_positions'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }, format='%Y-%m-%dT%H:%M'),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }, format='%Y-%m-%dT%H:%M'),
        }
    
    target_sectors_text = forms.CharField(
        label='Setores Alvo',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Digite os setores separados por virgula (ex: TI, RH, Comercial). Deixe vazio para todos.'
        })
    )
    
    target_positions_text = forms.CharField(
        label='Cargos Alvo',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Digite os cargos separados por virgula. Deixe vazio para todos.'
        })
    )
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        self.company = company
        
        if self.instance.pk:
            if self.instance.target_sectors:
                self.fields['target_sectors_text'].initial = ', '.join(self.instance.target_sectors)
            if self.instance.target_positions:
                self.fields['target_positions_text'].initial = ', '.join(self.instance.target_positions)
    
    def clean(self):
        cleaned_data = super().clean()
        
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('A data de termino deve ser posterior a data de inicio.')
        
        sectors_text = cleaned_data.get('target_sectors_text', '')
        if sectors_text:
            cleaned_data['target_sectors'] = [s.strip() for s in sectors_text.split(',') if s.strip()]
        else:
            cleaned_data['target_sectors'] = []
        
        positions_text = cleaned_data.get('target_positions_text', '')
        if positions_text:
            cleaned_data['target_positions'] = [p.strip() for p in positions_text.split(',') if p.strip()]
        else:
            cleaned_data['target_positions'] = []
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.target_sectors = self.cleaned_data.get('target_sectors', [])
        instance.target_positions = self.cleaned_data.get('target_positions', [])
        if commit:
            instance.save()
        return instance


class FormQuestionForm(forms.ModelForm):
    """Formulario para pergunta."""
    
    class Meta:
        model = FormQuestion
        fields = ['text', 'question_type', 'options', 'order', 'is_required', 'help_text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'help_text': forms.TextInput(attrs={'class': 'form-control'}),
        }


FormQuestionFormSet = formset_factory(FormQuestionForm, extra=1, can_delete=True)
