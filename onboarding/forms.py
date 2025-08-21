"""
ITIL Ticketing System Forms

Forms for creating and managing incident, problem, and change tickets.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
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

User = get_user_model()


class TicketForm(forms.ModelForm):
    """Form for creating new tickets (incidents, problems, changes)."""

    class Meta:
        model = Ticket
        fields = [
            'ticket_type', 'title', 'description', 'category', 'priority', 
            'impact', 'urgency', 'reporter_name', 'reporter_email', 
            'reporter_phone', 'affected_service', 'assigned_to'
        ]
        labels = {
            'ticket_type': _('ITIL Ticket Type'),
            'title': _('Summary'),
            'description': _('Detailed Description'),
            'category': _('Service Category'),
            'priority': _('Business Priority'),
            'impact': _('Impact Level'),
            'urgency': _('Urgency Level'),
            'reporter_name': _('Reporter Full Name'),
            'reporter_email': _('Reporter Email Address'),
            'reporter_phone': _('Reporter Phone Number'),
            'affected_service': _('Affected Service/System'),
            'assigned_to': _('Assigned Technician'),
        }
        widgets = {
            'ticket_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief summary of the issue'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed description of the issue, problem, or change request'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'impact': forms.Select(attrs={'class': 'form-control'}),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'reporter_name': forms.TextInput(attrs={'class': 'form-control'}),
            'reporter_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'reporter_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'affected_service': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service or system affected'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set default reporter info from current user if available
        if user and not self.instance.pk:
            self.fields['reporter_name'].initial = user.get_full_name() or user.username
            self.fields['reporter_email'].initial = user.email
        
        # Filter assigned_to to only show active staff users
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True, is_staff=True).order_by('first_name', 'last_name')
        self.fields['assigned_to'].required = False
        
        # Filter categories to active ones only
        self.fields['category'].queryset = Department.objects.filter(is_active=True).order_by('title')


# Backward compatibility form
class OnboardingRequestForm(TicketForm):
    """Legacy form for backward compatibility."""
    
    class Meta(TicketForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter departments to active ones
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        
        # Filter HR coordinators to staff users
        self.fields['hr_coordinator'].queryset = User.objects.filter(
            is_staff=True, is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['hr_coordinator'].required = False
        
        # Set default values
        if user and user.is_staff:
            self.fields['hr_coordinator'].initial = user
        
        # Generate default title if not provided
        if not self.instance.pk:
            self.fields['title'].help_text = _("Will be auto-generated if left blank")


class TicketProgressForm(forms.ModelForm):
    """Form for adding progress updates to tickets."""

    class Meta:
        model = TicketUpdate
        fields = ['title', 'comment', 'is_public', 'new_status', 'time_spent']
        labels = {
            'title': _('Update Title'),
            'comment': _('Progress Note'),
            'is_public': _('Visible to Reporter'),
            'new_status': _('Change Status To'),
            'time_spent': _('Time Spent'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'new_status': forms.Select(attrs={'class': 'form-control'}),
            'time_spent': forms.TimeInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_status'].required = False
        self.fields['time_spent'].required = False
        self.fields['title'].required = False


# Backward compatibility alias
ProgressUpdateForm = TicketProgressForm


class QuickProgressUpdateForm(forms.Form):
    """Simplified form for quick status updates."""

    comment = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        label=_("Progress Note"),
        help_text=_("Add a quick progress note")
    )
    
    new_status = forms.ChoiceField(
        choices=[('', _('No Status Change'))] + Ticket.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Change Status To"),
        required=False
    )

    is_public = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("Visible to Reporter"),
        initial=True,
        required=False
    )


class TicketUpdateForm(forms.ModelForm):
    """Form for updating existing tickets."""

    class Meta:
        model = Ticket
        fields = [
            'ticket_type', 'title', 'description', 'category', 'priority',
            'impact', 'urgency', 'reporter_name', 'reporter_email', 'reporter_phone',
            'affected_service', 'assigned_to', 'status', 'resolution'
        ]
        labels = {
            'ticket_type': _('ITIL Ticket Type'),
            'title': _('Summary'),
            'description': _('Detailed Description'),
            'category': _('Service Category'),
            'priority': _('Business Priority'),
            'impact': _('Impact Level'),
            'urgency': _('Urgency Level'),
            'reporter_name': _('Reporter Full Name'),
            'reporter_email': _('Reporter Email Address'),
            'reporter_phone': _('Reporter Phone Number'),
            'affected_service': _('Affected Service/System'),
            'assigned_to': _('Assigned Technician'),
            'status': _('Current Status'),
            'resolution': _('Resolution Details'),
        }
        widgets = {
            'ticket_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'impact': forms.Select(attrs={'class': 'form-control'}),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'reporter_name': forms.TextInput(attrs={'class': 'form-control'}),
            'reporter_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'reporter_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'affected_service': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'resolution': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True, is_staff=True).order_by('first_name', 'last_name')
        # Filter categories to active ones only
        self.fields['category'].queryset = Department.objects.filter(is_active=True).order_by('title')


# Backward compatibility form
class OnboardingRequestUpdateForm(TicketUpdateForm):
    """Legacy form for backward compatibility."""
    
    class Meta(TicketUpdateForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Legacy compatibility - no specific field filtering needed


class OnboardingTemplateForm(forms.ModelForm):
    """Form for creating and editing onboarding templates."""

    class Meta:
        model = OnboardingTemplate
        fields = [
            'name', 'department', 'position_types', 'checklist_items',
            'required_equipment', 'estimated_duration_days', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'position_types': forms.TextInput(attrs={'class': 'form-control'}),
            'checklist_items': forms.HiddenInput(),  # Will be handled by JavaScript
            'required_equipment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'estimated_duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OnboardingSettingsForm(forms.ModelForm):
    """Form for user onboarding settings."""

    class Meta:
        model = OnboardingSettings
        exclude = ['user']
        widgets = {
            'email_on_request_assign': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_on_request_update': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dashboard_show_pending': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dashboard_show_overdue': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requests_per_page': forms.Select(attrs={'class': 'form-control'}),
        }


class DepartmentForm(forms.ModelForm):
    """Form for creating and editing departments."""

    class Meta:
        model = Department
        fields = [
            'title', 'slug', 'email_address', 'description', 
            'manager', 'is_active', 'auto_assign_to_manager'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'email_address': forms.EmailInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_assign_to_manager': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = User.objects.filter(
            is_staff=True, is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['manager'].required = False


class OnboardingSearchForm(forms.Form):
    """Search form for filtering onboarding requests."""

    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by title, description, reporter, or service...')
        }),
        label=_("Search"),
        required=False
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Service Category"),
        required=False,
        empty_label=_("All Categories")
    )

    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + Ticket.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Status"),
        required=False
    )

    priority = forms.ChoiceField(
        choices=[('', _('All Priority Levels'))] + Ticket.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Priority"),
        required=False
    )

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Assigned To"),
        required=False,
        empty_label=_("All Assignees")
    )

    created_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_("Created From"),
        required=False
    )

    created_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label=_("Created To"),
        required=False
    )
