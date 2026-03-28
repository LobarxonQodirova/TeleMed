# TeleMed - Telemedicine Platform

A production-grade telemedicine platform enabling video consultations, appointment scheduling, e-prescriptions, medical file sharing, and more.

## Architecture

- **Backend:** Django 5 + Django REST Framework + Django Channels
- **Frontend:** React 18 + Redux Toolkit
- **Database:** PostgreSQL 16
- **Cache / Message Broker:** Redis 7
- **Task Queue:** Celery 5
- **Real-time:** WebSocket (Django Channels) + WebRTC (peer-to-peer video)
- **Reverse Proxy:** Nginx
- **Containerization:** Docker + Docker Compose

## Features

- **Video Consultations** -- WebRTC-based peer-to-peer video calls with signaling server
- **Appointment Scheduling** -- Doctors define availability; patients book slots
- **E-Prescriptions** -- Digital prescriptions with medication details and verification codes
- **Medical File Sharing** -- Upload and share medical documents during consultations
- **Doctor Search & Filter** -- Search by specialty, name, rating, and availability
- **Patient Queue** -- Real-time waiting room with position tracking
- **Consultation Notes** -- Doctors create clinical notes during or after consultations
- **Payments** -- Consultation fee management, payment processing, refunds
- **Ratings & Reviews** -- Patients rate doctors after completed consultations
- **Notifications** -- Email and in-app notifications for appointments, consultations, prescriptions

## Project Structure

```
telemed/
  backend/
    config/            # Django settings, ASGI, routing, Celery config
    apps/
      accounts/        # User management, doctor/patient profiles
      consultations/   # Video sessions, consultation notes, WebSocket signaling
      appointments/    # Scheduling, availability, booking
      prescriptions/   # E-prescriptions, prescription items
      payments/        # Payment processing, fees, refunds
      reviews/         # Doctor ratings and reviews
      notifications/   # Email and in-app notifications
      medical_files/   # Medical document management
    utils/             # Shared utilities, pagination, exception handling
  frontend/
    src/
      api/             # API client and service modules
      components/      # Reusable UI components
      pages/           # Page-level components
      store/           # Redux store and slices
      hooks/           # Custom React hooks
      styles/          # Global styles
  nginx/               # Nginx reverse proxy configuration
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd telemed
   ```

2. Create environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Build and start all services:
   ```bash
   docker-compose up --build
   ```

4. Run database migrations:
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

6. Access the application:
   - Frontend: http://localhost
   - Backend API: http://localhost/api/
   - Admin Panel: http://localhost/admin/
   - API Documentation: http://localhost/api/docs/

## API Endpoints

### Authentication
- `POST /api/auth/register/` -- Register a new user
- `POST /api/auth/login/` -- Obtain JWT token pair
- `POST /api/auth/refresh/` -- Refresh access token
- `GET /api/auth/me/` -- Current user profile

### Doctors
- `GET /api/accounts/doctors/` -- List doctors with search and filter
- `GET /api/accounts/doctors/{id}/` -- Doctor detail
- `GET /api/accounts/specialties/` -- List specialties

### Appointments
- `GET /api/appointments/` -- List appointments
- `POST /api/appointments/` -- Book an appointment
- `GET /api/appointments/slots/?doctor={id}&date={date}` -- Available slots
- `POST /api/appointments/{id}/cancel/` -- Cancel appointment

### Consultations
- `GET /api/consultations/` -- List consultations
- `POST /api/consultations/{id}/start/` -- Start a consultation
- `POST /api/consultations/{id}/end/` -- End a consultation
- `GET /api/consultations/{id}/notes/` -- Consultation notes
- `WS /ws/consultation/{id}/` -- WebSocket signaling for video

### Prescriptions
- `GET /api/prescriptions/` -- List prescriptions
- `POST /api/prescriptions/` -- Create a prescription
- `GET /api/prescriptions/{id}/download/` -- Download e-prescription PDF

### Payments
- `GET /api/payments/` -- List payments
- `POST /api/payments/` -- Create a payment
- `POST /api/payments/{id}/refund/` -- Request refund

### Reviews
- `GET /api/reviews/doctors/{id}/` -- Reviews for a doctor
- `POST /api/reviews/` -- Submit a review

### Medical Files
- `POST /api/medical-files/` -- Upload a file
- `POST /api/medical-files/{id}/share/` -- Share file with doctor

## Environment Variables

See `.env.example` for all available configuration options.

## Development

### Running Tests
```bash
docker-compose exec backend python manage.py test
```

### Code Formatting
```bash
# Backend
docker-compose exec backend black .
docker-compose exec backend isort .

# Frontend
docker-compose exec frontend npm run lint
```

## License

MIT License
