from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Ticket, Message
from companies.views import require_company_admin, require_admin_master

@login_required
def ticket_list(request):
    """Lista tickets do usuario (empresa se for admin de empresa, todos se for admin master)."""
    if request.user.is_admin_master:
        tickets = Ticket.objects.all()
    else:
        # Se não for de empresa, talvez seja funcionário, mas vamos restringir por ora
        if not request.user.company:
            return redirect('accounts:dashboard')
        tickets = Ticket.objects.filter(company=request.user.company)
    
    return render(request, 'support/ticket_list.html', {
        'tickets': tickets
    })

@login_required
def ticket_detail(request, pk):
    """Exibe um ticket e permite enviar mensagens."""
    if request.user.is_admin_master:
        ticket = get_object_or_404(Ticket, pk=pk)
    else:
        ticket = get_object_or_404(Ticket, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                ticket=ticket,
                sender=request.user,
                content=content
            )
            # Atualiza o ticket para mostrar nova mensagem no topo da lista
            ticket.save() 
            return redirect('support:ticket_detail', pk=pk)
            
    # Marcar mensagens como lidas
    ticket.messages.exclude(sender=request.user).update(is_read=True)
    
    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'messages': ticket.messages.all()
    })

@login_required
@require_company_admin
def ticket_create(request):
    """Cria um novo ticket de suporte para a empresa."""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        
        if subject and content:
            ticket = Ticket.objects.create(
                company=request.user.company,
                subject=subject
            )
            Message.objects.create(
                ticket=ticket,
                sender=request.user,
                content=content
            )
            return redirect('support:ticket_detail', pk=ticket.pk)
            
    return render(request, 'support/ticket_form.html')
