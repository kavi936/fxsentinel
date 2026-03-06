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

## 5. Summary

| What | Where |
|------|--------|
| **Redirect after click** | Handled in app; continue URL = your origin + `/verify-email`. Add your domain to Firebase **Authorized domains**. |
| **Email body locked** | Firebase: "To help prevent spam, the message can't be edited." Only Subject and Sender name may be editable. |
| **Custom email** | Backend: `auth.generate_email_verification_link()` then send via your SMTP/SendGrid/Resend with your template. |
| **Spam** | Improve Subject/Sender; or send yourself (section 3) for full control. |
