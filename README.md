# ITS120L-BILLING_FORM_SYSTEM
```
mapua-library-billing/
│
├── backend/                         # Django Backend
│   ├── manage.py
│   ├── requirements.txt
│   │
│   ├── config/                      # Django settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   │
│   ├── billing/                     # Main app
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── migrations/
│   │
│   └── media/                       # User uploads
│       └── avatars/
│
├── frontend/                        # Frontend
│   │
│   ├── static/                      # CSS, JS, Images
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── images/
│   │       ├── mapua-logo.png
│   │       └── icons/
│   │
│   └── templates/                   # HTML files
│       ├── base.html
│       ├── dashboard.html
│       ├── login.html
│       └── includes/
│           └── sidebar.html
│
└── README.md
```
```
# Requirements
- Python 3.10+
- Django (will be installed via requirements.txt)

# First-time setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# If you closed the terminal or deactivated the venv
cd backend
venv\Scripts\activate
python manage.py runserver


```