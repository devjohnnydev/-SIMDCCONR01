from django import forms
from .models import LandingConfig, Testimonial, Announcement


class LandingConfigForm(forms.ModelForm):
    class Meta:
        model = LandingConfig
        exclude = ['updated_at']
        widgets = {
            'primary_color':   forms.TextInput(attrs={'type': 'color', 'class': 'color-picker'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'color-picker'}),
            'accent_color':    forms.TextInput(attrs={'type': 'color', 'class': 'color-picker'}),
            'dark_bg_color':   forms.TextInput(attrs={'type': 'color', 'class': 'color-picker'}),
            'hero_badge':      forms.TextInput(attrs={'class': 'form-control'}),
            'hero_title1':     forms.TextInput(attrs={'class': 'form-control'}),
            'hero_title2':     forms.TextInput(attrs={'class': 'form-control'}),
            'hero_highlight':  forms.TextInput(attrs={'class': 'form-control'}),
            'hero_subtitle':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ticker_text':     forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Use | para separar as mensagens do ticker.'}),
            'hero_cta_text':   forms.TextInput(attrs={'class': 'form-control'}),
            'starter_price':   forms.NumberInput(attrs={'class': 'form-control'}),
            'starter_employees': forms.NumberInput(attrs={'class': 'form-control'}),
            'starter_description': forms.TextInput(attrs={'class': 'form-control'}),
            'pro_price':       forms.NumberInput(attrs={'class': 'form-control'}),
            'pro_employees':   forms.NumberInput(attrs={'class': 'form-control'}),
            'pro_description': forms.TextInput(attrs={'class': 'form-control'}),
            'enterprise_description': forms.TextInput(attrs={'class': 'form-control'}),
            'enterprise_contact': forms.EmailInput(attrs={'class': 'form-control'}),
            'cta_title':       forms.TextInput(attrs={'class': 'form-control'}),
            'cta_subtitle':    forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_email':   forms.EmailInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 5511999999999'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class TestimonialApproveForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['is_approved']


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'announcement_type', 'is_active', 'expires_at']
        widgets = {
            'title':    forms.TextInput(attrs={'class': 'form-control'}),
            'content':  forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'announcement_type': forms.Select(attrs={'class': 'form-control'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
