# PurposePay API

PurposePay is a backend API for managing remittances from abroad. The project has a modular structure with three apps:

| App           | Status      | Description                                                                                           |
| ------------- | ----------- | ----------------------------------------------------------------------------------------------------- |
| Accounts      | Implemented | Handles user registration, login, logout, profile management, and roles (`is_vendor` / `is_customer`) |
| Voucher       | Coming Soon | Will handle voucher creation, redemption, and tracking                                                |
| VendorProfile | Coming Soon | Will manage vendor-specific vendor profiles                                                           |

Right now, only the **accounts app** is ready. The API uses token authentication to secure endpoints.

## Features

* User registration with roles (`is_vendor` / `is_customer`)
* Login with email and password using token authentication
* View and update profile at `/account/me/`
* Login and logout endpoints under `/auth/`
* Easy to expand with more apps later

## Project Structure

```
purposepay/
├── accounts/        # Users, login, logout, profile
├── voucher/         # Future app (vouchers)
├── vendorprofile/   # Future app (vendor profiles)
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
  Fields: `username`, `email`, `password`, `is_vendor`, `is_customer`
  No authentication needed.

* **Login**: `POST /auth/login/`
  Fields: `email`, `password`
  Returns a token. No authentication needed.

* **Logout**: `POST /auth/logout/`
  Invalidates the token. Authentication required.

* **Profile**: `GET / PATCH / PUT /account/me/`
  View or update the logged-in user profile. Authentication required.

Include the token in headers for protected requests:

```
Authorization: Token <your_token_here>
```

## Testing the Accounts App

Use these JSON examples in Postman or curl.

**Register a user**:

```json
{
  "username": "testuser",
  "email": "testuser@example.com",
  "password": "TestPassword123",
  "is_vendor": false,
  "is_customer": true
}
```

**Login**:

```json
{
  "email": "testuser@example.com",
  "password": "TestPassword123"
}
```

**Access profile** with token:

```
Authorization: Token <your_token_here>
```

**Update profile**:

```json
{
  "is_vendor": true
}
```

**Logout**:

```
Authorization: Token <your_token_here>
```

## Notes

* Tokens are generated at signup using `signals.py`. Logging out removes the token; login again to get a new one.
* `is_vendor` and `is_customer` define user roles.
* Login/logout endpoints are under `/auth/`; other account actions are under `/account/`.
* Future apps (voucher, vendor profile) will be added without changing the core structure.
