---

# PurposePay API Testing Guide

This document outlines the standard procedures for testing the PurposePay API. It is designed to guide developers through the complete lifecycle of the application: from User Registration and Vendor Approval to Voucher Creation and the Escrow Redemption flow.

---

## Prerequisites

* **Tool:** Postman, Insomnia, or cURL.
* **Base URL:** `https://purposepayapi.duckdns.org` (Production)
* **Media Handling:** Ensure the server-side environment has the necessary media configurations for handling file uploads (e.g., S3 or local storage persistent volumes).

---

## 1. Authentication & Accounts

**Note:** All endpoints (except Login/Register) require the Authorization header.

* **Header Key:** `Authorization`
* **Header Value:** `Token <your_generated_token_here>`

### A. Register Users

You need two actors for the full flow: a **Vendor** and a **Customer**.

**1. Register a Vendor**

* **Endpoint:** `POST /account/register/`
* **Body (JSON):**
```json
{
    "username": "vendor_user",
    "email": "vendor@example.com",
    "password": "securepassword123",
    "is_vendor": true,
    "is_customer": false
}

```



**2. Register a Customer**

* **Endpoint:** `POST /account/register/`
* **Body (JSON):**
```json
{
    "username": "customer_user",
    "email": "customer@example.com",
    "password": "securepassword123",
    "is_vendor": false,
    "is_customer": true
}

```



### B. Login

* **Endpoint:** `POST /auth/login/`
* **Body (JSON):**
```json
{
    "email": "vendor@example.com",
    "password": "securepassword123"
}

```


* **Response:** Save the `token` returned here. You will need to switch tokens when testing as the Vendor vs. the Customer.

### C. Profile Management

* **View My Account:** `GET /account/me/`
* Returns user details, phone number, and account roles.


* **Update My Account:** `PATCH /account/me/`
* **Payload:** `{"phone_number": "0244000111", "username": "updated_user"}`


* **Logout:** `POST /auth/logout/`
* Invalidates the current session token.



---

## 2. Vendor Onboarding Flow

**Actor:** Vendor (Logged in)

### A. Create Vendor Profile

The vendor account is inactive until this profile is created. Note the nested `finance` and `verification` objects.

* **Endpoint:** `POST /vendor/create/`
* **Headers:** `Authorization: Token <vendor_token>`
* **Body (Multipart/Form-Data):**
* *Text Fields:*
* `business_name`: "Accra Pharmacy"
* `phone_number`: "0244123456"
* `city`: "Accra"
* `business_address`: "Box 44, Legon"
* `gps_code`: "GA-123-4567"
* `category`: "PHARMACY"
* `finance.payout_account_number`: "1234567890"
* `finance.payout_bank_name`: "Ecobank"
* `verification.owner_id_type`: "GHANA_CARD"


* *File Fields:*
* `verification.owner_id_document`: (File)
* `verification.business_registration_document`: (File)
* `verification.business_location_image`: (File)





### B. Vendor Self-Management

* **View My Profile:** `GET /vendor/me/`
* Check verification status and current financial balance.


* **Update Finance Info:** `PATCH /vendor/me/`
* **Payload:** `{"payout_bank_name": "GCB Bank"}`



### C. Admin Approval (Simulation)

**Actor:** Admin (Superuser)

* **List Pending Vendors:** `GET /vendor/admin/?verification__status=PENDING`
* Retrieves a list of all vendors awaiting verification. Use this to find the `vendor_id` needed for approval.
* **View Vendor Detail:** `GET /vendor/admin/<vendor_id>/`
* Provides an admin-only view of a specific vendor’s documents and full profile for manual KYC (Know Your Customer) checks.
* **Approve Vendor:** `POST /vendor/admin/<vendor_id>/approve/`
* Moves a vendor from `PENDING` to `APPROVED`. This action activates the vendor's ability to redeem vouchers from customers.
* **Reject Vendor:** `POST /vendor/admin/<vendor_id>/reject/`
* Moves a vendor to `REJECTED` status. This blocks the vendor from performing any transactions on the platform.


### D. Public Vendor Directory
* **List Approved Vendors:** `GET /vendor/public/`
* A public-facing directory that allows customers to search for where they can use their vouchers.
* *Query Params:* `?category=PHARMACY&city=Accra` - Filters vendors by their business category and physical location.

---

## 3. Customer Wallet & Voucher Creation

**Actor:** Customer (Logged in)

### A. Deposit Money into Wallet

Before creating a voucher, the customer needs funds.

* **Endpoint:** `POST /voucher/wallet/deposit/`
* **Headers:** `Authorization: Token <customer_token>`
* **Body (JSON):**
```json
{
    "amount": 500.00
}

```



### B. Create a Voucher

This locks money from the Wallet into the Voucher (Escrow).

* **Endpoint:** `POST /voucher/create/`
* **Body (JSON):**
```json
{
    "category": "PHARMACY",
    "initial_amount": 200.00
}

```


* **Response:** Note the `id` and the `code` (e.g., `PP-X1Y2Z3...`). The status will be `PENDING`.

### C. Activate Voucher

The customer must activate the voucher before it can be used.

* **Endpoint:** `POST /voucher/<voucher_id>/activate/`

### D. My Vouchers & Search

* **View My Vouchers:** `GET /voucher/my/`
* Lists all vouchers owned by the logged-in customer, including their current status (ACTIVE/EXPIRED) and remaining balance.
* **Approved Vendors for Voucher Category:** `GET /voucher/vendors/approved/<category>/`
* Dynamically fetches a list of vendors specifically approved for a voucher's category (e.g., fetching all 'PHARMACY' vendors for a pharmacy voucher).

---

## 4. The Redemption Flow (Escrow Logic)

This is the core transaction. The Vendor requests payment, and the Customer confirms it.

### A. Vendor Requests Redemption

**Actor:** Vendor (Logged in)

* **Endpoint:** `POST /voucher/vendor/redemptions/create/`
* **Headers:** `Authorization: Token <vendor_token>`
* **Body (JSON):**
```json
{
    "voucher_code": "PP-YOUR-CODE-HERE",
    "redeemed_amount": 100.00
}

```


* **Logic Check:**
* Amount must be >= 50.
* Vendor Category must match Voucher Category.
* Status becomes `PENDING`.



### B. Customer Confirms Redemption

**Actor:** Customer (Logged in)

First, view pending requests:

* **Endpoint:** `GET /voucher/redemptions/pending/`
* **Response:** Get the `id` of the redemption request.

Then, confirm it:

* **Endpoint:** `PATCH /voucher/redemptions/<redemption_id>/confirm/`
* **Headers:** `Authorization: Token <customer_token>`
* **Body:** `{}`

**Result:**

1. Voucher `escrow_balance` decreases by 100.
2. Vendor `finance.balance` increases by 100.
3. Redemption status becomes `REDEEMED`.

### C. Cancellation & History

* **Cancel Redemption:** `PATCH /voucher/redemptions/<id>/cancel/`
* Allows the customer to reject a redemption request from a vendor if the amount or service is incorrect. This moves the status to `CANCELLED`.
* **Redemption History:** `GET /voucher/vendor/redemptions/history/`
* Provides a vendor with a list of all their transaction requests, showing which were confirmed, cancelled, or are still pending.

---

## 5. Vendor Payout

**Actor:** Vendor (Logged in)

Now that the vendor has been paid, they can withdraw funds to their bank.

* **Endpoint:** `POST /vendor/payout/`
* **Headers:** `Authorization: Token <vendor_token>`
* **Body (JSON):**
```json
{
    "amount": 50.00
}

```



---

## 6. Admin Voucher Oversight

**Actor:** Admin (Superuser)

* **List All Vouchers:** `GET /voucher/admin/vouchers/`
* Gives admins a system-wide view of every voucher generated, useful for monitoring total escrow volume.
* **Detailed Voucher Audit:** `GET /voucher/admin/vouchers/<id>/`
* Shows an admin the specific transaction history of a voucher, including every redemption attempt and the owner’s details.

---

## Common Error Codes & Troubleshooting

| Status Code | Meaning | Common Cause in PurposePay |
| --- | --- | --- |
| **400 Bad Request** | Validation Error | Sending text instead of numbers, invalid GPS code format, or insufficient wallet balance. |
| **401 Unauthorized** | Auth Failed | Missing `Authorization` header or invalid Token. |
| **403 Forbidden** | Permission Denied | A Customer trying to access Vendor routes, or a Vendor trying to redeem before Admin approval. |
| **404 Not Found** | Object Missing | Using a Voucher Code that doesn't exist, or trying to confirm a redemption that isn't yours. |

---

## Testing Checklist

1. [ ] **User Roles:** Can a Customer accidentally create a Vendor profile? (Should fail).
2. [ ] **Categories:** Can a "Hardware" vendor redeem a "Pharmacy" voucher? (Should fail).
3. [ ] **Balances:** Does the Customer Wallet balance decrease immediately upon Voucher creation?
4. [ ] **Overdraft:** Can a Vendor redeem more than the voucher's remaining balance? (Should fail).
5. [ ] **Concurrency:** If the Vendor clicks "Redeem" twice rapidly, does it deduct twice? (Row-locking should prevent this).

### Additional Checklist Items

6. [ ] **Invalid Tokens:** API calls fail gracefully with invalid or expired tokens.
7. [ ] **Missing Tokens:** Endpoints reject requests with no token.
8. [ ] **Role Enforcement:** Customers cannot access Admin or Vendor-only endpoints.
9. [ ] **Activation Status:** Vouchers cannot be used before activation.
10. [ ] **Expired Voucher:** Redemption is blocked after voucher expiry.
11. [ ] **Partial Redemption:** Multiple partial redemptions are handled correctly.
12. [ ] **Voucher Limits:** Creating vouchers exceeding wallet balance is prevented.
13. [ ] **Double Confirmation:** Customers cannot confirm the same redemption twice.
14. [ ] **Redemption Amount Validation:** Negative numbers, zero, or invalid decimals are rejected.
15. [ ] **Wallet Negative Balance:** Wallet cannot go below zero.
16. [ ] **Payout Limits:** Vendors cannot withdraw more than current balance.
17. [ ] **Payout Race Conditions:** Multiple simultaneous payouts maintain balance integrity.
18. [ ] **Invalid File Type/Size:** Uploading unsupported or oversized files is rejected.
19. [ ] **Missing Required Fields:** Required fields missing trigger validation errors.
20. [ ] **Large Amounts:** Very high voucher and wallet amounts are handled correctly.
21. [ ] **Simultaneous Users:** Correct balance maintenance under load.
22. [ ] **Unexpected Inputs:** Special characters in inputs are handled gracefully.

---
