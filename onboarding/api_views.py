"""
HR Onboarding System API Views

REST API views for the onboarding system.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
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
from .serializers import (
    DepartmentSerializer,
    OnboardingRequestListSerializer,
    OnboardingRequestDetailSerializer,
    ProgressUpdateSerializer,
    OnboardingTemplateSerializer,
    OnboardingSettingsSerializer,
)

User = get_user_model()


class DepartmentViewSet(viewsets.ModelViewSet):
    """API viewset for Department management."""
    
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        active_only = self.request.query_params.get('active_only', None)
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('title')


class OnboardingRequestViewSet(viewsets.ModelViewSet):
    """API viewset for OnboardingRequest management."""
    
    queryset = OnboardingRequest.objects.select_related(
        'department', 'hr_coordinator'
    ).prefetch_related('progress_updates')
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OnboardingRequestListSerializer
        return OnboardingRequestDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by department
        department = self.request.query_params.get('department', None)
        if department:
            queryset = queryset.filter(department_id=department)
        
        # Filter by coordinator
        coordinator = self.request.query_params.get('coordinator', None)
        if coordinator:
            queryset = queryset.filter(hr_coordinator_id=coordinator)
        
        # Filter by urgency
        urgency = self.request.query_params.get('urgency', None)
        if urgency:
            queryset = queryset.filter(urgency=urgency)
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(new_hire_name__icontains=search) |
                Q(new_hire_email__icontains=search) |
                Q(position__icontains=search) |
                Q(title__icontains=search)
            )
        
        # Filter by date range
        start_date_from = self.request.query_params.get('start_date_from', None)
        start_date_to = self.request.query_params.get('start_date_to', None)
        if start_date_from:
            queryset = queryset.filter(start_date__gte=start_date_from)
        if start_date_to:
            queryset = queryset.filter(start_date__lte=start_date_to)
        
        # Filter overdue
        overdue_only = self.request.query_params.get('overdue_only', None)
        if overdue_only and overdue_only.lower() == 'true':
            queryset = queryset.filter(
                start_date__lt=timezone.now().date(),
                status__in=OnboardingRequest.OPEN_STATUSES
            )
        
        return queryset.order_by('-created')
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get requests assigned to the current user."""
        requests = self.get_queryset().filter(hr_coordinator=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue requests."""
        requests = self.get_queryset().filter(
            start_date__lt=timezone.now().date(),
            status__in=OnboardingRequest.OPEN_STATUSES
        )
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get requests with upcoming start dates (next 7 days)."""
        end_date = timezone.now().date() + timezone.timedelta(days=7)
        requests = self.get_queryset().filter(
            start_date__gte=timezone.now().date(),
            start_date__lte=end_date,
            status__in=OnboardingRequest.OPEN_STATUSES
        ).order_by('start_date')
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_update(self, request, pk=None):
        """Add a progress update to a request."""
        onboarding_request = self.get_object()
        
        data = request.data.copy()
        data['request'] = onboarding_request.id
        data['user'] = request.user.id
        
        serializer = ProgressUpdateSerializer(data=data)
        if serializer.is_valid():
            update = serializer.save()
            
            # Update request status if provided
            if 'new_status' in data and data['new_status']:
                onboarding_request.status = data['new_status']
                onboarding_request.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign or reassign a request to an HR coordinator."""
        onboarding_request = self.get_object()
        coordinator_id = request.data.get('hr_coordinator')
        
        if coordinator_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                coordinator = User.objects.get(id=coordinator_id, is_staff=True)
                
                old_coordinator = onboarding_request.hr_coordinator
                onboarding_request.hr_coordinator = coordinator
                onboarding_request.save()
                
                # Create progress update
                ProgressUpdate.objects.create(
                    request=onboarding_request,
                    title="Request Reassigned",
                    comment=f"Request reassigned from {old_coordinator or 'Unassigned'} to {coordinator}",
                    user=request.user,
                    is_public=False,
                )
                
                serializer = self.get_serializer(onboarding_request)
                return Response(serializer.data)
                
            except User.DoesNotExist:
                return Response(
                    {'error': 'Invalid coordinator selected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'Coordinator ID required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get request statistics."""
        user = request.user
        total_requests = OnboardingRequest.objects.count()
        
        stats = {
            'total_requests': total_requests,
            'my_assigned': OnboardingRequest.objects.filter(hr_coordinator=user).count(),
            'pending': OnboardingRequest.objects.filter(
                status=OnboardingRequest.PENDING_STATUS
            ).count(),
            'in_progress': OnboardingRequest.objects.filter(
                status=OnboardingRequest.IN_PROGRESS_STATUS
            ).count(),
            'completed': OnboardingRequest.objects.filter(
                status=OnboardingRequest.COMPLETED_STATUS
            ).count(),
            'overdue': OnboardingRequest.objects.filter(
                start_date__lt=timezone.now().date(),
                status__in=OnboardingRequest.OPEN_STATUSES
            ).count(),
            'completed_this_week': OnboardingRequest.objects.filter(
                status=OnboardingRequest.COMPLETED_STATUS,
                completion_date__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
        }
        
        return Response(stats)


class ProgressUpdateViewSet(viewsets.ModelViewSet):
    """API viewset for ProgressUpdate management."""
    
    queryset = ProgressUpdate.objects.select_related('request', 'user')
    serializer_class = ProgressUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by request
        request_id = self.request.query_params.get('request', None)
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        
        # Filter by public/private
        public_only = self.request.query_params.get('public_only', None)
        if public_only and public_only.lower() == 'true':
            queryset = queryset.filter(is_public=True)
        
        return queryset.order_by('-date')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OnboardingTemplateViewSet(viewsets.ModelViewSet):
    """API viewset for OnboardingTemplate management."""
    
    queryset = OnboardingTemplate.objects.select_related('department')
    serializer_class = OnboardingTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by department
        department = self.request.query_params.get('department', None)
        if department:
            queryset = queryset.filter(department_id=department)
        
        # Filter by active status
        active_only = self.request.query_params.get('active_only', None)
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('department__title', 'name')


class OnboardingSettingsViewSet(viewsets.ModelViewSet):
    """API viewset for OnboardingSettings management."""
    
    serializer_class = OnboardingSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return OnboardingSettings.objects.filter(user=self.request.user)
    
    def get_object(self):
        obj, created = OnboardingSettings.objects.get_or_create(
            user=self.request.user
        )
        return obj
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


# =====================================
# MODERN ITIL TICKETING SYSTEM API VIEWS
# =====================================

# Create aliases for modern ticketing terminology
class TicketViewSet(OnboardingRequestViewSet):
    """API viewset for Ticket management (modern ITIL terminology)."""
    pass


class TicketUpdateViewSet(ProgressUpdateViewSet):
    """API viewset for Ticket Updates (modern ITIL terminology)."""
    pass