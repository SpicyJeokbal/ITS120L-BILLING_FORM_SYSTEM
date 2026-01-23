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
cd backend
venv\Scripts\activate
python manage.py runserver
```