from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Department,
    Ticket,
    TicketUpdate,
    OnboardingTemplate,
    OnboardingAttachment,
    OnboardingSettings,
    # Backward compatibility
    OnboardingRequest,
    ProgressUpdate,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'manager', 'is_active', 'auto_assign_to_manager')
    list_filter = ('is_active', 'auto_assign_to_manager')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('manager',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_id', 'ticket_type', 'title', 'category', 
        'assigned_to', 'status', 'priority', 'created', 'is_overdue'
    )
    list_filter = (
        'ticket_type', 'status', 'priority', 'impact', 'category', 'created'
    )
    search_fields = (
        'reporter_name', 'reporter_email', 'title', 'description', 'affected_service'
    )
    date_hierarchy = 'created'
    raw_id_fields = ('assigned_to',)
    readonly_fields = ('created', 'modified', 'ticket_id', 'is_overdue', 'hours_since_created')
    
    fieldsets = (
        (_('Ticket Information'), {
            'fields': (
                'ticket_type', 'title', 'description', 'category'
            )
        }),
        (_('Priority & Impact'), {
            'fields': (
                'priority', 'impact', 'urgency', 'affected_service'
            )
        }),
        (_('Reporter Information'), {
            'fields': (
                'reporter_name', 'reporter_email', 'reporter_phone'
            )
        }),
        (_('Assignment & Resolution'), {
            'fields': (
                'assigned_to', 'status', 'resolution'
            )
        }),
        (_('Related Tickets'), {
            'fields': (
                'parent_problem', 'related_incidents'
            ),
            'classes': ('collapse',)
        }),
        (_('System Information'), {
            'fields': (
                'ticket_id', 'created', 'modified', 'is_overdue', 
                'hours_since_created', 'resolved_date', 'closed_date'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """Return different fieldsets for add vs change forms."""
        if not obj:  # Adding new ticket
            return (
                (_('Ticket Information'), {
                    'fields': (
                        'ticket_type', 'title', 'description', 'category'
                    )
                }),
                (_('Priority & Impact'), {
                    'fields': (
                        'priority', 'impact', 'urgency', 'affected_service'
                    )
                }),
                (_('Reporter Information'), {
                    'fields': (
                        'reporter_name', 'reporter_email', 'reporter_phone'
                    )
                }),
                (_('Assignment & Resolution'), {
                    'fields': (
                        'assigned_to', 'status', 'resolution'
                    )
                }),
                (_('Related Tickets'), {
                    'fields': (
                        'parent_problem', 'related_incidents'
                    ),
                    'classes': ('collapse',)
                }),
            )
        return super().get_fieldsets(request, obj)

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = _('Overdue')

    def get_form(self, request, obj=None, **kwargs):
        """Customize form for ticket creation."""
        form = super().get_form(request, obj, **kwargs)
        
        # Set default values for new tickets
        if not obj:
            form.base_fields['status'].initial = Ticket.NEW_STATUS
            form.base_fields['priority'].initial = 3  # Medium priority
            form.base_fields['impact'].initial = 2    # Medium impact
            form.base_fields['urgency'].initial = 3   # Medium urgency
            form.base_fields['ticket_type'].initial = Ticket.INCIDENT
            
            # Pre-fill reporter information from current user
            form.base_fields['reporter_name'].initial = (
                request.user.get_full_name() or request.user.username or 'System Admin'
            )
            form.base_fields['reporter_email'].initial = (
                request.user.email or f"{request.user.username}@company.com"
            )
        
        return form

    def save_model(self, request, obj, form, change):
        """Custom save logic for tickets."""
        if not change:  # New ticket
            # Set reporter info from current user if not provided
            if not obj.reporter_name:
                obj.reporter_name = request.user.get_full_name() or request.user.username or 'System Admin'
            if not obj.reporter_email:
                obj.reporter_email = request.user.email or f"{request.user.username}@company.com"
        
        super().save_model(request, obj, form, change)


class OnboardingAttachmentInline(admin.TabularInline):
    model = OnboardingAttachment
    extra = 0
    readonly_fields = ('size', 'mime_type', 'uploaded_date')


@admin.register(TicketUpdate)
class TicketUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'ticket', 'title', 'user', 'date', 'is_public', 'new_status'
    )
    list_filter = ('is_public', 'new_status', 'date')
    search_fields = ('title', 'comment', 'ticket__title', 'ticket__reporter_name')
    date_hierarchy = 'date'
    raw_id_fields = ('ticket', 'user')
    inlines = [OnboardingAttachmentInline]


# Create backward compatibility alias
class OnboardingRequestAdmin(TicketAdmin):
    pass

class ProgressUpdateAdmin(TicketUpdateAdmin):
    pass


@admin.register(OnboardingTemplate)
class OnboardingTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'department', 'position_types', 
        'estimated_duration_days', 'is_active'
    )
    list_filter = ('department', 'is_active')
    search_fields = ('name', 'position_types', 'required_equipment')


@admin.register(OnboardingSettings)
class OnboardingSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'email_on_request_assign', 'email_on_request_update',
        'requests_per_page'
    )
    list_filter = ('email_on_request_assign', 'email_on_request_update')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)
