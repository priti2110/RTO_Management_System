# RTO Management System

A web-based portal to track and manage Return to Office (RTO) status for employees, built with Flask and PostgreSQL.

## Features
- Employee and manager login
- Daily attendance tracking (WFO, WFH, Leave)
- Timesheet submission with hours
- Manager dashboard and Excel export
- Azure-ready deployment

## Tech Stack
- Python Flask
- PostgreSQL
- Azure App Service
- Azure DevOps Pipeline

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure your database in `config.py`
3. Run migrations: `flask db upgrade`
4. Start the app: `python run.py`
