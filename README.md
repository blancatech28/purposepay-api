# PurposePay API

PurposePay is a backend API for managing remittances from abroad. The project has a modular structure with three apps:

| App      | Status      | Description                                                                                                                                           |
| -------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Accounts | Implemented | Handles user registration, login, logout, profile management, and roles (`is_vendor` / `is_customer`)                                                 |
| Vendor   | Completed   | Fully implemented vendor management with profiles, verification documents, business locations, serializers, views, URLs, admin interface, and payouts |
| Voucher  | Coming Soon | Will handle voucher creation, redemption, and tracking                                                                                                |

Both the **accounts app** and the **vendor app** are fully functional. The API uses token authentication to secure endpoints.

## Features

* User registration with roles (`is_vendor` / `is_customer`)
* Login with email and password using token authentication
* View and update profile at `/account/me/`
* Login and logout endpoints under `/auth/`
* Vendor app features:

  * Create and manage vendor profiles
  * Upload and manage verification documents (IDs, certificates)
  * Upload and manage business location images
  * Public vendor listing and detail view for authenticated users
  * Admin views to list, approve, reject, and manage vendor profiles
  * Payout requests for vendors with balance tracking
  * Fully tested serializers, views, URLs, and admin interface
* Easy to expand with more apps later

## Project Structure

```
purposepay/
├── accounts/        # Users, login, logout, profile
├── vendor/          # Completed vendor app (profiles, documents, locations, payouts)
├── voucher/         # Future app (vouchers)
├── purposepay/      # Project settings and URLs
├── manage.py
└── requirements.txt
```

## Installation

Clone the repository:

```bash
git clone git@github.com:blancatech28/purposepay-api.git
cd purposepay
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

Create a `.env` file with your environment variables:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
```

Run migrations:

```bash
python manage.py migrate
```

Start the server:

```bash
python manage.py runserver
```

Default URL: `http://127.0.0.1:8000/`

## API Endpoints (Accounts App)

* **Register a user**: `POST /account/register/`
* **Login**: `POST /auth/login/`
* **Logout**: `POST /auth/logout/`
* **Profile**: `GET / PATCH / PUT /account/me/`

## Vendor App Endpoints

* **Vendor self profile**: `GET/PATCH /vendor/me/`
* **Create vendor profile**: `POST /vendor/create/`
* **Public vendor list**: `GET /vendor/public/`
* **Public vendor detail**: `GET /vendor/public/<id>/`
* **Admin vendor list**: `GET /vendor/admin/`
* **Admin vendor detail**: `GET/PATCH /vendor/admin/<id>/`
* **Admin approve vendor**: `POST /vendor/admin/<id>/approve/`
* **Admin reject vendor**: `POST /vendor/admin/<id>/reject/`
* **Vendor payout request**: `POST /vendor/payout/`

## Notes

* Tokens are generated at signup using `signals.py`. Logging out removes the token; login again to get a new one.
* `is_vendor` and `is_customer` define user roles.
* Vendor app is fully functional, tested, and integrated.
* Voucher app is coming soon and will be added without changing the core structure.
