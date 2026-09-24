# AutoMailSender

Send a personalised email (name, unique code, anything from your Excel columns) to every
row of an Excel file, from your Gmail account.

## 1. Get a Gmail App Password (one time)

1. Turn on **2-Step Verification**: https://myaccount.google.com/security
2. Create an **App Password**: https://myaccount.google.com/apppasswords
3. Copy the 16-character password. You'll enter it on the website. Your normal Gmail password won't work.

## 2. Prepare your Excel file

The first row must be the column headings. You need an email column, and you can add any other columns you want:

| Name          | Email               | Code     |
|---------------|---------------------|----------|
| Tanmay Shetty | tshetty510@gmail.com | AMS-1001 |

See `sample_recipients.xlsx`. In the template, write `{{Name}}`, `{{Code}}` and so on. Any column
heading works as a placeholder, and capitals don't matter.

## 3. Run it on your computer

```bash
pip install -r requirements.txt
python api/index.py
```

Open http://127.0.0.1:5050

## 4. Host it on Vercel

```bash
npm i -g vercel
vercel          # first deploy (preview)
vercel --prod   # production URL
```

Or push this folder to GitHub and import it at https://vercel.com/new. No settings are needed.

**Limits on Vercel:** attachments can total at most **3 MB** per email, because Vercel caps
request size at 4.5 MB. Locally the limit is 25 MB.

## How it works

- The browser reads the Excel file, fills in the template for each person, shows the preview and
  sends one request per email.
- `api/index.py` is a stateless Flask function. It logs in to Gmail over SMTP and sends that one email.
  It never stores your App Password, recipients or attachments.
- Keep the tab open while sending. The **Stop** button stops the run after the current email finishes.
- A normal Gmail account can send about 500 emails a day.
# AutoMailSender
