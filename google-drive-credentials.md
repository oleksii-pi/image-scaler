This guide shows you, step-by-step, how to get a **google-drive-credentials.json** file that works with the provided `image_publisher.py` script using **OAuth Client (Desktop app)**. Uploads will appear under **your** Google account.

---

## Prerequisites

- A Google account.
- Access to the Google Cloud Console: <https://console.cloud.google.com/>

> You’ll download a JSON file and place it next to `image_publisher.py` as `google-drive-credentials.json`.

---

## 1) Create (or select) a Google Cloud project

1. Open <https://console.cloud.google.com/> and sign in.
2. Click the **project selector** (top bar) → **New Project** (or pick an existing one).
3. Name it (e.g., `image-publisher`) → **Create**.
4. Make sure the new project is **selected** (check the top bar).

---

## 2) Enable the Google Drive API for your project

1. Go to **APIs & Services → Library**.
2. Search **Google Drive API**.
3. Click **Enable**. :contentReference[oaicite:0]{index=0}

---

## 3) Configure the OAuth consent screen (once per project)

1. Go to **APIs & Services → OAuth consent screen**.
2. **User type**: choose **External**, then **Create**.
3. Fill **App name**, **User support email**, and **Developer contact** email; **Save & Continue**.
4. **Scopes** can be left empty here; the script will request them at runtime. (We recommend the **`https://www.googleapis.com/auth/drive.file`** scope in your app code so the app only sees files it creates/opens.) :contentReference[oaicite:1]{index=1}
5. Under **Audience → Test users**, click **Add users** and add the Google account you’ll use. **Save**.  
   _(If you skip this while your app is in Testing, you’ll hit “Error 403: access_denied”.)_ :contentReference[oaicite:2]{index=2}
6. You can keep **Publishing status: Testing** for now; see section **7** to remove the 7-day expiry later.

---

## 4) Create OAuth Client Credentials (Desktop app)

1. Go to **APIs & Services → Credentials**.
2. Click **+ Create credentials → OAuth client ID**.
3. **Application type**: **Desktop app** → Name it (e.g., `image-publisher-desktop`) → **Create**.
4. Click **Download JSON**. This is your OAuth client secret file.  
   _(Desktop/installed apps use a local loopback redirect in the system browser—no manual redirect URLs required.)_ :contentReference[oaicite:3]{index=3}

---

## 5) Put the file in place

1. Rename the downloaded file to **`google-drive-credentials.json`**.
2. Move it next to `image_publisher.py` in your project directory.

**Layout**
