"""
Manual auth smoke test for Supabase Bearer-only flow.

Run after starting the FastAPI server and exporting:
  SUPABASE_TEST_TOKEN_USER1=<valid access token for user A>
  SUPABASE_TEST_TOKEN_USER2=<valid access token for user B>
"""

import os
import requests

BASE_URL = os.getenv("BLOGS_API_BASE_URL", "http://localhost:3003/api/v1/blogs")


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def print_check(name: str, ok: bool, details: str = "") -> None:
    icon = "PASS" if ok else "FAIL"
    suffix = f" - {details}" if details else ""
    print(f"[{icon}] {name}{suffix}")


def cleanup_test_data(created_items):
    """Clean up test data from the database."""
    print("\nCleaning up test data...")
    cleanup_order = ["reply", "comment", "blog"]

    for item_type in cleanup_order:
        items_to_delete = [item for item in created_items if item["type"] == item_type]

        for item in items_to_delete:
            response = None
            try:
                if item_type == "blog":
                    response = requests.delete(
                        f"{BASE_URL}/blogs/{item['id']}", headers=item["headers"]
                    )
                elif item_type in ["comment", "reply"]:
                    response = requests.delete(
                        f"{BASE_URL}/delete-comment-reply/{item['id']}", headers=item["headers"]
                    )

                deleted = response is not None and response.status_code in [200, 204]
                print_check(f"delete {item_type} {item['id']}", deleted, str(response.status_code) if response else "no response")
            except Exception as err:
                print_check(f"delete {item_type} {item['id']}", False, str(err))


def run_authentication_smoke():
    print("Testing Supabase Bearer authentication")
    print("=" * 50)

    token_user1 = os.getenv("SUPABASE_TEST_TOKEN_USER1", "").strip()
    token_user2 = os.getenv("SUPABASE_TEST_TOKEN_USER2", "").strip()
    if not token_user1:
        raise RuntimeError("SUPABASE_TEST_TOKEN_USER1 is required.")

    headers_user1 = auth_header(token_user1)
    headers_user2 = auth_header(token_user2) if token_user2 else headers_user1
    created_items = []

    # 0) health check
    health = requests.get(f"{BASE_URL}/health")
    print_check("health endpoint", health.status_code == 200, f"status={health.status_code}")

    # 1) missing auth should fail
    blog_data = {
        "comment_constraint": True,
        "tags": [1, 2],
        "number_of_views": 0,
        "title": "Supabase Auth Test Blog",
        "content": "This validates bearer-only auth behavior.",
    }
    unauth = requests.post(f"{BASE_URL}/createblog", json=blog_data)
    print_check("reject missing auth", unauth.status_code == 401, f"status={unauth.status_code}")

    # 2) invalid bearer should fail
    invalid = requests.post(
        f"{BASE_URL}/createblog",
        json=blog_data,
        headers=auth_header("not-a-valid-jwt"),
    )
    print_check("reject invalid bearer token", invalid.status_code == 401, f"status={invalid.status_code}")

    # 3) X-User-ID fallback must be rejected
    header_only = requests.post(
        f"{BASE_URL}/createblog",
        json=blog_data,
        headers={"X-User-ID": "legacy-header-user"},
    )
    print_check("reject header-only auth", header_only.status_code == 401, f"status={header_only.status_code}")

    # 4) valid bearer should pass
    create = requests.post(f"{BASE_URL}/createblog", json=blog_data, headers=headers_user1)
    created = create.status_code in [200, 201]
    print_check("allow valid bearer token", created, f"status={create.status_code}")
    if not created:
        print(create.text)
        return

    payload = create.json()
    blog_id = payload.get("blog_id") or payload.get("blogPost_id") or payload.get("_id")
    created_items.append({"type": "blog", "id": blog_id, "headers": headers_user1})
    print_check("create blog id extracted", bool(blog_id), str(blog_id))

    # 5) ownership check with second user token (or same token fallback)
    edit_attempt = requests.put(
        f"{BASE_URL}/updateblog/{blog_id}",
        json={"title": "Unauthorized update", "content": "Should fail", "tags": [1]},
        headers=headers_user2,
    )
    if token_user2:
        print_check("forbid update by different user", edit_attempt.status_code == 403, f"status={edit_attempt.status_code}")
    else:
        print_check("update with same fallback token", edit_attempt.status_code in [200, 201], f"status={edit_attempt.status_code}")

    # 6) owner update should pass
    owner_update = requests.put(
        f"{BASE_URL}/updateblog/{blog_id}",
        json={"title": "Owner update", "content": "Updated by owner", "tags": [1, 2]},
        headers=headers_user1,
    )
    print_check("allow owner update", owner_update.status_code == 200, f"status={owner_update.status_code}")

    # 7) auth debug endpoint should pass with bearer
    debug_auth = requests.get(f"{BASE_URL}/debug/test-auth-with-bearer", headers=headers_user1)
    print_check("debug bearer auth endpoint", debug_auth.status_code == 200, f"status={debug_auth.status_code}")

    cleanup_test_data(created_items)


if __name__ == "__main__":
    try:
        run_authentication_smoke()
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server. Ensure FastAPI is running and BLOGS_API_BASE_URL is correct.")
    except Exception as err:
        print(f"Test failed with error: {err}")
