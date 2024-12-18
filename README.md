# Bursary Management System

A comprehensive web-based platform for managing educational bursary programs, streamlining the process of bursary application, review, and distribution across different wards in Kenya.

## 🌟 Key Features

### Student Portal
- Secure user registration and authentication
- Profile management with academic information
- Browse and apply for available bursary programs
- Document upload functionality (PDF support)
- Real-time application status tracking
- Application history and timeline view

### Ward Administrator Dashboard
- Review and process ward-specific applications
- Track ward budget allocation and utilization
- Generate detailed ward-level reports
- Manage ward-specific bursary programs
- Application status management workflow

### System Administrator Console
- Comprehensive system management
- Create and manage bursary programs
- Ward creation and budget allocation
- User management (Ward admins, students)
- System-wide reporting and analytics
- Budget tracking across all wards

## 💻 Technology Stack

### Backend
- **Framework**: Flask 3.0.0
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF with validation
- **Email**: Flask-Mail
- **File Processing**: Python-docx, reportlab
- **Data Processing**: Pandas, NumPy

### Frontend
- **Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.0.0
- **Design System**: Custom Meta Design System
- **Typography**: Poppins Font Family
- **JavaScript**: jQuery 3.6.0

### Development & Deployment
- **Version Control**: Git
- **Platform**: Render.com
- **Server**: Gunicorn
- **Environment**: Python 3.10.0

## 🚀 Getting Started

### Prerequisites
- Python 3.10.0 or higher
- PostgreSQL database
- SMTP server for email functionality

### Installation

1. Clone the repository:
bash
git clone https://github.com/bizzy604/bursary-app.git

2. Set up virtual environment:
bash
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

3. Install dependencies:
bash
pip install -r requirements.txt

4. Configure environment variables:
Create a `.env` file with:

```env
FLASK_APP=bursary.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://username:password@localhost/bursary_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password
```

5. Initialize database:

```bash
flask db upgrade
```

6. Run the application:

```bash
flask run
```

## 📁 Project Structure
```
bursary-app/
├── app/
│   ├── admin/             # Admin module
│   ├── student/           # Student module
│   ├── ward_admin/        # Ward admin module
│   ├── static/
│   │   ├── styles/        # CSS files
│   │   └── js/           # JavaScript files
│   ├── templates/         # HTML templates
│   └── models.py         # Database models
├── migrations/           # Database migrations
├── requirements.txt      # Project dependencies
├── config.py            # Configuration settings
├── bursary.py          # Application entry point
└── render.yaml         # Deployment configuration
```

## 🔒 Security Features
- Secure password hashing
- CSRF protection
- Secure session management
- Role-based access control
- Secure file upload validation
- HTTPS enforcement in production

## 📊 Reporting Features
- Excel report generation
- PDF document generation
- Statistical analysis
- Budget tracking
- Application status reports
- Ward-wise performance metrics

## 🌐 Deployment
The application is configured for deployment on Render.com with:
- Automatic deployment pipeline
- Production-grade Gunicorn server
- Database backup and recovery
- SSL/TLS encryption
- Environment variable management

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License
This project is licensed under the MIT License.

## 👨‍💻 Developer
Developed by [Amoni Kevin {Egole}](https://www.linkedin.com/in/amoni-kevin/)

## 📞 Contact
- Email: info@bursary.com
- Phone: +254 796 861 525
- Location: Nairobi, Kenya

## 🙏 Acknowledgments
- Bootstrap team for the UI framework
- Flask community for excellent documentation
- All contributors and testers
```