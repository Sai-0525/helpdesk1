"""
ITIL Ticketing System URLs

URL patterns for the incident, problem, and change management system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import (
    DepartmentViewSet,
    TicketViewSet,
    TicketUpdateViewSet,
    OnboardingTemplateViewSet,
    OnboardingSettingsViewSet,
    # Backward compatibility
    OnboardingRequestViewSet,
    ProgressUpdateViewSet,
)

app_name = 'onboarding'

# API Router
router = DefaultRouter()
router.register(r'categories', DepartmentViewSet)  # Departments now represent service categories
router.register(r'tickets', TicketViewSet)
router.register(r'ticket-updates', TicketUpdateViewSet)
router.register(r'templates', OnboardingTemplateViewSet)
router.register(r'settings', OnboardingSettingsViewSet, basename='settings')

# Backward compatibility API routes (using different basenames)
router.register(r'departments', DepartmentViewSet, basename='departments-compat')
router.register(r'requests', OnboardingRequestViewSet, basename='requests-compat')
router.register(r'progress-updates', ProgressUpdateViewSet, basename='progress-updates-compat')

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Ticket Management (Modern ITIL Terminology)
    path('tickets/', views.TicketListView.as_view(), name='ticket_list'),
    path('tickets/create/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/<int:pk>/update/', views.TicketUpdateView.as_view(), name='ticket_update'),
    path('tickets/<int:pk>/assign/', views.assign_ticket, name='assign_ticket'),
    path('tickets/<int:pk>/add-update/', views.add_ticket_update, name='add_ticket_update'),
    path('tickets/<int:pk>/close/', views.close_ticket, name='close_ticket'),
    path('tickets/<int:pk>/reopen/', views.reopen_ticket, name='reopen_ticket'),
    
    # Service Categories (formerly Departments)
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    
    # Knowledge Base (formerly Templates)
    path('knowledge-base/', views.KnowledgeBaseListView.as_view(), name='knowledge_list'),
    path('knowledge-base/create/', views.KnowledgeBaseCreateView.as_view(), name='knowledge_create'),
    
    # User Settings
    path('settings/', views.UserSettingsView.as_view(), name='settings'),
    
    # ITIL-specific endpoints
    path('incidents/', views.IncidentListView.as_view(), name='incident_list'),
    path('problems/', views.ProblemListView.as_view(), name='problem_list'),
    path('changes/', views.ChangeListView.as_view(), name='change_list'),
    
    # Backward Compatibility Routes (for existing links)
    path('requests/', views.OnboardingRequestListView.as_view(), name='request_list'),
    path('requests/create/', views.OnboardingRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/', views.OnboardingRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/update/', views.OnboardingRequestUpdateView.as_view(), name='request_update'),
    path('requests/<int:pk>/assign/', views.assign_request, name='assign_request'),
    path('requests/<int:pk>/add-update/', views.add_progress_update, name='add_progress_update'),
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/update/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('templates/', views.OnboardingTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.OnboardingTemplateCreateView.as_view(), name='template_create'),
    
    # API endpoints
    path('api/category/<int:category_id>/templates/', views.get_category_templates, name='api_category_templates'),
    path('api/ticket-stats/', views.ticket_stats, name='api_ticket_stats'),
    path('api/sla-status/<int:ticket_id>/', views.sla_status, name='api_sla_status'),
    
    # Legacy API endpoints (for backward compatibility)
    path('api/department/<int:department_id>/templates/', views.get_department_templates, name='api_department_templates'),
    path('api/stats/', views.request_stats, name='api_stats'),
    
    # REST API
    path('api/', include(router.urls)),
]
