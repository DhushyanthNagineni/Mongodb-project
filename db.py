"""MongoDB connection and data-access helpers.

All persistence lives in a single MongoDB database named ``blog``.
No other storage backend is used.
"""
import os

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("MONGO_DB", "blog")

_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = _client[DB_NAME]


def ping():
    """Return True if MongoDB is reachable, otherwise False."""
    try:
        _client.admin.command("ping")
        return True
    except ServerSelectionTimeoutError:
        return False


# ---- posts ----------------------------------------------------------------

def posts_collection():
    return db["posts"]


def all_posts(include_drafts=False):
    """Return posts newest-first. Drafts are included only for the admin."""
    query = {} if include_drafts else {"is_published": True}
    return list(posts_collection().find(query).sort("created_at", -1))


def get_post(slug):
    return posts_collection().find_one({"slug": slug})


def create_post(data):
    result = posts_collection().insert_one(dict(data))
    return posts_collection().find_one({"_id": result.inserted_id})


def update_post(slug, data):
    return posts_collection().update_one({"slug": slug}, {"$set": dict(data)})


def delete_post(slug):
    return posts_collection().delete_one({"slug": slug})


def posts_by_category(category):
    return list(
        posts_collection()
        .find({"is_published": True, "category": category})
        .sort("created_at", -1)
    )


def posts_by_tag(tag):
    return list(
        posts_collection()
        .find({"is_published": True, "tags": tag})
        .sort("created_at", -1)
    )


def categories():
    """Distinct category values from all posts (newest creation first)."""
    values = posts_collection().distinct("category")
    values = [v for v in values if v]
    values.sort()
    return values


def tags():
    """Distinct tag values from all posts, sorted."""
    values = posts_collection().distinct("tags")
    values = [v for v in values if v]
    values.sort()
    return values


def slug_exists(slug, exclude=None):
    query = {"slug": slug}
    if exclude:
        query["_id"] = {"$ne": exclude}
    return posts_collection().find_one(query) is not None


# ---- admin ----------------------------------------------------------------

def admin_collection():
    return db["admin"]


def get_admin(username):
    return admin_collection().find_one({"username": username})