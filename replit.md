# Inventory Management System

## Project Overview
This is a Flask-based inventory management system imported from GitHub. The application provides a comprehensive solution for managing products, stock allocations, and user roles in a warehouse/production environment.

## Key Features
- **User Authentication**: Login system with role-based access (warehouse/production staff)
- **Inventory Management**: Add, edit, and track products with photos
- **Stock Control**: Stock adjustments, allocations, and movement tracking
- **Approval Workflow**: Production staff can request products, warehouse staff can approve
- **Multi-language Support**: Portuguese interface
- **File Uploads**: Product photo management

## Architecture
- **Backend**: Flask with SQLAlchemy ORM
- **Database**: SQLite for development, PostgreSQL support for production
- **Frontend**: HTML templates with Bootstrap CSS, jQuery for autocomplete
- **Authentication**: Flask-Login with role-based permissions
- **File Handling**: Secure file uploads for product images

## User Roles
- **Almoxarifado (Warehouse)**: Full access to inventory, can approve requests, manage users
- **Produção (Production)**: Can request products, view inventory (limited)

## Setup Status
✅ Dependencies installed (Flask, SQLAlchemy, etc.)
✅ Database configured (SQLite for development)
✅ Application running on port 5000
✅ Workflow configured for development
✅ Deployment configuration set for production (Gunicorn)

## Default Credentials
- **Username**: admin
- **Password**: admin123
- **Role**: Warehouse Administrator

## Current Configuration
- **Development**: Uses SQLite database with debug mode
- **Production**: Configured to use Gunicorn with autoscale deployment
- **Port**: 5000 (required for Replit environment)
- **Host**: 0.0.0.0 (allows external access through Replit proxy)

## Recent Changes
- Fixed Python dependencies installation
- Resolved type safety issue in stock movement logging
- Configured proper hosting settings for Replit environment
- Set up workflow for development server
- Configured deployment settings for production

## User Preferences
- Interface in Portuguese (Brazilian)
- Bootstrap-based responsive design
- Role-based dashboard navigation
- Image upload support for products

## Project Structure
```
src/
├── app.py              # Flask application factory
├── main.py             # Application entry point
├── models.py           # Database models
├── routes.py           # Application routes
├── forms.py            # WTForms definitions
├── utils.py            # Utility functions
├── static/             # CSS, JS, uploads
└── templates/          # HTML templates
```