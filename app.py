"""Blog application: routes, auth and rendering.

Run with ``python run.py`` (development) or via a WSGI server.
"""
import math
import os
import re
from datetime import datetime

import markdown as md
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf import CSRFProtect
from werkzeug.security import check_password_hash

import db

# Load variables from .env (MONGO_URI, MONGO_DB, SECRET_KEY, ADMIN_*).
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
csrf = CSRFProtect(app)


# ---- context processors & filters -----------------------------------------

@app.context_processor
def inject_nav():
    all_p = db.all_posts(include_drafts=False)
    return {
        "nav_categories": db.categories(),
        "nav_tags": db.tags(),
        "total_published_count": len(all_p),
    }


@app.template_filter("reading_time")
def reading_time_filter(text):
    """Estimate reading time in minutes."""
    if not text:
        return 1
    # Strip markdown syntax roughly to count words
    plain = re.sub(r"[#*`_\[\]()>-]", " ", text)
    words = len(plain.split())
    minutes = max(1, math.ceil(words / 180))
    return minutes


@app.template_filter("excerpt")
def excerpt_filter(text, length=140):
    """Extract clean plain-text summary."""
    if not text:
        return ""
    plain = re.sub(r"#+\s*", "", text)
    plain = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", plain)
    plain = re.sub(r"[*`_>~]", "", plain)
    plain = " ".join(plain.split())
    if len(plain) > length:
        return plain[:length].rstrip() + "..."
    return plain


# ---- helpers --------------------------------------------------------------

def slugify(text):
    """Turn a title into a lowercase, URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "post"


def render_markdown(text):
    """Render Markdown body to HTML with syntax enhancements."""
    return md.markdown(
        text or "",
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
    )


def login_required(view):
    """Route decorator: require an active admin session."""
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in as admin first.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def now():
    return datetime.utcnow()


# ---- public routes ----------------------------------------------------------

@app.route("/")
def index():
    posts = db.all_posts()
    return render_template("index.html", posts=posts)


@app.route("/post/<slug>")
def post(slug):
    post_doc = db.get_post(slug)
    if not post_doc or not post_doc.get("is_published"):
        abort(404)
    post_doc["rendered_body"] = render_markdown(post_doc.get("body"))
    # Also fetch previous/next posts for navigation
    all_published = db.all_posts()
    curr_idx = next(
        (i for i, p in enumerate(all_published) if p["slug"] == slug), -1
    )
    prev_post = (
        all_published[curr_idx + 1]
        if curr_idx != -1 and curr_idx + 1 < len(all_published)
        else None
    )
    next_post = (
        all_published[curr_idx - 1]
        if curr_idx > 0
        else None
    )
    return render_template(
        "post.html",
        post=post_doc,
        prev_post=prev_post,
        next_post=next_post,
    )


@app.route("/category/<name>")
def category(name):
    posts = db.posts_by_category(name)
    return render_template("category.html", name=name, posts=posts)


@app.route("/tag/<name>")
def tag(name):
    posts = db.posts_by_tag(name)
    return render_template("tag.html", name=name, posts=posts)


@app.route("/api/preview-markdown", methods=["POST"])
@login_required
def preview_markdown():
    """Live preview endpoint for Markdown in editor."""
    data = request.get_json(silent=True) or {}
    content = data.get("content", "")
    return jsonify({"html": render_markdown(content)})


# ---- auth -------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        admin = db.get_admin(username)
        if admin and check_password_hash(admin["password_hash"], password):
            session["logged_in"] = True
            session["username"] = admin["username"]
            flash(f"Welcome back, {admin['username']}!", "success")
            next_url = request.args.get("next") or url_for("admin_dashboard")
            return redirect(next_url)

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out safely.", "success")
    return redirect(url_for("index"))


# ---- admin routes ------------------------------------------------------------

@app.route("/admin")
@login_required
def admin_dashboard():
    posts = db.all_posts(include_drafts=True)
    published_count = sum(1 for p in posts if p.get("is_published"))
    drafts_count = len(posts) - published_count
    stats = {
        "total": len(posts),
        "published": published_count,
        "drafts": drafts_count,
        "categories": len(db.categories()),
        "tags": len(db.tags()),
    }
    return render_template("admin/dashboard.html", posts=posts, stats=stats)


@app.route("/admin/new", methods=["GET", "POST"])
@login_required
def admin_new():
    if request.method == "POST":
        return _save_post()
    return render_template("admin/post_form.html", post=None, mode="new")


@app.route("/admin/edit/<slug>", methods=["GET", "POST"])
@login_required
def admin_edit(slug):
    post_doc = db.get_post(slug)
    if not post_doc:
        abort(404)
    if request.method == "POST":
        return _save_post(post_doc)
    return render_template("admin/post_form.html", post=post_doc, mode="edit")


@app.route("/admin/delete/<slug>", methods=["POST"])
@login_required
def admin_delete(slug):
    db.delete_post(slug)
    flash("Post permanently deleted.", "success")
    return redirect(url_for("admin_dashboard"))


def _save_post(existing=None):
    """Validate and persist a post from the form (create or edit)."""
    title = (request.form.get("title") or "").strip()
    body = (request.form.get("body") or "").strip()
    category = (request.form.get("category") or "").strip()
    tags_raw = (request.form.get("tags") or "").strip()
    is_published = request.form.get("is_published") == "on"

    tags = [t.strip() for t in re.split(r"[,\n]+", tags_raw) if t.strip()]

    if not title:
        flash("Title is required.", "error")
        return render_template(
            "admin/post_form.html",
            post=existing,
            mode="edit" if existing else "new",
        )

    tags = sorted(list({t.lower() for t in tags}))  # dedupe, case-insensitive

    if existing is None:
        slug = slugify(title)
        candidate, index = slug, 1
        while db.slug_exists(candidate):
            candidate = f"{slug}-{index}"
            index += 1
        slug = candidate
        payload = {
            "title": title,
            "slug": slug,
            "body": body,
            "category": category,
            "tags": tags,
            "author": session.get("username", "admin"),
            "is_published": is_published,
            "created_at": now(),
            "updated_at": now(),
        }
        db.create_post(payload)
        flash(f'Created post "{title}" successfully!', "success")
        return redirect(url_for("admin_edit", slug=slug))

    db.update_post(
        existing["slug"],
        {
            "title": title,
            "body": body,
            "category": category,
            "tags": tags,
            "is_published": is_published,
            "updated_at": now(),
        },
    )
    flash(f'Updated post "{title}" successfully!', "success")
    return redirect(url_for("admin_edit", slug=existing["slug"]))


# ---- error pages --------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html", error=error), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)