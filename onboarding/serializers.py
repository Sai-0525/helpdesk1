"""
HR Onboarding System API Serializers

DRF serializers for API endpoints.
"""

from rest_framework import serializers
from .models import (
    Department,
    OnboardingRequest,
    ProgressUpdate,
    OnboardingTemplate,
    OnboardingSettings,
)


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    
    manager_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'title', 'slug', 'email_address', 'description',
            'manager', 'manager_name', 'is_active', 'auto_assign_to_manager'
        ]
        read_only_fields = ['id']
    
    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.get_full_name() or obj.manager.username
        return None


class ProgressUpdateSerializer(serializers.ModelSerializer):
    """Serializer for ProgressUpdate model."""
    
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProgressUpdate
        fields = [
            'id', 'request', 'date', 'title', 'comment', 'user', 'user_name',
            'is_public', 'new_status', 'time_spent'
        ]
        read_only_fields = ['id', 'date', 'user']
    
    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None


class OnboardingRequestListSerializer(serializers.ModelSerializer):
    """Serializer for OnboardingRequest list view."""
    
    department_name = serializers.CharField(source='department.title', read_only=True)
    coordinator_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    
    class Meta:
        model = OnboardingRequest
        fields = [
            'id', 'request_id', 'title', 'new_hire_name', 'new_hire_email',
            'position', 'department', 'department_name', 'hr_coordinator',
            'coordinator_name', 'status', 'status_display', 'urgency',
            'urgency_display', 'start_date', 'created', 'modified',
            'is_overdue', 'days_until_start'
        ]
        read_only_fields = [
            'id', 'request_id', 'created', 'modified', 'is_overdue', 'days_until_start'
        ]
    
    def get_coordinator_name(self, obj):
        if obj.hr_coordinator:
            return obj.hr_coordinator.get_full_name() or obj.hr_coordinator.username
        return None


class OnboardingRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer for OnboardingRequest detail view."""
    
    department = DepartmentSerializer(read_only=True)
    coordinator_name = serializers.SerializerMethodField()
    progress_updates = ProgressUpdateSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    
    class Meta:
        model = OnboardingRequest
        fields = [
            'id', 'request_id', 'title', 'department', 'new_hire_name',
            'new_hire_email', 'new_hire_phone', 'position', 'start_date',
            'hiring_manager', 'hr_coordinator', 'coordinator_name', 'status',
            'status_display', 'urgency', 'urgency_display', 'description',
            'notes', 'equipment_needed', 'completed_tasks', 'pending_tasks',
            'completion_date', 'created', 'modified', 'is_overdue',
            'days_until_start', 'progress_updates'
        ]
        read_only_fields = [
            'id', 'request_id', 'created', 'modified', 'is_overdue',
            'days_until_start', 'progress_updates'
        ]
    
    def get_coordinator_name(self, obj):
        if obj.hr_coordinator:
            return obj.hr_coordinator.get_full_name() or obj.hr_coordinator.username
        return None


class OnboardingTemplateSerializer(serializers.ModelSerializer):
    """Serializer for OnboardingTemplate model."""
    
    department_name = serializers.CharField(source='department.title', read_only=True)
    
    class Meta:
        model = OnboardingTemplate
        fields = [
            'id', 'name', 'department', 'department_name', 'position_types',
            'checklist_items', 'required_equipment', 'estimated_duration_days',
            'is_active', 'created', 'modified'
        ]
        read_only_fields = ['id', 'created', 'modified']


class OnboardingSettingsSerializer(serializers.ModelSerializer):
    """Serializer for OnboardingSettings model."""
    
    class Meta:
        model = OnboardingSettings
        fields = [
            'email_on_request_assign', 'email_on_request_update',
            'dashboard_show_pending', 'dashboard_show_overdue',
            'requests_per_page'
        ]
