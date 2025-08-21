# HR Onboarding System

A streamlined Django-based onboarding system for HR departments to manage new hire onboarding processes efficiently.

## Features

- **Onboarding Request Management**: Create and track onboarding requests for new hires
- **Department-based Organization**: Organize requests by department with dedicated managers
- **Progress Tracking**: Real-time progress updates and status tracking
- **Task Management**: Track completed and pending tasks for each onboarding
- **Email Notifications**: Automated notifications for assignments and updates
- **Dashboard Analytics**: Overview of metrics and upcoming start dates
- **Fast Performance**: Optimized for speed with PostgreSQL and efficient queries

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip

### Installation

1. **Clone and setup the project:**
   ```bash
   cd hr_onboarding_system
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL database:**
   ```bash
   # Create database
   createdb hr_onboarding
   
   # Set environment variables (optional)
   export DB_NAME=hr_onboarding
   export DB_USER=postgres
   export DB_PASSWORD=your_password
   export DB_HOST=localhost
   export DB_PORT=5432
   ```

3. **Initialize the application:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic
   ```

4. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

5. **Access the application:**
   - Application: http://localhost:8000/
   - Admin: http://localhost:8000/admin/

## Usage

### Setting Up Departments

1. Log into the admin interface
2. Go to "Departments" and create your organizational departments
3. Assign managers to each department

### Creating Onboarding Requests

1. Navigate to the main dashboard
2. Click "New Onboarding Request"
3. Fill in the new hire details and requirements
4. Assign to an HR coordinator

### Tracking Progress

1. View all requests from the "All Requests" page
2. Click on any request to see detailed progress
3. Add updates and change status as needed
4. Mark as completed when onboarding is finished

## Key Models

- **Department**: Organizational units handling onboarding
- **OnboardingRequest**: Main entity representing a new hire's onboarding
- **ProgressUpdate**: Timeline of updates and status changes
- **OnboardingTemplate**: Reusable templates for different position types

## Configuration

Key settings can be modified in `hr_onboarding_project/settings.py`:

- Database connection
- Email backend
- File upload limits
- Cache configuration
- Security settings

## Production Deployment

For production deployment:

1. Set `DEBUG = False`
2. Configure a production database
3. Set up Redis for caching
4. Configure email backend (SMTP)
5. Set up static file serving
6. Use a production WSGI server (gunicorn, uWSGI)

## API Access

The system includes REST API endpoints for integration:

- `/api/requests/` - Onboarding requests
- `/api/departments/` - Department management
- `/api/progress-updates/` - Progress tracking

## Performance Features

- Database connection pooling
- Query optimization with select_related/prefetch_related
- Caching for frequently accessed data
- Minimal dependencies for fast startup
- Optimized templates and static files

## Support

For issues or questions, check the Django admin logs or application logs in the `logs/` directory.
