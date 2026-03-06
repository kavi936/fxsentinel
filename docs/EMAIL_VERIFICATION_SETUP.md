# Email verification: branding and redirect

Verification emails are sent by **Firebase Authentication**. The app sends the verification with a **continue URL** so that after the user clicks the link they land on **our** branded page (`/verify-email`), not Firebase's default page.

## 1. Redirect (continue URL) – already in code

The app calls `sendEmailVerification(user, { url: getEmailVerificationContinueUrl() })`, which uses:

- **Production:** `https://fxsentinel.io/verify-email`
- **Local:** `http://localhost:5173/verify-email` (when running on localhost)

So the **redirect page** after clicking the link is always our branded Verify Email page.

**Required:** The domain must be an **Authorized domain** in Firebase:

1. [Firebase Console](https://console.firebase.google.com) → your project → **Authentication** → **Settings** (or **Sign-in method** tab) → **Authorized domains**.
2. Ensure **`fxsentinel.io`** is listed (and **`localhost`** for local testing).
3. If you use another production domain, add it there too.

Without this, the continue URL may be rejected and users could see an error or the default Firebase page.

---

## 2. "The message can't be edited" – Firebase's restriction

Firebase may show: **"To help prevent spam, the message can't be edited on this email template."** So the **body** of the verification email is locked; you can only change what the Console still allows (e.g. **Subject**, **Sender name**). The default text ("Hello %DISPLAY_NAME%, Follow this link… Thanks, Your %APP_NAME% team") will stay, and %APP_NAME% may show as "project-92187574391".

**What you can still do in the Console (if allowed):**

- **Subject:** Set to `Verify your FXSentinel email` so the subject line is branded.
- **Sender name:** If there's a field for it, set to `FXSentinel` so the "From" line doesn't say "not provided".

The **link** in the email still works and still uses your continue URL (our app), so after they click they land on our branded `/verify-email` page.

---

## 3. Option: Custom verification email (Admin SDK + your own email)

If you need **full control** over the email body (branding, "The FXSentinel team", no "project-…"), you have to **stop using Firebase's built-in send** and do this instead:

1. **Backend** uses the **Firebase Admin SDK** to generate a one-time verification link: `auth.generate_email_verification_link(email, action_code_settings)`.
2. **Backend** sends an email with that link using **your** email service (e.g. SMTP, SendGrid, Resend) and **your** HTML/text template.

**Flow:**

- User signs up on the client as now. Client **does not** call `sendEmailVerification()`. Instead, after signup the client calls your backend, e.g. `POST /api/send-verification-email` (with the user's id token or email).
- Backend: verify the user exists and is unverified, call `auth.generate_email_verification_link(email, action_code_settings)` with `url` set to your continue URL (e.g. `https://fxsentinel.io/verify-email`), then send your own email with that link.

**Python (Admin SDK) example:**

```python
from firebase_admin import auth

action_code_settings = {
    'url': 'https://fxsentinel.io/verify-email',  # or from env
    'handleCodeInApp': False,
}
link = auth.generate_email_verification_link(email, action_code_settings)
# Send an email with `link` in the body using your SMTP / SendGrid / Resend.
```

Your backend already has `firebase_admin` and SMTP (e.g. in `app.py`). You'd add an endpoint that generates the link and reuses your existing email-sending logic (or integrate SendGrid/Resend) with a custom template that says "The FXSentinel team" and your branding.

**Summary:** If the Console won't let you edit the message, you can only improve Subject and Sender name there. For a fully custom message, use the Admin SDK to generate the link and send the email yourself from the backend.

---

## 4. Why it might go to spam and what you can do

- **Sender address:** Mail is sent from Firebase (e.g. `noreply@fxsentinel.firebaseapp.com`). You can't change that domain without using a custom email flow (e.g. your own SMTP or a Firebase extension).
- **Content:** Generic or "project-…" style text often triggers filters. Using a clear app name (FXSentinel), a proper greeting, and a link to your site usually helps.
- **Reputation:** New or low-volume senders get more scrutiny. As more users receive and open the email (and don't mark it spam), deliverability tends to improve.

**Practical steps:**

1. Set Subject and Sender name in the Console as in section 2 (if allowed).
2. (Optional) On the "Verify your email" or "Check your inbox" screen in the app, add a short note: "If you don't see the email, check your spam folder and add our sender to your contacts."
3. For full control and better deliverability, use the custom flow in section 3 (Admin SDK + your own email service).

---

## 5. How professional SaaS products do branded verification and welcome emails

Professional businesses and large software companies typically do **not** send verification or welcome emails from generic domains like `@firebaseapp.com`. Instead they:

### 5.1 Send from their own domain

- **From:** `no-reply@company.com` or `support@company.com` (not `noreply@project.firebaseapp.com`).
- The domain has proper **DNS authentication**:
  - **SPF** – DNS TXT record listing authorized mail servers.
  - **DKIM** – Cryptographic signature so Gmail/Outlook can verify the email wasn't altered and came from your domain.
  - **DMARC** – Policy (`p=none` → `quarantine` → `reject`) telling providers to trust only mail that passes SPF/DKIM.

Without this, even well-designed emails often land in spam.

### 5.2 Use a transactional email provider (ESP)

Instead of Firebase sending the email directly, they use:

- **SendGrid, Postmark, Mailgun, Resend, AWS SES**, etc.

Flow:

1. Backend generates the verification link (e.g. Firebase Admin SDK `generate_email_verification_link`).
2. Backend calls the ESP API with: From `no-reply@company.com`, To user, template ID, dynamic data (name, verify_link).
3. ESP handles delivery, bounce tracking, and reputation.

### 5.3 Use HTML templates with consistent branding

- **Header:** Logo + app name.
- **Headline:** "Verify your email" or "Welcome to FXSentinel".
- **Body:** One clear primary CTA button (the link), fallback raw URL, short explanation.
- **Footer:** Company name, site link, support/help link.

All transactional emails (verification, password reset, invoices) share the same layout, colors, typography, and sender identity.

### 5.4 Separate transactional vs marketing traffic

- **Transactional:** verification, password reset, invoices, security alerts. Often `no-reply@company.com`. High deliverability, strict content.
- **Marketing:** newsletters, product updates. Often `updates@company.com`. Full unsubscribe, tracking, etc.

Keeping them separate helps reputation: verification emails don't get mixed with marketing blasts.

### 5.5 Warm up and monitor reputation

- Start with low volume; avoid test-spamming your own Gmail repeatedly.
- Use ESP dashboards and DMARC reports to watch for spam complaints, bounces, and misconfigurations.

### 5.6 For verification links specifically

Many still use a vendor link (Firebase, Auth0, Cognito) but:

- Generate the link on the **backend** (Admin SDK).
- Embed it in **their own template** and send from **their own sender** via their ESP.

For FXSentinel, the professional pattern would be: backend calls `auth.generate_email_verification_link()`, then sends via your ESP as `no-reply@fxsentinel.io` with a branded HTML template and proper SPF/DKIM/DMARC on `fxsentinel.io`.

---

## 6. Summary

| What | Where |
|------|--------|
| **Redirect after click** | Handled in app; continue URL = your origin + `/verify-email`. Add your domain to Firebase **Authorized domains**. |
| **Email body locked** | Firebase: "To help prevent spam, the message can't be edited." Only Subject and Sender name may be editable. |
| **Custom email** | Backend: `auth.generate_email_verification_link()` then send via your SMTP/SendGrid/Resend with your template. |
| **Spam** | Improve Subject/Sender; or send yourself (section 3) for full control. |
| **Pro pattern** | Section 5: own domain, ESP, SPF/DKIM/DMARC, branded HTML templates. |
