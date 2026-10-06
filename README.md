# MONOGRAPH — Technical Engineering Journal

A high-performance technical engineering publication built strictly with **Python Flask** and **MongoDB**. Visitors read long-form technical monographs filtered by discipline and topic, while authenticated administrators compose, edit, preview, and manage publications.

Everything is stored exclusively in **MongoDB** — no SQL, no filesystem storage.

---

## Technical Architecture

- **Runtime**: Python 3.9 (Anaconda environment exclusively)
- **Backend**: Python Flask 2.3.3 + Jinja2 + Flask-WTF (CSRF Protection)
- **Database**: MongoDB Server 8.3 via PyMongo driver
- **Typography & UI**: Space Grotesk, Plus Jakarta Sans, JetBrains Mono
- **Interactive Canvas**: HTML5 Canvas rendering a mouse-reactive particle/dot grid with spring physics
- **Content Rendering**: Python Markdown with code highlighting, table extensions, and live asynchronous preview

---

## Setup & Execution (Anaconda Python)

### 1. Configure Environment
Activate your Anaconda environment:
```bash
conda activate blogenv
pip install -r requirements.txt
```

### 2. Environment Variables
Verify `.env` configuration:
```ini
MONGO_URI=mongodb://localhost:27017
MONGO_DB=blog
SECRET_KEY=dev-secret-key-change-me
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 3. Verify MongoDB Service
Ensure MongoDB is running locally on port `27017`.

### 4. Database Seed
Initialize the default administrative account and technical articles:
```bash
python seed.py
```

### 5. Launch the Application
```bash
python run.py
```
Visit `http://127.0.0.1:5000` in your browser.

---

## Credentials
- **Username**: `admin`
- **Password**: `admin123`
- Access the management console at `/login` or via the **Console** link in the navigation header.

---

## Verification Test Suite
Run the automated end-to-end verification suite with:
```bash
python test_verification.py
```

---

## Data Model (`blog` database)

### `posts` Collection
- `title` *(String)*: Publication title
- `slug` *(String, unique)*: URL-safe identifier
- `body` *(String)*: Full text in Markdown
- `category` *(String)*: Discipline / category
- `tags` *(Array of Strings)*: Topic tags
- `author` *(String)*: Author username
- `created_at` *(ISODate)*: Creation timestamp
- `updated_at` *(ISODate)*: Last modification timestamp
- `is_published` *(Boolean)*: Publication state (Published vs Private Draft)

### `admin` Collection
- `username` *(String)*: Administrative username
- `password_hash` *(String)*: Werkzeug scrypt/pbkdf2 hash

---

## API & Route Index

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| `GET` | `/` | Public | Journal index with search & filtering |
| `GET` | `/post/<slug>` | Public | Full article view with reading time |
| `GET` | `/category/<name>` | Public | Filtered articles by discipline |
| `GET` | `/tag/<name>` | Public | Filtered articles by topic tag |
| `GET, POST` | `/login` | Public | Administrative authentication |
| `GET` | `/logout` | Authenticated | Session termination |
| `GET` | `/admin` | Authenticated | Publication metrics & management dashboard |
| `GET, POST` | `/admin/new` | Authenticated | Compose new technical essay |
| `GET, POST` | `/admin/edit/<slug>` | Authenticated | Edit existing publication |
| `POST` | `/admin/delete/<slug>` | Authenticated | Delete publication |
| `POST` | `/api/preview-markdown` | Authenticated | Asynchronous live Markdown compiler |
