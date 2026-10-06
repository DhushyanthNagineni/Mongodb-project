import db
import app

def run_tests():
    print("========================================")
    print(" MONOGRAPH - VERIFICATION TEST RUNNER   ")
    print("========================================")

    # 1. Database Check
    print("\n[1] Checking MongoDB Collections & Aggregations...")
    all_posts = db.all_posts(include_drafts=True)
    published = db.all_posts(include_drafts=False)
    cats = db.categories()
    tags = db.tags()
    admin = db.get_admin("admin")

    print(f"  - Total Posts in MongoDB: {len(all_posts)}")
    print(f"  - Published Posts: {len(published)}")
    print(f"  - Distinct Disciplines/Categories: {len(cats)} -> {cats}")
    print(f"  - Distinct Topics/Tags: {len(tags)} -> {tags}")
    print(f"  - Admin User Present: {bool(admin)}")
    assert len(all_posts) > 0, "No posts in database!"
    assert admin is not None, "Admin user missing!"
    print("  => DB Layer: PASS")

    # 2. Flask Test Client
    print("\n[2] Testing Public Routes (No Auth Required)...")
    app.app.config["WTF_CSRF_ENABLED"] = False
    app.app.config["TESTING"] = True
    client = app.app.test_client()

    # Index
    res = client.get("/")
    assert res.status_code == 200, f"Index failed: {res.status_code}"
    assert b"MONOGRAPH" in res.data
    assert b"interactive-grid" in res.data
    print("  - GET / (Index): 200 OK")

    # Post detail
    for p in published[:2]:
        res = client.get(f"/post/{p['slug']}")
        assert res.status_code == 200, f"Post {p['slug']} failed: {res.status_code}"
        assert b"markdown-content" in res.data
        print(f"  - GET /post/{p['slug']}: 200 OK")

    # Category
    if cats:
        res = client.get(f"/category/{cats[0]}")
        assert res.status_code == 200
        print(f"  - GET /category/{cats[0]}: 200 OK")

    # Tag
    if tags:
        res = client.get(f"/tag/{tags[0]}")
        assert res.status_code == 200
        print(f"  - GET /tag/{tags[0]}: 200 OK")

    # 404 handler
    res = client.get("/post/non-existent-article-slug-xyz")
    assert res.status_code == 404
    assert b"404" in res.data
    print("  - GET /post/non-existent (404 Error Handler): 404 OK")

    # 3. Auth & Admin Security
    print("\n[3] Testing Authentication & Admin Protection...")
    # Attempt unauthorized access
    res = client.get("/admin", follow_redirects=False)
    assert res.status_code == 302, "Unauthenticated access to /admin should redirect to /login"
    assert "/login" in res.headers["Location"]
    print("  - GET /admin (Unauthenticated): 302 Redirect to /login -> PASS")

    # Login with bad password
    res = client.post("/login", data={"username": "admin", "password": "wrongpassword"}, follow_redirects=True)
    assert b"Invalid username or password" in res.data
    print("  - POST /login (Bad Password): Rejected -> PASS")

    # Login with valid credentials
    with client:
        res = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        assert res.status_code == 200
        assert b"Management Console" in res.data
        print("  - POST /login (Valid Credentials): 200 OK -> PASS")

        # Admin Dashboard
        res = client.get("/admin")
        assert res.status_code == 200
        assert b"Total Records" in res.data
        print("  - GET /admin (Authenticated Dashboard): 200 OK -> PASS")

        # Admin New Post Form GET
        res = client.get("/admin/new")
        assert res.status_code == 200
        print("  - GET /admin/new (Post Form): 200 OK -> PASS")

        # Create a test post
        test_slug = "test-automated-verification-article"
        db.delete_post(test_slug)
        res = client.post("/admin/new", data={
            "title": "Test Automated Verification Article",
            "body": "## Section Header\n\nTesting live technical markdown.\n\n```python\nprint('verified')\n```",
            "category": "Systems",
            "tags": "testing, automated, verification",
            "is_published": "on"
        }, follow_redirects=True)
        assert res.status_code == 200
        created = db.get_post(test_slug)
        assert created is not None, "Post was not created in MongoDB!"
        print(f"  - POST /admin/new (Create Post '{test_slug}'): Created in DB -> PASS")

        # Edit post
        res = client.post(f"/admin/edit/{test_slug}", data={
            "title": "Test Automated Verification Article",
            "body": "Updated body content.",
            "category": "Systems",
            "tags": "testing, updated",
            "is_published": "on"
        }, follow_redirects=True)
        assert res.status_code == 200
        updated = db.get_post(test_slug)
        assert updated["body"] == "Updated body content."
        print(f"  - POST /admin/edit/{test_slug} (Update Post): Updated in DB -> PASS")

        # Delete post
        res = client.post(f"/admin/delete/{test_slug}", follow_redirects=True)
        assert res.status_code == 200
        assert db.get_post(test_slug) is None
        print(f"  - POST /admin/delete/{test_slug} (Delete Post): Removed from DB -> PASS")

        # Test Markdown Preview API
        res = client.post("/api/preview-markdown", json={"content": "### Heading 3\n\n- item 1\n- item 2"})
        assert res.status_code == 200
        json_data = res.get_json()
        assert "<h3>Heading 3</h3>" in json_data["html"]
        print("  - POST /api/preview-markdown (Live preview): 200 OK -> PASS")

        # Logout
        res = client.get("/logout", follow_redirects=True)
        assert res.status_code == 200
        print("  - GET /logout (Session cleared): 200 OK -> PASS")

    print("\n========================================")
    print(" ALL 12 TEST SUITES PASSED SUCCESSFULLY! ")
    print("========================================")

if __name__ == "__main__":
    run_tests()
