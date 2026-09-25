# AutoMailSender

Send a personalised email (name, unique code, anything from your Excel columns) to every
row of an Excel file, from a **Gmail** or **Microsoft 365 / Outlook** account.

## 1. Prepare your Excel file

The first row must be the column headings. You need an email column, and you can add any other columns you want
(e.g. a Google Form export plus a **Code** column):

| Full Name     | Email Address        | … | Code     |
|---------------|----------------------|---|----------|
| Tanmay Shetty | tshetty510@gmail.com | … | NX7K2Q9M |

See `sample_recipients.xlsx`. In the template, write `{{Full Name}}`, `{{Code}}` and so on. Any column
heading works as a placeholder. Capitals, extra spaces and line breaks in headings don't matter.
`{{First Name}}` is created automatically from a "Name" or "Full Name" column.

## 2. Choose how to send

### Option A: Gmail (App Password)

1. Turn on **2-Step Verification**: https://myaccount.google.com/security
2. Create an **App Password**: https://myaccount.google.com/apppasswords
3. On the website, pick **Gmail** and enter your address and the 16-character App Password.

This only works for Google accounts. Organisation addresses on Microsoft 365 (such as
`@d227toastmasters.org`) must use Option B.

### Option B: Microsoft 365 / Outlook (Sign in with Microsoft)

Microsoft no longer allows password logins for sending mail, so this uses Microsoft's official sign-in.
Do this one-time setup:

1. Go to https://entra.microsoft.com and sign in with your organisation account (e.g. `you@d227toastmasters.org`).
2. Go to **Applications → App registrations → New registration**.
   - **Name:** `Nexus Mailer`
   - **Supported account types:** *Accounts in this organizational directory only*
   - **Redirect URI:** choose platform **Single-page application (SPA)** and enter
     `http://localhost:5050/auth.html`
   - Click **Register**.
3. On the app's page, open **Authentication** and add the redirect URIs for your hosted site too:
   - `https://mailer.tanmayshetty.com/auth.html`
   - `https://<your-project>.vercel.app/auth.html`
4. Open **API permissions**, then **Add a permission → Microsoft Graph → Delegated permissions**, and tick **Mail.Send**.
   `User.Read` is already there. If you're an admin, click **Grant admin consent**. If you aren't,
   ask your Microsoft 365 admin to grant it; many organisations block users from approving apps themselves.
5. From the **Overview** page, copy:
   - **Application (client) ID** → setting `MS_CLIENT_ID`
   - **Directory (tenant) ID** → setting `MS_TENANT`. You can also use the domain, e.g. `d227toastmasters.org`.

Neither value is a secret. On the website, pick **Microsoft 365 / Outlook** and click **Sign in with Microsoft**.
Emails are sent from the signed-in account and appear in its **Sent Items**.

If you can't create an app registration in the organisation's directory, register it with any other
Microsoft account instead. Choose *Accounts in any organizational directory and personal Microsoft
accounts*, and leave `MS_TENANT` unset. An admin of `d227toastmasters.org` will still need to approve it.

## 3. Run it on your computer

```bash
pip install -r requirements.txt
MS_CLIENT_ID=<client-id> MS_TENANT=<tenant-id> python3 api/index.py   # leave out the MS_ settings for Gmail only
```

Open **http://localhost:5050**. Use `localhost`, not `127.0.0.1`, because Microsoft sign-in only accepts `localhost`.

## 4. Host it on Vercel

Push to GitHub and import the repo at https://vercel.com/new. There are no build settings to change.
For Microsoft sign-in, add `MS_CLIENT_ID` and `MS_TENANT` under **Project → Settings → Environment Variables**,
then redeploy.

**Custom domain:** under **Project → Settings → Domains**, add e.g. `mailer.tanmayshetty.com`, then create the
CNAME record Vercel shows at your domain provider.

## Limits

| | Gmail | Microsoft 365 | Outlook.com (free) |
|---|---|---|---|
| Emails per day | ~500 | 10,000 recipients | ~300 |
| Speed | — | ~30 per minute (keep delay ≥ 2 s) | — |
| Attachments per email | 25 MB locally, 3 MB on Vercel | 3 MB | 3 MB |

## How it works

- The browser reads the Excel file, fills in the template for each person, shows the preview and
  sends the emails one at a time. Keep the tab open while sending. **Stop** stops the run after the current email.
- **Gmail:** `api/index.py` is a stateless Flask function. It logs in to Gmail over SMTP for each
  email and never stores your App Password, recipients or attachments.
- **Microsoft:** the browser signs in with MSAL and calls Microsoft Graph `sendMail` directly. The
  sign-in token lives only in this browser tab's session storage.
- Participant spreadsheets are git-ignored, so they can't be committed by accident.
