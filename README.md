# PurposePay API

## Overview

PurposePay is a backend API designed to **protect remittances sent for specific purposes**. Instead of sending cash directly to relatives or other recipients where misuse is common, senders purchase purpose-bound vouchers that can only be redeemed at approved vendors for approved categories.

The core idea is simple:

* Money is **locked to a purpose**
* Recipients cannot self-credit
* Customers must confirm redemptions
* Expiry and balance rules are strictly enforced

This project currently targets **Ghana** as the initial market but is designed to be extensible.

---

## Live Production Access

* **Base API URL:** `https://purposepayapi.duckdns.org`
* **Detailed Testing Guide:** **[API_TESTING.md](https://www.google.com/search?q=./API_TESTING.md)**

---

## Problem PurposePay Solves

Real-world scenarios this API addresses:

* **School fees**: A ward claims fees are GHS 5,000 when the real amount is GHS 2,000.
* **Construction projects**: Misuse of funds meant for materials.
* **Medical support**: Funds sent for treatment are diverted.

With PurposePay:

* Funds are converted into vouchers
* Vouchers are redeemable only at approved vendors
* Vendors request redemption
* Customers explicitly confirm before money is released

This removes trust issues and misuse of funds.

---

## Core Concepts

### Voucher Lifecycle

A voucher moves through the following states:

1. **PENDING**
* Created after wallet deduction
* Not yet usable


2. **ACTIVE**
* Activated by the customer
* Can be redeemed by vendors


3. **LOCKED**
* Fully spent
* No further actions allowed


4. **EXPIRED**
* Automatically invalidated after expiry time
* Cannot be activated, redeemed, or confirmed



Expiry is enforced lazily: whenever a voucher is accessed, its status is checked and updated if necessary.

---

### Escrow System

PurposePay uses an **escrow-style balance system**:

* `remaining_balance`: what the customer still owns
* `escrow_balance`: funds reserved for pending vendor redemptions

Flow:

1. Customer purchases voucher → funds move from **wallet** → **escrow balance**
2. Vendor requests redemption → pending until customer confirmation
3. Customer confirms → funds move **escrow balance** → **vendor balance**
4. Redemption canceled or expired → funds currently remain in **escrow balance** (future updates may allow automatic refund)

This prevents double spending and unauthorized withdrawals.

---

## User Roles

### Customer

* Registers and authenticates
* Funds wallet
* Purchases vouchers
* Activates vouchers
* Confirms or rejects redemptions
* Views voucher history

### Vendor

* Applies for vendor Profile account
* Is approved by admin
* Redeems vouchers (request-based)
* Receives funds only after customer confirmation

### Admin

* Manages users and vendors
* Views all vouchers
* Monitors system-wide activity

---

## Application Structure

```
purposepay/
├── accounts/        # Custom user model, auth, profiles
├── vendor/          # Vendor onboarding & redemption logic
├── voucher/         # Voucher lifecycle & escrow system
├── home/            # Landing page
├── purposepay/      # Project settings & URLs
├── static/          # CSS and assets
├── templates/       # HTML templates

```

---

## Key Features

* **Customer Wallets**: Fund wallet and purchase vouchers
* **Voucher System**: Redeemable by recipients
* **Escrow Management**: Secure fund transfer with confirmation
* **Redemption Flow**:
1. Wallet → Escrow on voucher purchase
2. Escrow → Vendor balance on redemption confirmation
3. Canceled redemption → Escrow (currently no auto-refund)


* **API Authentication**: Token-based (DRF)
* **Filtering & Pagination**: Search, ordering, and pagination supported

---

## Installation & Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/purposepay.git
cd purposepay

```


2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows

```


3. Install dependencies:
```bash
pip install -r requirements.txt

```


4. Configure environment variables in a `.env` file:
```text
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
ALLOWED_HOSTS=*

```


5. Run migrations:
```bash
python manage.py migrate

```


6. Create a superuser:
```bash
python manage.py createsuperuser

```


7. Start the development server:
```bash
python manage.py runserver

```



---

## API Testing

* **[API_TESTING.md](https://www.google.com/search?q=./API_TESTING.md)**: Detailed endpoint testing instructions

---

## Notes

* Canceled voucher redemptions currently leave funds in escrow
* Escrow ensures secure transfer and prevents misuse before confirmation
* All operations are transaction-safe

---

## Contribution

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License

---

## Authentication

* Token-based authentication (DRF TokenAuth)
* Email-based login supported
* Permissions enforced per role (Customer / Vendor / Admin)

---

## API Design Philosophy

* No silent money movement
* Explicit confirmations for critical actions
* Defensive checks at every step
* Idempotent operations where applicable

---

## Environment Configuration

Sensitive configuration via environment variables.

Example `.env.example`:

```
SECRET_KEY=your-secret-key
DEBUG=False
DB_NAME=purposepay_db
DB_USER=db_user
DB_PASSWORD=db_password
DB_HOST=localhost
DB_PORT=3306
ALLOWED_HOSTS=127.0.0.1,localhost

```

---

## Testing

* Unit and integration tests included
* Business logic (balances, expiry, confirmations) explicitly tested
* Postman collections provided for manual testing

See **[API_TESTING.md](https://www.google.com/search?q=./API_TESTING.md)** for detailed testing flows.

---

## Security Considerations

* Wallet and voucher operations use database transactions
* `select_for_update()` prevents race conditions
* Expired vouchers blocked at every access point
* Role-based permissions enforced consistently

---

## Future Improvements

* Real payment gateway integration
* Scheduled background tasks for expiry
* Multi-country support
* Vendor payout batching
* Audit logging

---

## Final Notes

PurposePay is a **serious backend system**, not a demo CRUD app. Correctness, safety, and realistic money handling are the priorities. Understanding this codebase gives insight into how real financial backends operate.

---
