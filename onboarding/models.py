"""
ITIL Ticketing System - Django powered incident, problem, and change management system.

models.py - Core database models for the ticketing system.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext, gettext_lazy as _
from markdown import markdown
from markdown.extensions import Extension
import datetime
import mimetypes
import os
import re
import uuid

User = get_user_model()


class EscapeHtml(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.deregister("html_block")
        md.inlinePatterns.deregister("html")


def get_markdown(text):
    """Process markdown text safely."""
    if not text:
        return ""
    
    # Basic markdown processing for security
    return mark_safe(
        markdown(
            text,
            extensions=[
                EscapeHtml(),
                "markdown.extensions.nl2br",
                "markdown.extensions.fenced_code",
            ],
        )
    )


class Department(models.Model):
    """
    A department represents a business unit handling onboarding processes.
    For example: IT, HR, Finance, Operations, etc.
    """

    title = models.CharField(
        _("Department Name"),
        max_length=100,
    )

    slug = models.SlugField(
        _("Slug"),
        max_length=50,
        unique=True,
        help_text=_(
            "This slug is used when building request IDs. Once set, "
            "try not to change it as it may cause confusion."
        ),
    )

    email_address = models.EmailField(
        _("Department E-Mail Address"),
        blank=True,
        null=True,
        help_text=_(
            "All outgoing e-mails for this department will use this e-mail address."
        ),
    )

    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Brief description of this department's role in onboarding.")
    )

    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_departments",
        blank=True,
        null=True,
        verbose_name=_("Department Manager"),
        help_text=_("Manager responsible for this department's onboarding tasks.")
    )

    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Whether this department is actively handling onboarding requests.")
    )

    auto_assign_to_manager = models.BooleanField(
        _("Auto-assign to Manager"),
        default=False,
        help_text=_("Automatically assign new requests to the department manager.")
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("title",)
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    @property
    def from_address(self):
        """Return formatted email address for this department."""
        if not self.email_address:
            return f"NO DEPARTMENT EMAIL DEFINED <{settings.DEFAULT_FROM_EMAIL}>"
        return f"{self.title} <{self.email_address}>"


def mk_secret():
    return str(uuid.uuid4())


class Ticket(models.Model):
    """
    Core model representing a ticket in the ITIL system.
    Can be an Incident, Problem, or Change Request.
    """

    # Ticket types
    INCIDENT = 'incident'
    PROBLEM = 'problem'
    CHANGE = 'change'
    
    TICKET_TYPE_CHOICES = [
        (INCIDENT, _("Incident")),
        (PROBLEM, _("Problem")),
        (CHANGE, _("Change Request")),
    ]

    # Status choices
    NEW_STATUS = 1
    IN_PROGRESS_STATUS = 2
    WAITING_STATUS = 3
    RESOLVED_STATUS = 4
    CLOSED_STATUS = 5
    CANCELLED_STATUS = 6

    STATUS_CHOICES = [
        (NEW_STATUS, _("New")),
        (IN_PROGRESS_STATUS, _("In Progress")),
        (WAITING_STATUS, _("Waiting for Information")),
        (RESOLVED_STATUS, _("Resolved")),
        (CLOSED_STATUS, _("Closed")),
        (CANCELLED_STATUS, _("Cancelled")),
    ]

    OPEN_STATUSES = [NEW_STATUS, IN_PROGRESS_STATUS, WAITING_STATUS]

    # Priority levels (ITIL standard)
    PRIORITY_CHOICES = [
        (1, _("Critical - Service Down")),
        (2, _("High - Major Impact")),
        (3, _("Medium - Minor Impact")),
        (4, _("Low - Minimal Impact")),
    ]

    # Impact levels
    IMPACT_CHOICES = [
        (1, _("High - Multiple Users/Systems")),
        (2, _("Medium - Single User/System")),
        (3, _("Low - Minor Functionality")),
    ]

    # Basic ticket information
    ticket_type = models.CharField(
        _("Ticket Type"),
        max_length=20,
        choices=TICKET_TYPE_CHOICES,
        default=INCIDENT,
        help_text=_("Type of ticket: Incident, Problem, or Change Request")
    )

    title = models.CharField(
        _("Summary"),
        max_length=200,
        help_text=_("Brief description of the issue or request")
    )

    description = models.TextField(
        _("Description"),
        help_text=_("Detailed description of the issue, problem, or change request")
    )

    category = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name=_("Category"),
        help_text=_("Service category or department affected")
    )

    # ITIL fields
    priority = models.IntegerField(
        _("Priority"),
        choices=PRIORITY_CHOICES,
        default=3,
        help_text=_("Business priority based on urgency and impact")
    )

    impact = models.IntegerField(
        _("Impact"),
        choices=IMPACT_CHOICES,
        default=2,
        help_text=_("Impact level of the issue")
    )

    urgency = models.IntegerField(
        _("Urgency"),
        choices=PRIORITY_CHOICES,
        default=3,
        help_text=_("How quickly this needs to be resolved")
    )

    # Reporter information
    reporter_name = models.CharField(
        _("Reporter Name"),
        max_length=200,
        help_text=_("Name of the person reporting the issue")
    )

    reporter_email = models.EmailField(
        _("Reporter Email"),
        help_text=_("Email address of the reporter")
    )

    reporter_phone = models.CharField(
        _("Reporter Phone"),
        max_length=20,
        blank=True,
        help_text=_("Contact phone number for the reporter")
    )

    # Assignment and tracking
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
        blank=True,
        null=True,
        verbose_name=_("Assigned To"),
        help_text=_("Team member responsible for resolving this ticket")
    )

    created = models.DateTimeField(
        _("Created"),
        auto_now_add=True,
        help_text=_("Date this ticket was created")
    )

    modified = models.DateTimeField(
        _("Modified"),
        auto_now=True,
        help_text=_("Date this ticket was last modified")
    )

    resolved_date = models.DateTimeField(
        _("Resolved Date"),
        blank=True,
        null=True,
        help_text=_("Date this ticket was resolved")
    )

    closed_date = models.DateTimeField(
        _("Closed Date"),
        blank=True,
        null=True,
        help_text=_("Date this ticket was closed")
    )

    status = models.IntegerField(
        _("Status"),
        choices=STATUS_CHOICES,
        default=NEW_STATUS,
    )

    # Additional ticket information
    affected_service = models.CharField(
        _("Affected Service"),
        max_length=200,
        blank=True,
        help_text=_("Service or system affected by this issue")
    )

    resolution = models.TextField(
        _("Resolution"),
        blank=True,
        help_text=_("Description of how this ticket was resolved")
    )

    # Related tickets for ITIL processes
    related_incidents = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='related_to',
        limit_choices_to={'ticket_type': INCIDENT},
        help_text=_("Related incident tickets")
    )

    parent_problem = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='child_incidents',
        limit_choices_to={'ticket_type': PROBLEM},
        help_text=_("Parent problem ticket (for incidents)")
    )

    def __str__(self):
        return f"{self.get_ticket_type_display()} #{self.pk} - {self.title}"

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")

    @property
    def ticket_id(self):
        """User-friendly ticket ID combining category and ID."""
        return f"[{self.category.slug}-{self.id}]"

    @property
    def ticket_for_url(self):
        """URL-friendly ticket ID."""
        return f"{self.category.slug}-{self.id}"

    @property
    def is_overdue(self):
        """Check if ticket is overdue based on priority SLA."""
        if self.status in [self.RESOLVED_STATUS, self.CLOSED_STATUS, self.CANCELLED_STATUS]:
            return False
        
        # Define SLA hours based on priority
        sla_hours = {1: 4, 2: 8, 3: 24, 4: 72}  # Critical: 4hrs, High: 8hrs, Medium: 1day, Low: 3days
        
        sla_delta = timezone.timedelta(hours=sla_hours.get(self.priority, 24))
        return timezone.now() > (self.created + sla_delta)

    @property
    def hours_since_created(self):
        """Hours since ticket was created."""
        delta = timezone.now() - self.created
        return int(delta.total_seconds() / 3600)

    @property
    def priority_css_class(self):
        """Return Bootstrap CSS class for priority level."""
        if self.priority == 1:
            return "danger"
        elif self.priority == 2:
            return "warning"
        elif self.priority == 3:
            return "info"
        else:
            return "secondary"

    @property
    def status_css_class(self):
        """Return Bootstrap CSS class for status."""
        status_classes = {
            self.NEW_STATUS: "primary",
            self.IN_PROGRESS_STATUS: "info",
            self.WAITING_STATUS: "warning",
            self.RESOLVED_STATUS: "success",
            self.CLOSED_STATUS: "secondary",
            self.CANCELLED_STATUS: "danger",
        }
        return status_classes.get(self.status, "secondary")

    @property
    def ticket_type_css_class(self):
        """Return Bootstrap CSS class for ticket type."""
        type_classes = {
            self.INCIDENT: "danger",
            self.PROBLEM: "warning", 
            self.CHANGE: "success"
        }
        return type_classes.get(self.ticket_type, "secondary")

    def get_status_display_with_context(self):
        """Enhanced status display with additional context."""
        status_text = self.get_status_display()
        if self.is_overdue and self.status in self.OPEN_STATUSES:
            status_text += _(" - OVERDUE")
        return status_text

    def save(self, *args, **kwargs):
        if not self.id:
            # New ticket - auto assignment logic
            if not self.assigned_to and self.category.auto_assign_to_manager:
                self.assigned_to = self.category.manager

        # Auto-set resolved/closed dates
        if self.status == self.RESOLVED_STATUS and not self.resolved_date:
            self.resolved_date = timezone.now()
        
        if self.status == self.CLOSED_STATUS and not self.closed_date:
            self.closed_date = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("onboarding:request_detail", args=(self.id,))


# Backward compatibility alias
OnboardingRequest = Ticket


class TicketUpdate(models.Model):
    """
    Updates and comments on tickets.
    Tracks all communications and status changes.
    """

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        verbose_name=_("Ticket"),
        related_name="updates"
    )

    date = models.DateTimeField(
        _("Date"),
        default=timezone.now
    )

    title = models.CharField(
        _("Title"),
        max_length=200,
        blank=True,
        help_text=_("Brief title for this update")
    )

    comment = models.TextField(
        _("Comment"),
        blank=True,
        help_text=_("Detailed progress update or notes")
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("User"),
        help_text=_("User who made this update")
    )

    is_public = models.BooleanField(
        _("Visible to Reporter"),
        default=True,
        help_text=_("Whether this update is visible to the ticket reporter")
    )

    new_status = models.IntegerField(
        _("New Status"),
        choices=Ticket.STATUS_CHOICES,
        blank=True,
        null=True,
        help_text=_("If status was changed, what was it changed to?")
    )

    time_spent = models.DurationField(
        _("Time Spent"),
        blank=True,
        null=True,
        help_text=_("Time spent on this update")
    )

    class Meta:
        ordering = ["date"]
        verbose_name = _("Progress Update")
        verbose_name_plural = _("Progress Updates")

    def __str__(self):
        return f"{self.title or 'Update'} - {self.date.strftime('%Y-%m-%d')}"

    def get_markdown(self):
        return get_markdown(self.comment)

    def save(self, *args, **kwargs):
        # Update the ticket's modified timestamp
        self.ticket.modified = timezone.now()
        self.ticket.save(update_fields=['modified'])
        super().save(*args, **kwargs)


# Backward compatibility alias
ProgressUpdate = TicketUpdate


class OnboardingTemplate(models.Model):
    """
    Templates for different types of onboarding processes.
    """

    name = models.CharField(
        _("Template Name"),
        max_length=100,
        help_text=_("Name of this onboarding template")
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name=_("Department"),
        help_text=_("Department this template applies to")
    )

    position_types = models.CharField(
        _("Position Types"),
        max_length=200,
        blank=True,
        help_text=_("Comma-separated list of position types this template applies to")
    )

    checklist_items = models.JSONField(
        _("Checklist Items"),
        default=list,
        help_text=_("List of standard checklist items for this type of onboarding")
    )

    required_equipment = models.TextField(
        _("Required Equipment"),
        blank=True,
        help_text=_("Standard equipment needed for this position type")
    )

    estimated_duration_days = models.IntegerField(
        _("Estimated Duration (Days)"),
        default=5,
        help_text=_("Typical number of days to complete this onboarding")
    )

    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Whether this template is currently in use")
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["department", "name"]
        verbose_name = _("Onboarding Template")
        verbose_name_plural = _("Onboarding Templates")

    def __str__(self):
        return f"{self.department.title} - {self.name}"


class OnboardingAttachment(models.Model):
    """
    File attachments for onboarding requests and updates.
    """

    progress_update = models.ForeignKey(
        ProgressUpdate,
        on_delete=models.CASCADE,
        verbose_name=_("Progress Update"),
        related_name="attachments"
    )

    file = models.FileField(
        _("File"),
        upload_to="onboarding/attachments/%Y/%m/",
        max_length=1000,
    )

    filename = models.CharField(
        _("Filename"),
        max_length=1000,
        blank=True,
    )

    mime_type = models.CharField(
        _("MIME Type"),
        max_length=255,
        blank=True,
    )

    size = models.IntegerField(
        _("Size"),
        blank=True,
        help_text=_("Size of this file in bytes")
    )

    uploaded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["filename"]
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

    def __str__(self):
        return self.filename or str(self.file)

    def save(self, *args, **kwargs):
        if not self.size and self.file:
            self.size = self.file.size

        if not self.filename and self.file:
            self.filename = self.file.name

        if not self.mime_type and self.filename:
            self.mime_type = (
                mimetypes.guess_type(self.filename, strict=False)[0]
                or "application/octet-stream"
            )

        super().save(*args, **kwargs)


class OnboardingSettings(models.Model):
    """
    User-specific settings for the onboarding system.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="onboarding_settings"
    )

    email_on_request_assign = models.BooleanField(
        _("E-mail me when assigned a request"),
        default=True,
        help_text=_("Receive email notifications when assigned new onboarding requests")
    )

    email_on_request_update = models.BooleanField(
        _("E-mail me on request updates"),
        default=True,
        help_text=_("Receive email notifications when requests I'm assigned to are updated")
    )

    dashboard_show_pending = models.BooleanField(
        _("Show pending requests on dashboard"),
        default=True,
    )

    dashboard_show_overdue = models.BooleanField(
        _("Show overdue requests on dashboard"),
        default=True,
    )

    requests_per_page = models.IntegerField(
        _("Requests per page"),
        default=25,
        choices=[(10, "10"), (25, "25"), (50, "50"), (100, "100")]
    )

    class Meta:
        verbose_name = _("Onboarding Settings")
        verbose_name_plural = _("Onboarding Settings")

    def __str__(self):
        return f"Settings for {self.user.get_full_name() or self.user.username}"


# Signal to create settings for new users
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_onboarding_settings(sender, instance, created, **kwargs):
    if created:
        OnboardingSettings.objects.create(user=instance)
