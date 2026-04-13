from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import LandingConfig, Testimonial, Announcement
from .forms import LandingConfigForm, AnnouncementForm


def landing_page(request):
    """Página pública da landing page (lê config do banco)."""
    config = LandingConfig.get()
    ticker_items = [s.strip() for s in config.ticker_text.split('|')] if config.ticker_text else []
    testimonials = Testimonial.objects.filter(is_approved=True).order_by('-created_at')[:6]
    announcements = [a for a in Announcement.objects.filter(is_active=True) if a.is_live]
    return render(request, 'landing/page.html', {
        'config': config,
        'ticker_items': ticker_items,
        'testimonials': testimonials,
        'announcements': announcements,
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
            return redirect('landing:editor')
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
    return redirect('landing:editor')


@login_required
@require_POST
def reject_testimonial(request, pk):
    if not request.user.is_admin_master:
        return redirect('accounts:dashboard')
    t = get_object_or_404(Testimonial, pk=pk)
    t.delete()
    messages.info(request, 'Depoimento removido.')
    return redirect('landing:editor')


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
    return redirect('landing:editor')


@login_required
@require_POST
def toggle_announcement(request, pk):
    if not request.user.is_admin_master:
        return redirect('accounts:dashboard')
    ann = get_object_or_404(Announcement, pk=pk)
    ann.is_active = not ann.is_active
    ann.save()
    return redirect('landing:editor')


@login_required
@require_POST
def delete_announcement(request, pk):
    if not request.user.is_admin_master:
        return redirect('accounts:dashboard')
    get_object_or_404(Announcement, pk=pk).delete()
    messages.info(request, 'Aviso removido.')
    return redirect('landing:editor')
