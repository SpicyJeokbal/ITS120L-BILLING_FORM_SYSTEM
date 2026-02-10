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
│   │   ├── supabase_client.py
│   │   ├── auth_backend.py
│   │   ├── context_processors.py
│   │   ├── decorators.py
│   │   ├── user_management_views.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   └── media/                       # User uploads
│   │   └── avatars/
│   └── manage.py
│   └── requirements.txt
│
├── frontend/                        # Frontend
│   │
│   ├── static/                      # CSS, JS, Images
│   │   ├── css/
│   │   │   └── style.css            # Dashboard
│   │   │   └── login.css
│   │   │   └── logs.css
│   │   │   └── user_management.css
│   │   ├── js/
│   │   │   └── main.js              # Dashboard
│   │   │   └── login.js 
│   │   │   └── register.js 
│   │   │   └── logs.js 
│   │   │   └── user_management.js 
│   │   └── images/
│   │       ├── mapua-logo.png
│   │       └── icons/
│   │
│   └── templates/                   # HTML files
│       ├── base.html
│       ├── dashboard.html
│       ├── login.html
│       ├── register.html
│       ├── logs.html
│       ├── user_management.html
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