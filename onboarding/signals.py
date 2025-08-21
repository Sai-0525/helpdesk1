"""
ITIL Ticketing System Signals

Signal handlers for the ticketing system.
"""

from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from .models import Ticket, TicketUpdate, OnboardingRequest, ProgressUpdate


# Modern Ticket System Signals
@receiver(pre_save, sender=Ticket)
def generate_ticket_title_if_empty(sender, instance, **kwargs):
    """Auto-generate title if not provided."""
    if not instance.title:
        instance.title = f"{instance.get_ticket_type_display()} - {instance.reporter_name or 'System Generated'}"


@receiver(post_save, sender=Ticket)
def send_ticket_assignment_notification(sender, instance, created, **kwargs):
    """Send email notification when ticket is assigned."""
    if instance.assigned_to and instance.assigned_to.email:
        settings = getattr(instance.assigned_to, 'onboarding_settings', None)
        if settings and settings.email_on_request_assign:
            if created:
                subject = f"New {instance.get_ticket_type_display().lower()} assigned: {instance.ticket_id}"
                message = f"""
                A new {instance.get_ticket_type_display().lower()} has been assigned to you:
                
                Ticket: {instance.title}
                Reporter: {instance.reporter_name}
                Priority: {instance.get_priority_display()}
                Category: {instance.category.title}
                
                Please review the details at your earliest convenience.
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        instance.category.from_address,
                        [instance.assigned_to.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass  # Fail silently to avoid disrupting the save process


@receiver(post_save, sender=TicketUpdate)
def send_ticket_update_notification(sender, instance, created, **kwargs):
    """Send email notification for ticket updates."""
    if created and instance.ticket.assigned_to:
        assignee = instance.ticket.assigned_to
        settings = getattr(assignee, 'onboarding_settings', None)
        
        if settings and settings.email_on_request_update and assignee.email:
            subject = f"Update on {instance.ticket.get_ticket_type_display().lower()}: {instance.ticket.ticket_id}"
            message = f"""
            An update has been posted to {instance.ticket.get_ticket_type_display().lower()} {instance.ticket.ticket_id}:
            
            Ticket: {instance.ticket.title}
            Update: {instance.title or 'Progress Update'}
            {instance.comment[:200]}{'...' if len(instance.comment) > 200 else ''}
            
            Please check the full details in the system.
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    instance.ticket.category.from_address,
                    [assignee.email],
                    fail_silently=True,
                )
            except Exception:
                pass  # Fail silently


# Legacy signals for backward compatibility
@receiver(pre_save, sender=OnboardingRequest)
def generate_title_if_empty(sender, instance, **kwargs):
    """Auto-generate title if not provided (legacy)."""
    if not instance.title:
        instance.title = f"Onboarding for {instance.reporter_name} - {instance.affected_service or 'General'}"


@receiver(post_save, sender=OnboardingRequest)
def send_assignment_notification(sender, instance, created, **kwargs):
    """Send email notification when request is assigned (legacy)."""
    if instance.assigned_to and instance.assigned_to.email:
        settings = getattr(instance.assigned_to, 'onboarding_settings', None)
        if settings and settings.email_on_request_assign:
            if created:
                subject = f"New request assigned: {instance.ticket_id}"
                message = f"""
                A new request has been assigned to you:
                
                Title: {instance.title}
                Reporter: {instance.reporter_name}
                Priority: {instance.get_priority_display()}
                Category: {instance.category.title}
                
                Please review the details at your earliest convenience.
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        instance.category.from_address,
                        [instance.assigned_to.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass


@receiver(post_save, sender=ProgressUpdate)
def send_update_notification(sender, instance, created, **kwargs):
    """Send email notification for progress updates (legacy)."""
    if created and instance.ticket.assigned_to:
        assignee = instance.ticket.assigned_to
        settings = getattr(assignee, 'onboarding_settings', None)
        
        if settings and settings.email_on_request_update and assignee.email:
            subject = f"Update on request: {instance.ticket.ticket_id}"
            message = f"""
            An update has been posted to request {instance.ticket.ticket_id}:
            
            Title: {instance.ticket.title}
            Update: {instance.title or 'Progress Update'}
            {instance.comment[:200]}{'...' if len(instance.comment) > 200 else ''}
            
            Please check the full details in the system.
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    instance.ticket.category.from_address,
                    [assignee.email],
                    fail_silently=True,
                )
            except Exception:
                pass
