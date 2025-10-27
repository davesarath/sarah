# Pet Care Management System

A comprehensive web application for managing pet care services, appointments, medical records, and user management with role-based access control.

## 🚀 Features

### User Roles & Permissions
- **Admin**: Complete system management, user oversight, comprehensive reporting
- **Veterinarian**: Medical records management, appointment handling, patient care
- **Pet Owner**: Pet registration, appointment booking, medical history access

### Core Functionality
- **User Management**: Registration, authentication, role-based access control
- **Pet Management**: Add/edit pets with photo uploads, medical history tracking
- **Appointment System**: Book, confirm, complete appointments with conflict detection
- **Medical Records**: Vaccination and medication tracking with vet-owner notifications
- **Profile Management**: Role-specific fields, password updates, account deletion
- **File Upload**: Secure pet image uploads with validation

## 🛠 Technology Stack

### Backend
- **Flask 3.1.2** - Python web framework
- **MySQL** - Relational database with proper relationships
- **Werkzeug 3.1.3** - Password hashing and file uploads
- **Flask-CORS 6.0.1** - Cross-origin resource sharing
- **Python-dotenv 1.1.1** - Environment variable management

### Frontend
- **Bootstrap 5.3.3** - Responsive UI framework
- **Bootstrap Icons** - Icon library
- **Vanilla JavaScript** - Dynamic interactions and AJAX calls
- **Jinja2 3.1.6** - Template engine with role-based layouts

### Database
- **MySQL Connector Python 9.4.0** - Database connectivity
- **Parameterized queries** - SQL injection prevention

## 📁 Project Structure

```
sarah/
├── backend/
│   ├── backend.py          # Main Flask application (1,200+ lines)
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Database configuration
├── database/
│   └── setup.sql          # Complete database schema
├── frontend/
│   ├── layouts/           # Role-based base templates
│   │   ├── admin_base.html
│   │   ├── vet_base.html
│   │   └── owner_base.html
│   ├── dashboard/         # Role-specific dashboards
│   │   ├── admin.html
│   │   ├── vet.html
│   │   └── owner.html
│   ├── appointments/      # Appointment management
│   │   ├── book.html
│   │   ├── list.html
│   │   ├── admin_list.html
│   │   └── calender.html
│   ├── medical/           # Medical records templates
│   │   ├── vaccinations.html
│   │   ├── medications.html
│   │   ├── pet_medical.html
│   │   └── admin_medical.html
│   ├── pets/             # Pet management
│   │   ├── add.html
│   │   ├── edit.html
│   │   └── view.html
│   ├── petcareFrontend/  # Authentication pages
│   │   ├── index.html
│   │   ├── register.html
│   │   └── forgot-password.html
│   └── assets/           # Static resources
│       ├── css/
│       ├── js/
│       └── images/
├── static/uploads/        # File storage
│   └── pets/             # Pet images
└── env/                  # Virtual environment
```

## 🗄 Database Schema

### Core Tables
- **users**: Authentication and role management
- **owners**: Pet owner specific information
- **veterinarians**: Veterinarian profiles and specializations
- **pets**: Pet profiles with medical history
- **appointments**: Scheduling system with status tracking
- **vaccinations**: Vaccination records with due dates
- **medications**: Medication prescriptions and dosages
- **expenses**: Pet care expense tracking

### Key Relationships
- Users → Owners/Veterinarians (1:1)
- Owners → Pets (1:Many)
- Pets → Medical Records (1:Many)
- Appointments link Owners, Pets, and Veterinarians

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip (Python package manager)

### 1. Clone Repository
```bash
git clone <repository-url>
cd sarah
```

### 2. Database Setup
```sql
-- Create database and run schema
mysql -u root -p
CREATE DATABASE petcare;
USE petcare;
source database/setup.sql;
```

### 3. Backend Configuration
```bash
cd backend

# Create virtual environment
python -m venv env
env\Scripts\activate  # Windows
# source env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit .env file:
DB_HOST=127.0.0.1
DB_USER=root
DB_PASS=your_password
DB_NAME=petcare
FLASK_ENV=development
```

### 4. Run Application
```bash
python backend.py
```
Access at `http://localhost:5000`

## 👤 Default Admin Account
- **Email**: admin@petcare.in
- **Password**: test123
- **Role**: Admin

## 🔐 Security Features
- **Password Hashing**: Werkzeug secure password hashing
- **Role-Based Access Control**: Decorator-based route protection
- **Session Management**: Flask session handling
- **SQL Injection Prevention**: Parameterized queries
- **File Upload Validation**: Type and size restrictions (5MB limit)
- **Secure Filename Handling**: Werkzeug secure_filename

## 📊 API Endpoints

### Authentication
- `POST /register` - User registration with role-specific data
- `POST /login` - User authentication
- `GET /logout` - Session termination

### User Management (Admin)
- `GET /manageusers` - List all users
- `POST /manage_add_user` - Add new user
- `POST /manage_edit_user` - Update user information
- `DELETE /manage_delete_user` - Soft delete user

### Pet Management
- `GET /managepets` - List pets (role-filtered)
- `POST /manage_add_pet` - Add new pet with image upload
- `POST /manage_edit_pet` - Update pet information
- `DELETE /manage_delete_pet` - Delete pet (Admin only)

### Appointments
- `GET /book_appointment` - Appointment booking form
- `POST /book_appointment` - Create appointment with conflict detection
- `GET /appointments` - View appointments (role-filtered)
- `POST /update_appointment_status` - Update status (Vet only)
- `POST /cancel_appointment` - Cancel appointment (Owner only)

### Medical Records
- `GET /pet_medical/<pet_id>` - Pet medical history
- `POST /add_vaccination` - Add vaccination record
- `POST /add_medication` - Add medication record
- `GET /vaccinations` - View vaccination records (role-filtered)
- `GET /medications` - View medication records (role-filtered)

### Profile Management
- `GET /profile` - User profile
- `POST /update_profile` - Update profile information
- `DELETE /delete_account` - Account deletion

### Utilities
- `GET /autocomplete_users` - User search for forms
- `GET /static/<filename>` - Static file serving

## 🎨 User Interface

### Role-Based Themes
- **Admin**: Professional blue theme with sidebar navigation
- **Veterinarian**: Medical green theme with specialized tools
- **Pet Owner**: User-friendly blue theme with standard navbar

### Responsive Design
- Bootstrap 5.3.3 responsive grid system
- Mobile-friendly navigation
- Adaptive layouts for different screen sizes

## 🔧 Development Features

### Role-Based Filtering
- Veterinarians see only their own medical records
- Pet owners see only their pets' information
- Admins have full system access

### File Upload System
- Pet images stored in `static/uploads/pets/`
- Unique filename generation with timestamps
- File type validation (PNG, JPG, JPEG, GIF)
- 5MB file size limit

### Error Handling
- MySQL error handling with rollback
- Flash message system for user feedback
- Graceful error responses

### Session Management
- User authentication state
- Role-based access control
- Secure session handling

## 📈 Dashboard Features

### Admin Dashboard
- Total users, pets, appointments statistics
- Recent system activities
- User management tools
- Comprehensive reporting

### Veterinarian Dashboard
- Today's appointments
- Recent medical activities
- Patient management tools
- Medical record access

### Pet Owner Dashboard
- Pet overview
- Upcoming reminders (medications, vaccinations)
- Appointment history
- Medical record access

## 🚦 Status Management

### Appointment Statuses
- **Pending**: Newly booked appointments
- **Confirmed**: Vet-confirmed appointments
- **Completed**: Finished appointments
- **Cancelled**: Cancelled appointments

### User Statuses
- **Active**: Normal user account
- **Inactive**: Temporarily disabled
- **Deleted**: Soft-deleted (vchr_status = 'D')

## 🔄 Workflow Examples

### Pet Owner Workflow
1. Register account → Login
2. Add pets with photos
3. Book appointments with veterinarians
4. View medical records and reminders
5. Manage profile and pets

### Veterinarian Workflow
1. Login to dashboard
2. View today's appointments
3. Access pet medical records
4. Add vaccinations/medications
5. Update appointment statuses

### Admin Workflow
1. Monitor system statistics
2. Manage users and roles
3. Oversee all pets and appointments
4. Generate reports and analytics

## 🛡️ Data Validation

### Frontend Validation
- Form field requirements
- File type and size validation
- Date and time validation

### Backend Validation
- Input sanitization
- Database constraint enforcement
- Business logic validation

## 📝 Development Notes

### Code Organization
- Modular route handlers
- Role-based decorators
- Consistent error handling
- Clean separation of concerns

### Database Design
- Normalized schema design
- Foreign key relationships
- Proper indexing for performance
- Soft delete implementation

### Future Enhancements
- Real-time notifications system
- Email notification integration
- Advanced reporting features
- Mobile application support
- Payment integration for services

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection**: Check MySQL service and credentials
2. **File Uploads**: Verify upload directory permissions
3. **Session Issues**: Clear browser cookies and restart server
4. **Template Errors**: Check template file paths and syntax

### Debug Mode
- Set `FLASK_ENV=development` in .env
- Enable debug mode: `app.run(debug=True)`
- Check console logs for detailed error messages

## 📄 License
This project is developed for educational and demonstration purposes.

## 🤝 Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

**Note**: This is a comprehensive pet care management system with production-ready features including security, role-based access, file uploads, and complete CRUD operations for all entities.