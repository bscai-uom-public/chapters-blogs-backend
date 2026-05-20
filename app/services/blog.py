import json
from typing import List, Dict

from bson import json_util

from app.db.database import collection_blog, collection_like, database
from app.schemas.blog import (
    BlogPost,
    BlogPostWithUserData,
    AllBlogsBlogPost,
    Like,
    BlogPostCreate,
    BlogPostUpdate,
)
from app.services.auth_provider import get_user_by_id_safely
from app.core.exceptions import (
    BlogAPIException,
    BlogNotFoundException,
    BlogInsertionException,
    BlogUpdateException,
    BlogDeletionException,
    BlogOwnershipException,
    NoBlogsFoundException,
    BlogsByTagsNotFoundException,
    PermissionDeniedException,
    BlogLikeException,
    BlogUnlikeException,
    InvalidLikeValueException,
    InternalServerException,
)

CONTENT_PREVIEW_LENGTH = 150


def convert_mongo_doc_to_dict(doc):
    """Convert a MongoDB document to a dict compatible with Pydantic models."""
    if doc is None:
        return None
    doc_dict = json.loads(json_util.dumps(doc))
    for date_field in ("postedAt", "commentedAt", "repliedAt"):
        if date_field in doc_dict and isinstance(doc_dict[date_field], dict) and "$date" in doc_dict[date_field]:
            doc_dict[date_field] = doc_dict[date_field]["$date"]
    return doc_dict


async def _decorate_with_user(blog_data: dict) -> dict:
    """Inject author display fields onto a blog dict."""
    user_data = await get_user_by_id_safely(blog_data.get("user_id", ""))
    blog_data["user_username"] = user_data.username
    blog_data["user_image_url"] = user_data.profilePicUrl
    blog_data["user_first_name"] = user_data.firstName
    blog_data["user_last_name"] = user_data.lastName
    return blog_data


async def get_blog_by_id(entity_id: str) -> BlogPostWithUserData:
    try:
        entity = await collection_blog.find_one({"_id": entity_id})
        blog_data = convert_mongo_doc_to_dict(entity)
        if not blog_data:
            raise BlogNotFoundException(entity_id)

        # Public read: respect visibility flag.
        if blog_data.get("visibility", True) is False:
            raise BlogNotFoundException(entity_id)

        await collection_blog.update_one({"_id": entity_id}, {"$inc": {"number_of_views": 1}})
        blog_data = await _decorate_with_user(blog_data)
        return BlogPostWithUserData(**blog_data)

    except BlogAPIException:
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise InternalServerException


async def create_blog(blog_input: BlogPostCreate, user_id: str) -> BlogPostWithUserData:
    blog = BlogPost(
        comment_constraint=blog_input.comment_constraint,
        tags=blog_input.tags,
        title=blog_input.title,
        content=blog_input.content,
        post_image=blog_input.post_image,
        user_id=user_id,
        number_of_views=0,
        likes_count=0,
        visibility=True,
    )
    blog_dict = blog.dict(by_alias=True)
    result = await collection_blog.insert_one(blog_dict)
    if result.inserted_id:
        blog_data = blog.dict(by_alias=True)
        blog_data = await _decorate_with_user(blog_data)
        return BlogPostWithUserData(**blog_data)
    raise BlogInsertionException


async def update_blog(blog_id: str, blog_update: BlogPostUpdate, user_id: str) -> BlogPostWithUserData:
    old_blog = await collection_blog.find_one({"_id": blog_id})
    if not old_blog:
        raise BlogNotFoundException(blog_id)
    if old_blog["user_id"] != user_id:
        raise BlogOwnershipException

    update_data = {
        "title": blog_update.title,
        "content": blog_update.content,
        "tags": blog_update.tags,
        "comment_constraint": blog_update.comment_constraint,
        "post_image": blog_update.post_image,
    }
    await collection_blog.update_one({"_id": blog_id}, {"$set": update_data})

    updated_blog = await collection_blog.find_one({"_id": blog_id})
    blog_data = convert_mongo_doc_to_dict(updated_blog)
    if blog_data is None:
        raise BlogUpdateException
    blog_data = await _decorate_with_user(blog_data)
    return BlogPostWithUserData(**blog_data)


async def get_all_blogs(
    visible_only: bool = True,
    page: int = 1,
    limit: int = 12,
) -> dict:
    """Paginated blog list. Returns ``{items, total, page, limit}``."""
    import asyncio

    query = {"visibility": {"$ne": False}} if visible_only else {}
    skip = max(0, (page - 1) * limit)

    total = await collection_blog.count_documents(query)
    cursor = collection_blog.find(query).sort("postedAt", -1).skip(skip).limit(limit)
    blog_list = [b async for b in cursor]

    unique_user_ids = list({b.get("user_id") for b in blog_list if b.get("user_id")})
    user_data_cache = {}
    if unique_user_ids:
        results = await asyncio.gather(*[get_user_by_id_safely(uid) for uid in unique_user_ids])
        for uid, data in zip(unique_user_ids, results):
            user_data_cache[uid] = data

    items = []
    for blog in blog_list:
        user_data = user_data_cache.get(blog.get("user_id")) or await get_user_by_id_safely(
            blog.get("user_id", "")
        )
        content = blog.get("content", "")
        preview = content[:CONTENT_PREVIEW_LENGTH] + "..." if len(content) > CONTENT_PREVIEW_LENGTH else content
        items.append(
            AllBlogsBlogPost(
                **{
                    "_id": str(blog["_id"]),
                    "comment_constraint": blog["comment_constraint"],
                    "tags": blog["tags"],
                    "number_of_views": blog["number_of_views"],
                    "likes_count": blog.get("likes_count", 0),
                    "title": blog["title"],
                    "content_preview": preview,
                    "postedAt": blog["postedAt"],
                    "post_image": blog.get("post_image"),
                    "user_id": blog.get("user_id"),
                    "user_username": user_data.username,
                    "user_image_url": user_data.profilePicUrl,
                    "user_first_name": user_data.firstName,
                    "user_last_name": user_data.lastName,
                    "visibility": blog.get("visibility", True),
                }
            )
        )

    return {"items": items, "total": total, "page": page, "limit": limit}


async def delete_blog_by_id(id: str, user_id: str) -> BlogPostWithUserData:
    blog = await collection_blog.find_one({"_id": id})
    if not blog:
        raise BlogNotFoundException(id)
    if blog["user_id"] != user_id:
        raise PermissionDeniedException()

    blog_data = convert_mongo_doc_to_dict(blog)
    if blog_data is None:
        raise BlogDeletionException()
    blog_data = await _decorate_with_user(blog_data)
    deleted_blog = BlogPostWithUserData(**blog_data)

    result = await collection_blog.delete_one({"_id": id})
    if result.deleted_count == 0:
        raise BlogDeletionException()
    return deleted_blog


async def get_blogs_byTags(tags: List[str]) -> List[AllBlogsBlogPost]:
    query = {"tags": {"$in": tags}, "visibility": {"$ne": False}}
    if await collection_blog.count_documents(query) == 0:
        raise BlogsByTagsNotFoundException(tags)

    cursor = collection_blog.find(query)
    blogs = []
    async for document in cursor:
        user_data = await get_user_by_id_safely(document["user_id"])
        content = document.get("content", "")
        preview = content[:CONTENT_PREVIEW_LENGTH] + "..." if len(content) > CONTENT_PREVIEW_LENGTH else content
        blogs.append(
            AllBlogsBlogPost(
                **{
                    "_id": str(document["_id"]),
                    "comment_constraint": document["comment_constraint"],
                    "tags": document["tags"],
                    "number_of_views": document["number_of_views"],
                    "likes_count": document.get("likes_count", 0),
                    "title": document["title"],
                    "content_preview": preview,
                    "postedAt": document["postedAt"],
                    "post_image": document.get("post_image"),
                    "user_id": document.get("user_id"),
                    "user_username": user_data.username,
                    "user_image_url": user_data.profilePicUrl,
                    "user_first_name": user_data.firstName,
                    "user_last_name": user_data.lastName,
                    "visibility": document.get("visibility", True),
                }
            )
        )
    return blogs


# ---------- Admin moderation ----------

async def admin_list_all_blogs(status_filter: str = "all") -> List[AllBlogsBlogPost]:
    """Admin view: list every blog, optionally filtered by visibility.

    No pagination here — the admin table is expected to be small enough
    to render in one go; if it grows large later we can add page/limit.
    """
    if status_filter == "visible":
        query = {"visibility": {"$ne": False}}
    elif status_filter == "hidden":
        query = {"visibility": False}
    else:
        query = {}

    import asyncio

    cursor = collection_blog.find(query).sort("postedAt", -1)
    blog_list = [b async for b in cursor]
    unique_user_ids = list({b.get("user_id") for b in blog_list if b.get("user_id")})
    user_data_cache = {}
    if unique_user_ids:
        results = await asyncio.gather(*[get_user_by_id_safely(uid) for uid in unique_user_ids])
        for uid, data in zip(unique_user_ids, results):
            user_data_cache[uid] = data

    blogs = []
    for blog in blog_list:
        user_data = user_data_cache.get(blog.get("user_id")) or await get_user_by_id_safely(
            blog.get("user_id", "")
        )
        content = blog.get("content", "")
        preview = content[:CONTENT_PREVIEW_LENGTH] + "..." if len(content) > CONTENT_PREVIEW_LENGTH else content
        blogs.append(
            AllBlogsBlogPost(
                **{
                    "_id": str(blog["_id"]),
                    "comment_constraint": blog["comment_constraint"],
                    "tags": blog["tags"],
                    "number_of_views": blog["number_of_views"],
                    "likes_count": blog.get("likes_count", 0),
                    "title": blog["title"],
                    "content_preview": preview,
                    "postedAt": blog["postedAt"],
                    "post_image": blog.get("post_image"),
                    "user_id": blog.get("user_id"),
                    "user_username": user_data.username,
                    "user_image_url": user_data.profilePicUrl,
                    "user_first_name": user_data.firstName,
                    "user_last_name": user_data.lastName,
                    "visibility": blog.get("visibility", True),
                }
            )
        )
    return blogs


async def admin_delete_blog(id: str) -> BlogPostWithUserData:
    """Admin-override delete — ignores ownership."""
    blog = await collection_blog.find_one({"_id": id})
    if not blog:
        raise BlogNotFoundException(id)

    blog_data = convert_mongo_doc_to_dict(blog)
    blog_data = await _decorate_with_user(blog_data)
    deleted = BlogPostWithUserData(**blog_data)

    result = await collection_blog.delete_one({"_id": id})
    if result.deleted_count == 0:
        raise BlogDeletionException()
    return deleted


async def admin_set_blog_visibility(id: str, visibility: bool) -> BlogPostWithUserData:
    blog = await collection_blog.find_one({"_id": id})
    if not blog:
        raise BlogNotFoundException(id)
    await collection_blog.update_one({"_id": id}, {"$set": {"visibility": visibility}})
    updated = await collection_blog.find_one({"_id": id})
    blog_data = convert_mongo_doc_to_dict(updated)
    blog_data = await _decorate_with_user(blog_data)
    return BlogPostWithUserData(**blog_data)


# ---------- Likes ----------

async def like_or_unlike(blog_id: str, user_id: str, like_value: int):
    blog = await collection_blog.find_one({"_id": blog_id})
    if not blog:
        raise BlogNotFoundException(blog_id)

    existing_like = await collection_like.find_one({"blog_id": blog_id, "user_id": user_id})

    if like_value == 1:
        if existing_like:
            return {"message": "Blog already liked", "liked": True}
        like = Like(blog_id=blog_id, user_id=user_id)
        result = await collection_like.insert_one(like.dict(by_alias=True))
        if result.inserted_id:
            await collection_blog.update_one(
                {"_id": blog_id},
                [{"$set": {"likes_count": {"$add": [{"$ifNull": ["$likes_count", 0]}, 1]}}}],
            )
            return {"message": "Blog liked successfully", "liked": True}
        raise BlogLikeException()

    if like_value == 0:
        if existing_like:
            result = await collection_like.delete_one({"blog_id": blog_id, "user_id": user_id})
            if result.deleted_count > 0:
                await collection_blog.update_one(
                    {"_id": blog_id},
                    [
                        {
                            "$set": {
                                "likes_count": {
                                    "$max": [{"$subtract": [{"$ifNull": ["$likes_count", 0]}, 1]}, 0]
                                }
                            }
                        }
                    ],
                )
                return {"message": "Blog unliked successfully", "liked": False}
            raise BlogUnlikeException()
        return {"message": "Blog not liked yet", "liked": False}

    raise InvalidLikeValueException()


async def check_user_like_status(blog_id: str, user_id: str):
    blog = await collection_blog.find_one({"_id": blog_id})
    if not blog:
        raise BlogNotFoundException(blog_id)

    existing_like = await collection_like.find_one({"blog_id": blog_id, "user_id": user_id})
    return {
        "blog_id": blog_id,
        "user_id": user_id,
        "is_liked": existing_like is not None,
        "likes_count": blog.get("likes_count", 0),
        "like_id": str(existing_like["_id"]) if existing_like else None,
        "liked_at": existing_like.get("liked_at") if existing_like else None,
    }


async def check_database_health() -> Dict:
    import time

    try:
        start_time = time.time()
        await database.command("ping")
        blogs_count = await collection_blog.count_documents({})
        likes_count = await collection_like.count_documents({})
        response_time = round((time.time() - start_time) * 1000, 2)
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "service": "mongodb",
            "metrics": {
                "total_blogs": blogs_count,
                "total_comments": 0,
                "total_replies": 0,
                "total_likes": likes_count,
                "total_content_items": blogs_count,
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "service": "mongodb",
            "error": str(e),
            "metrics": None,
        }
