"""Views para Gestão de Documentos."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse

from .models import Document, DocumentVersion
from audit.models import AuditLog


def _get_company(request):
    if request.user.is_admin_master:
        company_pk = request.GET.get('company')
        if company_pk:
            from companies.models import Company
            return get_object_or_404(Company, pk=company_pk)
    return request.user.company


@login_required
def document_list(request):
    """Lista de documentos com filtros por tipo."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    docs = Document.objects.filter(company=company)

    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    if tipo:
        docs = docs.filter(tipo=tipo)
    if status:
        docs = docs.filter(status=status)

    # Tabs por tipo
    type_counts = {}
    for t_code, t_label in Document.TYPE_CHOICES:
        count = Document.objects.filter(company=company, tipo=t_code).count()
        if count > 0:
            type_counts[t_code] = {'label': t_label, 'count': count}

    return render(request, 'documents/document_list.html', {
        'documents': docs,
        'type_counts': type_counts,
        'type_choices': Document.TYPE_CHOICES,
        'filter_tipo': tipo,
        'filter_status': status,
        'company': company,
    })


@login_required
def document_upload(request):
    """Upload de novo documento."""
    company = _get_company(request)
    if not company:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        doc = Document.objects.create(
            company=company,
            tipo=request.POST.get('tipo', 'LAUDO'),
            titulo=request.POST.get('titulo', '').strip(),
            descricao=request.POST.get('descricao', '').strip(),
            arquivo=request.FILES.get('arquivo'),
            status=request.POST.get('status', 'DRAFT'),
            data_emissao=request.POST.get('data_emissao') or None,
            validade=request.POST.get('validade') or None,
            created_by=request.user,
        )
        # Normas aplicadas
        normas = request.POST.getlist('normas')
        if normas:
            doc.normas_aplicadas = normas
            doc.save(update_fields=['normas_aplicadas'])

        # Primeira versão
        DocumentVersion.objects.create(
            document=doc,
            versao=1,
            arquivo=doc.arquivo,
            alterado_por=request.user,
            motivo_alteracao='Versão inicial'
        )

        AuditLog.log(
            user=request.user, action='CREATE',
            description=f'Documento criado: {doc.titulo}',
            obj=doc, company=company, request=request
        )
        messages.success(request, 'Documento enviado com sucesso!')
        return redirect('documents:list')

    return render(request, 'documents/document_upload.html', {
        'type_choices': Document.TYPE_CHOICES,
        'company': company,
    })


@login_required
def document_detail(request, pk):
    """Detalhes do documento com timeline de versões."""
    company = _get_company(request)
    doc = get_object_or_404(Document, pk=pk, company=company)
    versions = doc.version_history.all()

    return render(request, 'documents/document_detail.html', {
        'doc': doc,
        'versions': versions,
        'company': company,
    })


@login_required
def document_new_version(request, pk):
    """Cria nova versão de um documento existente."""
    company = _get_company(request)
    doc = get_object_or_404(Document, pk=pk, company=company)

    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')
        motivo = request.POST.get('motivo', 'Atualização')

        new_doc = doc.create_new_version(request.user, arquivo=arquivo)

        DocumentVersion.objects.filter(
            document=new_doc, versao=new_doc.versao
        ).update(motivo_alteracao=motivo)

        AuditLog.log(
            user=request.user, action='UPDATE',
            description=f'Nova versão do documento: {new_doc.titulo} (v{new_doc.versao})',
            obj=new_doc, company=company, request=request
        )
        messages.success(request, f'Versão {new_doc.versao} criada!')
        return redirect('documents:detail', pk=new_doc.pk)

    return render(request, 'documents/document_new_version.html', {
        'doc': doc,
        'company': company,
    })


@login_required
def document_download(request, pk):
    """Download do arquivo do documento."""
    from django.http import HttpResponse
    company = _get_company(request)
    doc = get_object_or_404(Document, pk=pk, company=company)
    
    if doc.arquivo_db:
        response = HttpResponse(doc.arquivo_db, content_type=doc.arquivo_mime or 'application/pdf')
        filename = doc.arquivo_nome or f"documento_{doc.pk}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    elif doc.arquivo:
        return FileResponse(doc.arquivo, as_attachment=True)
        
    messages.error(request, 'Documento sem arquivo.')
    return redirect('documents:detail', pk=pk)
