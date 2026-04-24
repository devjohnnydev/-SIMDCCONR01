from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import LandingConfig, Testimonial, Announcement
from .forms import LandingConfigForm, AnnouncementForm
from companies.models import Company


def landing_page(request):
    """Página pública da landing page (lê config do banco)."""
    config = LandingConfig.get()
    ticker_items = [s.strip() for s in config.ticker_text.split('|')] if config.ticker_text else []
    testimonials = Testimonial.objects.filter(is_approved=True).order_by('-created_at')[:6]
    announcements = [a for a in Announcement.objects.filter(is_active=True) if a.is_live]
    
    # Busca empresas parceiras (ativas, com logo e com link)
    partner_companies = Company.objects.filter(
        subscription_status='active',
        logo__isnull=False,
        website_url__isnull=False
    ).exclude(logo='').exclude(website_url='').order_by('?') 
    
    return render(request, 'landing/page.html', {
        'config': config,
        'ticker_items': ticker_items,
        'testimonials': testimonials,
        'announcements': announcements,
        'partner_companies': partner_companies,
    })


@login_required
def landing_editor(request):
    """Painel do Admin para editar a landing page."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')

    config = LandingConfig.get()
    announcements = Announcement.objects.all()
    pending_testimonials = Testimonial.objects.filter(is_approved=False)
    approved_testimonials = Testimonial.objects.filter(is_approved=True)

    if request.method == 'POST':
        form = LandingConfigForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Landing page atualizada com sucesso!')
            return redirect('landing:landing_editor')
    else:
        form = LandingConfigForm(instance=config)

    return render(request, 'landing/editor.html', {
        'form': form,
        'config': config,
        'announcements': announcements,
        'pending_testimonials': pending_testimonials,
        'approved_testimonials': approved_testimonials,
        'announcement_form': AnnouncementForm(),
    })


@login_required
@require_POST
def approve_testimonial(request, pk):
    if not request.user.is_admin_master:
        return redirect('accounts:dashboard')
    t = get_object_or_404(Testimonial, pk=pk)
    t.is_approved = True
    t.save()
    messages.success(request, f'Depoimento de {t.author_name} aprovado!')
    return redirect(request.META.get('HTTP_REFERER', 'landing:manage_testimonials'))


@login_required
@require_POST
def reject_testimonial(request, pk):
    if not request.user.is_admin_master:
        return redirect('accounts:dashboard')
    t = get_object_or_404(Testimonial, pk=pk)
    t.delete()
    messages.info(request, 'Depoimento removido.')
    return redirect(request.META.get('HTTP_REFERER', 'landing:manage_testimonials'))


@login_required
def create_announcement(request):
    if not request.user.is_admin_master:
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.created_by = request.user
            ann.save()
            messages.success(request, '📢 Aviso criado com sucesso!')
    return redirect(request.META.get('HTTP_REFERER', 'landing:manage_testimonials'))


@login_required
@require_POST
def toggle_announcement(request, pk):
    if not request.user.is_admin_master:
        return redirect('accounts:dashboard')
    ann = get_object_or_404(Announcement, pk=pk)
    ann.is_active = not ann.is_active
    ann.save()
    return redirect(request.META.get('HTTP_REFERER', 'landing:manage_testimonials'))


@login_required
@require_POST
def delete_announcement(request, pk):
    if not request.user.is_admin_master:
        return redirect('accounts:dashboard')
    get_object_or_404(Announcement, pk=pk).delete()
    messages.info(request, 'Aviso removido.')
    return redirect(request.META.get('HTTP_REFERER', 'landing:manage_testimonials'))
@require_POST
def submit_testimonial(request):
    """Recebe um depoimento enviado publicamente."""
    author_name = request.POST.get('author_name', '').strip()
    author_role = request.POST.get('author_role', '').strip()
    author_company = request.POST.get('author_company', '').strip()
    content = request.POST.get('content', '').strip()
    rating = request.POST.get('rating', 5)

    if not author_name or not content:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Nome e depoimento são obrigatórios.'})
        messages.error(request, 'Nome e depoimento são obrigatórios.')
        return redirect('landing:home')

    Testimonial.objects.create(
        author_name=author_name,
        author_role=author_role,
        author_company=author_company,
        content=content,
        rating=int(rating),
        is_approved=False  # Sempre inativo ate aprovação
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Depoimento enviado com sucesso! Aguarde a moderação.'})
    
    messages.success(request, 'Obrigado pelo seu depoimento! Ele será analisado pela nossa equipe antes de ser publicado.')
    return redirect('landing:home')
@login_required
def manage_testimonials(request):
    """Tela dedicada para o Admin Master gerenciar depoimentos."""
    if not request.user.is_admin_master:
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')
    
    pending = Testimonial.objects.filter(is_approved=False).order_of_arrival = '-created_at'
    approved = Testimonial.objects.filter(is_approved=True).order_of_arrival = '-created_at'
    
    # Correction: .order_by instead of .order_of_arrival (brain fart)
    pending = Testimonial.objects.filter(is_approved=False).order_by('-created_at')
    approved = Testimonial.objects.filter(is_approved=True).order_by('-created_at')

    return render(request, 'landing/testimonials_admin.html', {
        'pending_testimonials': pending,
        'approved_testimonials': approved,
    })
