"""
HR Onboarding System Views

Main views for the onboarding system.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_http_methods

from .models import (
    Department,
    Ticket,
    TicketUpdate,
    OnboardingTemplate,
    OnboardingSettings,
    # Backward compatibility
    OnboardingRequest,
    ProgressUpdate,
)
from .forms import (
    TicketForm,
    TicketProgressForm,
    TicketUpdateForm,
    OnboardingTemplateForm,
    OnboardingSettingsForm,
    DepartmentForm,
    OnboardingSearchForm,
    # Backward compatibility
    OnboardingRequestForm,
    ProgressUpdateForm,
    QuickProgressUpdateForm,
    OnboardingRequestUpdateForm,
)

User = get_user_model()


@login_required
def dashboard(request):
    """Main dashboard view showing key metrics and recent activity."""
    user = request.user
    
    # Get user's assignments (using new Ticket model)
    assigned_tickets = Ticket.objects.filter(assigned_to=user)
    
    # Calculate metrics for ITIL ticketing
    metrics = {
        'total_assigned': assigned_tickets.count(),
        'new_tickets': assigned_tickets.filter(status=Ticket.NEW_STATUS).count(),
        'in_progress': assigned_tickets.filter(status=Ticket.IN_PROGRESS_STATUS).count(),
        'overdue': assigned_tickets.filter(
            created__lt=timezone.now() - timezone.timedelta(hours=24),
            status__in=Ticket.OPEN_STATUSES
        ).count(),
        'resolved_this_week': assigned_tickets.filter(
            status=Ticket.RESOLVED_STATUS,
            resolved_date__gte=timezone.now() - timezone.timedelta(days=7)
        ).count(),
        'incidents': assigned_tickets.filter(ticket_type=Ticket.INCIDENT).count(),
        'problems': assigned_tickets.filter(ticket_type=Ticket.PROBLEM).count(),
        'changes': assigned_tickets.filter(ticket_type=Ticket.CHANGE).count(),
    }
    
    # Recent activity
    recent_tickets = assigned_tickets.order_by('-modified')[:5]
    
    # High priority tickets needing attention
    urgent_tickets = Ticket.objects.filter(
        priority__lte=2,  # Critical and High priority
        status__in=Ticket.OPEN_STATUSES
    ).order_by('priority', 'created')[:10]
    
    # Department statistics (if user is a manager)
    managed_departments = Department.objects.filter(manager=user)
    dept_stats = []
    for dept in managed_departments:
        dept_tickets = Ticket.objects.filter(category=dept)
        dept_stats.append({
            'department': dept,
            'total': dept_tickets.count(),
            'new': dept_tickets.filter(status=Ticket.NEW_STATUS).count(),
            'overdue': dept_tickets.filter(
                created__lt=timezone.now() - timezone.timedelta(hours=24),
                status__in=Ticket.OPEN_STATUSES
            ).count(),
        })
    
    context = {
        'metrics': metrics,
        'recent_tickets': recent_tickets,
        'urgent_tickets': urgent_tickets,
        'dept_stats': dept_stats,
        'user_settings': getattr(user, 'onboarding_settings', None),
    }
    
    return render(request, 'onboarding/dashboard.html', context)


class OnboardingRequestListView(LoginRequiredMixin, ListView):
    """List view for tickets with filtering (legacy URL compatibility)."""
    model = Ticket
    template_name = 'onboarding/request_list.html'
    context_object_name = 'requests'
    paginate_by = 25

    def get_queryset(self):
        queryset = Ticket.objects.select_related(
            'category', 'assigned_to'
        ).order_by('-created')
        
        # Apply search filters
        form = OnboardingSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data['search']:
                search = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(reporter_name__icontains=search) |
                    Q(reporter_email__icontains=search) |
                    Q(affected_service__icontains=search) |
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )
            
            if form.cleaned_data['department']:
                queryset = queryset.filter(category=form.cleaned_data['department'])
            
            if form.cleaned_data['status']:
                queryset = queryset.filter(status=form.cleaned_data['status'])
            
            if form.cleaned_data['priority']:
                queryset = queryset.filter(priority=form.cleaned_data['priority'])
            
            if form.cleaned_data['assigned_to']:
                queryset = queryset.filter(assigned_to=form.cleaned_data['assigned_to'])
            
            if form.cleaned_data['created_from']:
                queryset = queryset.filter(created__gte=form.cleaned_data['created_from'])
            
            if form.cleaned_data['created_to']:
                queryset = queryset.filter(created__lte=form.cleaned_data['created_to'])
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = OnboardingSearchForm(self.request.GET)
        context['total_count'] = self.get_queryset().count()
        return context


class OnboardingRequestDetailView(LoginRequiredMixin, DetailView):
    """Detail view for individual tickets (legacy URL compatibility)."""
    model = Ticket
    template_name = 'onboarding/request_detail.html'
    context_object_name = 'request'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress_updates'] = self.object.updates.order_by('-date')
        context['quick_update_form'] = QuickProgressUpdateForm()
        context['update_form'] = TicketProgressForm()
        context['all_staff_users'] = User.objects.filter(is_staff=True, is_active=True).order_by('first_name', 'last_name')
        return context


class OnboardingRequestCreateView(LoginRequiredMixin, CreateView):
    """Create view for new tickets (legacy URL compatibility)."""
    model = Ticket
    form_class = TicketForm
    template_name = 'onboarding/request_create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('Ticket created successfully.'))
        return super().form_valid(form)


class OnboardingRequestUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for tickets (legacy URL compatibility)."""
    model = Ticket
    form_class = TicketUpdateForm
    template_name = 'onboarding/request_update.html'

    def form_valid(self, form):
        messages.success(self.request, _('Ticket updated successfully.'))
        return super().form_valid(form)


@login_required
@require_http_methods(["POST"])
def add_progress_update(request, pk):
    """Add a progress update to a ticket."""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    form = QuickProgressUpdateForm(request.POST)
    if form.is_valid():
        update = TicketUpdate(
            ticket=ticket,
            title=form.cleaned_data.get('comment', '')[:50],  # Use first 50 chars as title
            comment=form.cleaned_data['comment'],
            user=request.user,
            is_public=form.cleaned_data['is_public'],
        )
        
        if form.cleaned_data['new_status']:
            update.new_status = int(form.cleaned_data['new_status'])
            ticket.status = update.new_status
            ticket.save()
        
        update.save()
        messages.success(request, _('Progress update added successfully.'))
    else:
        messages.error(request, _('Error adding progress update.'))
    
    return redirect('onboarding:request_detail', pk=pk)


@login_required
def assign_request(request, pk):
    """Assign or reassign a ticket."""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        assignee_id = request.POST.get('assigned_to')
        if assignee_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                assignee = User.objects.get(id=assignee_id, is_staff=True)
                old_assignee = ticket.assigned_to
                ticket.assigned_to = assignee
                ticket.save()
                
                # Create progress update
                TicketUpdate.objects.create(
                    ticket=ticket,
                    title="Ticket Reassigned",
                    comment=f"Ticket reassigned from {old_assignee or 'Unassigned'} to {assignee}",
                    user=request.user,
                    is_public=False,
                )
                
                messages.success(request, f'Ticket assigned to {assignee.get_full_name() or assignee.username}')
            except User.DoesNotExist:
                messages.error(request, 'Invalid assignee selected.')
        else:
            messages.error(request, 'Please select an assignee.')
    
    return redirect('onboarding:request_detail', pk=pk)


class OnboardingSettingsView(LoginRequiredMixin, UpdateView):
    """User settings for the onboarding system."""
    model = OnboardingSettings
    form_class = OnboardingSettingsForm
    template_name = 'onboarding/settings.html'
    success_url = reverse_lazy('onboarding:settings')

    def get_object(self):
        obj, created = OnboardingSettings.objects.get_or_create(user=self.request.user)
        return obj

    def form_valid(self, form):
        messages.success(self.request, _('Settings updated successfully.'))
        return super().form_valid(form)


# Department Management Views
class DepartmentListView(LoginRequiredMixin, ListView):
    """List view for departments."""
    model = Department
    template_name = 'onboarding/department_list.html'
    context_object_name = 'departments'


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Create view for departments."""
    model = Department
    form_class = DepartmentForm
    template_name = 'onboarding/department_create.html'
    success_url = reverse_lazy('onboarding:department_list')


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for departments."""
    model = Department
    form_class = DepartmentForm
    template_name = 'onboarding/department_update.html'
    success_url = reverse_lazy('onboarding:department_list')


# Template Management Views
class OnboardingTemplateListView(LoginRequiredMixin, ListView):
    """List view for onboarding templates."""
    model = OnboardingTemplate
    template_name = 'onboarding/template_list.html'
    context_object_name = 'templates'


class OnboardingTemplateCreateView(LoginRequiredMixin, CreateView):
    """Create view for onboarding templates."""
    model = OnboardingTemplate
    form_class = OnboardingTemplateForm
    template_name = 'onboarding/template_create.html'
    success_url = reverse_lazy('onboarding:template_list')


# API Views for AJAX requests
@login_required
def get_department_templates(request, department_id):
    """Get templates for a specific department (AJAX)."""
    templates = OnboardingTemplate.objects.filter(
        department_id=department_id, is_active=True
    ).values('id', 'name', 'checklist_items', 'required_equipment')
    
    return JsonResponse({'templates': list(templates)})


@login_required
def request_stats(request):
    """Get request statistics (AJAX)."""
    user = request.user
    
    stats = {
        'my_assigned': OnboardingRequest.objects.filter(hr_coordinator=user).count(),
        'pending': OnboardingRequest.objects.filter(
            status=OnboardingRequest.PENDING_STATUS
        ).count(),
        'overdue': OnboardingRequest.objects.filter(
            start_date__lt=timezone.now().date(),
            status__in=OnboardingRequest.OPEN_STATUSES
        ).count(),
        'completed_today': OnboardingRequest.objects.filter(
            status=OnboardingRequest.COMPLETED_STATUS,
            completion_date__date=timezone.now().date()
        ).count(),
    }
    
    return JsonResponse(stats)


# =====================================
# MODERN ITIL TICKETING SYSTEM VIEWS
# =====================================

# New Ticket Management Views
class TicketListView(OnboardingRequestListView):
    """List view for tickets (modern ticketing terminology)."""
    template_name = 'onboarding/ticket_list.html'
    context_object_name = 'tickets'


class TicketCreateView(OnboardingRequestCreateView):
    """Create view for tickets (modern ticketing terminology)."""
    form_class = TicketForm
    template_name = 'onboarding/ticket_create.html'


class TicketDetailView(LoginRequiredMixin, DetailView):
    """Detail view for tickets (modern ticketing terminology)."""
    model = Ticket
    template_name = 'onboarding/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress_updates'] = self.object.updates.order_by('-date')
        context['quick_update_form'] = QuickProgressUpdateForm()
        context['update_form'] = TicketProgressForm()
        context['all_staff_users'] = User.objects.filter(is_staff=True, is_active=True).order_by('first_name', 'last_name')
        return context


class TicketUpdateView(OnboardingRequestUpdateView):
    """Update view for tickets (modern ticketing terminology)."""
    form_class = TicketUpdateForm
    template_name = 'onboarding/ticket_update.html'


# ITIL-specific filtered views
class IncidentListView(TicketListView):
    """List view for incidents only."""
    def get_queryset(self):
        return super().get_queryset().filter(ticket_type=Ticket.INCIDENT)


class ProblemListView(TicketListView):
    """List view for problems only."""
    def get_queryset(self):
        return super().get_queryset().filter(ticket_type=Ticket.PROBLEM)


class ChangeListView(TicketListView):
    """List view for change requests only."""
    def get_queryset(self):
        return super().get_queryset().filter(ticket_type=Ticket.CHANGE)


# Service Category Views (formerly Department Views)
class CategoryListView(DepartmentListView):
    """List view for service categories."""
    template_name = 'onboarding/category_list.html'
    context_object_name = 'categories'


class CategoryCreateView(DepartmentCreateView):
    """Create view for service categories."""
    template_name = 'onboarding/category_create.html'


class CategoryUpdateView(DepartmentUpdateView):
    """Update view for service categories."""
    template_name = 'onboarding/category_update.html'


# Knowledge Base Views (formerly Template Views)
class KnowledgeBaseListView(OnboardingTemplateListView):
    """List view for knowledge base articles."""
    template_name = 'onboarding/knowledge_list.html'
    context_object_name = 'articles'


class KnowledgeBaseCreateView(OnboardingTemplateCreateView):
    """Create view for knowledge base articles."""
    template_name = 'onboarding/knowledge_create.html'


# User Settings View (renamed from OnboardingSettingsView)
class UserSettingsView(OnboardingSettingsView):
    """User settings for the ticketing system."""
    template_name = 'onboarding/settings.html'


# New ticket-specific functions
@login_required
def assign_ticket(request, pk):
    """Assign a ticket to a user (modern terminology)."""
    return assign_request(request, pk)


@login_required
def add_ticket_update(request, pk):
    """Add an update to a ticket (modern terminology)."""
    return add_progress_update(request, pk)


@login_required
def close_ticket(request, pk):
    """Close a ticket."""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        ticket.status = Ticket.CLOSED_STATUS
        ticket.closed_date = timezone.now()
        ticket.save()
        
        messages.success(request, _('Ticket closed successfully.'))
        return redirect('onboarding:ticket_detail', pk=pk)
    
    return redirect('onboarding:ticket_detail', pk=pk)


@login_required
def reopen_ticket(request, pk):
    """Reopen a closed ticket."""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        ticket.status = Ticket.IN_PROGRESS_STATUS
        ticket.closed_date = None
        ticket.save()
        
        messages.success(request, _('Ticket reopened successfully.'))
        return redirect('onboarding:ticket_detail', pk=pk)
    
    return redirect('onboarding:ticket_detail', pk=pk)


# New API endpoints for modern ticketing system
@login_required
def get_category_templates(request, category_id):
    """Get templates for a specific service category (AJAX)."""
    return get_department_templates(request, category_id)


@login_required
def ticket_stats(request):
    """Get ticket statistics (AJAX)."""
    user = request.user
    
    stats = {
        'my_assigned': Ticket.objects.filter(assigned_to=user).count(),
        'new_tickets': Ticket.objects.filter(status=Ticket.NEW_STATUS).count(),
        'overdue': Ticket.objects.filter(
            created__lt=timezone.now() - timezone.timedelta(hours=24),
            status__in=Ticket.OPEN_STATUSES
        ).count(),
        'resolved_today': Ticket.objects.filter(
            status=Ticket.RESOLVED_STATUS,
            resolved_date__date=timezone.now().date()
        ).count(),
        'incidents': Ticket.objects.filter(ticket_type=Ticket.INCIDENT).count(),
        'problems': Ticket.objects.filter(ticket_type=Ticket.PROBLEM).count(),
        'changes': Ticket.objects.filter(ticket_type=Ticket.CHANGE).count(),
    }
    
    return JsonResponse(stats)


@login_required
def sla_status(request, ticket_id):
    """Get SLA status for a specific ticket (AJAX)."""
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    
    sla_data = {
        'ticket_id': ticket.id,
        'is_overdue': ticket.is_overdue,
        'hours_since_created': ticket.hours_since_created,
        'priority': ticket.get_priority_display(),
        'priority_level': ticket.priority,
    }
    
    return JsonResponse(sla_data)
