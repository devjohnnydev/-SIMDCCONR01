"""
Configuracao do Django Admin para formularios.
"""
from django.contrib import admin
from .models import FormTemplate, FormQuestion, FormInstance, FormAssignment, FormAnswer


class FormQuestionInline(admin.TabularInline):
    """Inline para perguntas do template."""
    model = FormQuestion
    extra = 1
    ordering = ['order']


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    """Admin para templates de formulario."""
    
    list_display = ['name', 'category', 'company', 'is_global', 'is_active', 'created_at']
    list_filter = ['category', 'is_global', 'is_active', 'company']
    search_fields = ['name', 'description']
    inlines = [FormQuestionInline]


@admin.register(FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):
    """Admin para perguntas."""
    
    list_display = ['text_short', 'template', 'question_type', 'order', 'is_required']
    list_filter = ['question_type', 'is_required', 'template']
    search_fields = ['text']
    
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Pergunta'


class FormAssignmentInline(admin.TabularInline):
    """Inline para atribuicoes."""
    model = FormAssignment
    extra = 0
    readonly_fields = ['employee', 'status', 'started_at', 'completed_at']
    can_delete = False


@admin.register(FormInstance)
class FormInstanceAdmin(admin.ModelAdmin):
    """Admin para instancias de formulario."""
    
    list_display = ['title', 'template', 'company', 'status', 'start_date', 'end_date', 'is_anonymous']
    list_filter = ['status', 'is_anonymous', 'company', 'template__category']
    search_fields = ['title', 'description']
    inlines = [FormAssignmentInline]
    
    actions = ['publish_forms', 'close_forms']
    
    def publish_forms(self, request, queryset):
        count = 0
        for form in queryset.filter(status='DRAFT'):
            form.publish()
            count += 1
        self.message_user(request, f'{count} formulario(s) publicado(s).')
    publish_forms.short_description = 'Publicar formularios selecionados'
    
    def close_forms(self, request, queryset):
        count = queryset.filter(status='ACTIVE').update(status='CLOSED')
        self.message_user(request, f'{count} formulario(s) encerrado(s).')
    close_forms.short_description = 'Encerrar formularios selecionados'


@admin.register(FormAssignment)
class FormAssignmentAdmin(admin.ModelAdmin):
    """Admin para atribuicoes."""
    
    list_display = ['form_instance', 'employee', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'form_instance__company']
    search_fields = ['employee__nome', 'form_instance__title']


@admin.register(FormAnswer)
class FormAnswerAdmin(admin.ModelAdmin):
    """Admin para respostas."""
    
    list_display = ['assignment', 'question_short', 'get_display_value', 'created_at']
    list_filter = ['question__question_type', 'created_at']
    search_fields = ['text_value']
    
    def question_short(self, obj):
        return obj.question.text[:30] + '...' if len(obj.question.text) > 30 else obj.question.text
    question_short.short_description = 'Pergunta'
