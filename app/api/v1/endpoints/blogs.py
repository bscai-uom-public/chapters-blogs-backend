from typing import List, Optional
from fastapi import APIRouter, Query, Depends, status, Request, Response

from app.schemas.blog import (
    AllBlogsBlogPost,
    BlogPostWithUserData,
    BlogPostCreate,
    BlogPostUpdate,
    LikeRequest,
    LikeResponse,
    LikeStatusResponse,
    HealthCheckResponse,
    AuthUserProfile,
    PaginatedBlogList,
)
from app.schemas.responses import (
    HEALTH_CHECK_RESPONSES,
    AUTH_PROVIDER_USERS_LIST_RESPONSES,
    AUTH_PROVIDER_USER_RESPONSES,
    BLOGS_LIST_RESPONSES,
    BLOGS_BY_TAGS_RESPONSES,
    BLOG_GET_RESPONSES,
    BLOG_CREATE_RESPONSES,
    BLOG_UPDATE_RESPONSES,
    BLOG_DELETE_RESPONSES,
    LIKE_RESPONSES,
    LIKE_STATUS_RESPONSES,
)
from app.services.blog import (
    create_blog,
    delete_blog_by_id,
    get_all_blogs,
    get_blog_by_id,
    get_blogs_byTags,
    update_blog,
    like_or_unlike,
    check_user_like_status,
    admin_list_all_blogs,
    admin_delete_blog,
    admin_set_blog_visibility,
)
from app.services.auth_provider import get_all_users, get_user_by_id
from app.services.status import (
    get_comprehensive_health_check,
    get_request_headers_debug,
    get_auth_debug_info,
    get_system_info,
    is_debug_endpoint_enabled,
)
from app.core.security import get_current_user_id, require_admin

router = APIRouter()


# ---------- Health & ping ----------

@router.get("/ping", tags=["Health"], summary="Ping the service to check if it's alive")
async def ping():
    return {"message": "Pong. Hey I am alive!"}


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Blog Service Health Check",
    responses=HEALTH_CHECK_RESPONSES,
)
async def blog_service_health():
    health_result = await get_comprehensive_health_check()
    health_response = health_result["health_response"]
    status_code = health_result["status_code"]
    if status_code != 200:
        response = Response()
        response.status_code = status_code
    return health_response


# ---------- Debug endpoints (dev only) ----------

@router.get(
    "/debug/auth-users",
    response_model=List[AuthUserProfile],
    tags=["Debug"],
    summary="Get all auth users",
    responses=AUTH_PROVIDER_USERS_LIST_RESPONSES,
)
async def getAllUsers():
    if not is_debug_endpoint_enabled():
        return []
    return await get_all_users()


@router.get(
    "/debug/auth-users/{user_id}",
    response_model=AuthUserProfile,
    tags=["Debug"],
    summary="Get auth user by ID",
    responses=AUTH_PROVIDER_USER_RESPONSES,
)
async def getUserByID(user_id: str):
    return await get_user_by_id(user_id)


@router.get("/debug/headers", tags=["Debug"], summary="Get all request headers for debugging")
async def get_request_headers(request: Request):
    if not is_debug_endpoint_enabled():
        return {"error": "Debug endpoints are disabled in this environment"}
    return await get_request_headers_debug(request)


@router.get("/debug/auth-info", tags=["Debug"], summary="Get authentication info from headers")
async def get_auth_info(request: Request, current_user_id: str = Depends(get_current_user_id)):
    if not is_debug_endpoint_enabled():
        return {"error": "Debug endpoints are disabled in this environment"}
    return await get_auth_debug_info(request, current_user_id)


@router.get("/debug/system-info", tags=["Debug"], summary="Get system information")
async def get_system_information():
    if not is_debug_endpoint_enabled():
        return {"error": "Debug endpoints are disabled in this environment"}
    return await get_system_info()


# ---------- Public blog reads ----------

@router.get(
    "/public/blogs",
    response_model=PaginatedBlogList,
    tags=["Blog", "Unauthenticated"],
    summary="Get all public (visible) blogs, paginated",
    responses=BLOGS_LIST_RESPONSES,
)
async def getAllBlogs(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
):
    return await get_all_blogs(visible_only=True, page=page, limit=limit)


@router.get(
    "/public/blogsByTags",
    response_model=List[AllBlogsBlogPost],
    tags=["Blog", "Unauthenticated"],
    summary="Get blogs by tags",
    responses=BLOGS_BY_TAGS_RESPONSES,
)
async def Blogs_By_tags(tags: List[str] = Query(..., description="List of tags")):
    return await get_blogs_byTags(tags)


@router.get(
    "/public/blog/{blog_id}",
    response_model=BlogPostWithUserData,
    tags=["Blog", "Unauthenticated"],
    summary="Get Blog by ID",
    responses=BLOG_GET_RESPONSES,
)
async def get_blog_by_blog_id(blog_id: str):
    return await get_blog_by_id(blog_id)


# ---------- Authenticated blog writes (own posts) ----------

@router.post(
    "/createblog",
    response_model=BlogPostWithUserData,
    tags=["Blog", "Authenticated"],
    summary="Create a new blog post",
    status_code=status.HTTP_201_CREATED,
    responses=BLOG_CREATE_RESPONSES,
)
async def createBlog(blog: BlogPostCreate, current_user_id: str = Depends(get_current_user_id)):
    return await create_blog(blog, current_user_id)


@router.put(
    "/updateblog/{id}",
    response_model=BlogPostWithUserData,
    tags=["Blog", "Authenticated"],
    summary="Update an existing blog post",
    responses=BLOG_UPDATE_RESPONSES,
)
async def updateBlog(id: str, blog: BlogPostUpdate, current_user_id: str = Depends(get_current_user_id)):
    return await update_blog(id, blog, current_user_id)


@router.delete(
    "/blogs/{id}",
    response_model=BlogPostWithUserData,
    tags=["Blog", "Authenticated"],
    summary="Delete a blog post by ID (own posts only)",
    responses=BLOG_DELETE_RESPONSES,
)
async def deleteBlog(id: str, current_user_id: str = Depends(get_current_user_id)):
    return await delete_blog_by_id(id, current_user_id)


# ---------- Likes ----------

@router.post(
    "/blog/{blog_id}/like",
    response_model=LikeResponse,
    tags=["Blog", "Authenticated"],
    summary="Like or unlike a blog post",
    responses=LIKE_RESPONSES,
)
async def likeUnlikeBlog(
    blog_id: str, like_request: LikeRequest, current_user_id: str = Depends(get_current_user_id)
):
    return await like_or_unlike(blog_id, current_user_id, like_request.like_value)


@router.get(
    "/blog/{blog_id}/like-status",
    response_model=LikeStatusResponse,
    tags=["Blog", "Authenticated"],
    summary="Check if user has liked a blog post",
    responses=LIKE_STATUS_RESPONSES,
)
async def getUserLikeStatus(blog_id: str, current_user_id: str = Depends(get_current_user_id)):
    return await check_user_like_status(blog_id, current_user_id)


# ---------- Admin moderation ----------

@router.get(
    "/admin/blogs",
    response_model=List[AllBlogsBlogPost],
    tags=["Blog-Admin", "Authenticated"],
    summary="List all blogs (admin moderation view)",
)
async def admin_list_blogs(
    status_filter: Optional[str] = Query("all", description="visible|hidden|all"),
    admin: dict = Depends(require_admin),
):
    """Return every blog (including hidden) for moderation. Admin only."""
    return await admin_list_all_blogs(status_filter or "all")


@router.delete(
    "/admin/blog/{id}",
    response_model=BlogPostWithUserData,
    tags=["Blog-Admin", "Authenticated"],
    summary="Admin override delete (any blog, regardless of owner)",
)
async def admin_delete_blog_endpoint(id: str, admin: dict = Depends(require_admin)):
    return await admin_delete_blog(id)


@router.patch(
    "/admin/blog/{id}/visibility",
    response_model=BlogPostWithUserData,
    tags=["Blog-Admin", "Authenticated"],
    summary="Admin: set blog visibility (hide spam/inappropriate posts)",
)
async def admin_visibility_endpoint(
    id: str,
    visibility: bool,
    admin: dict = Depends(require_admin),
):
    return await admin_set_blog_visibility(id, visibility)
