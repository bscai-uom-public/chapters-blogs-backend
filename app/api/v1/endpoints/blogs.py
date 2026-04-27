from typing import List, Union
from fastapi import APIRouter, Query, Depends, status, Request, Response
from pydantic import BaseModel
from app.schemas.blog import BlogPost, Comment, Reply, AllBlogsBlogPost, BlogPostWithUserData, CommentBase, ReplyBase, UpdateTextRequest, LikeRequest, LikeResponse, LikeStatusResponse, BlogPostCreate, BlogPostUpdate, CommentCreate, ReplyCreate, HealthCheckResponse
from app.schemas.blog import AuthUserProfile
from app.schemas.responses import (
    HEALTH_CHECK_RESPONSES, AUTH_PROVIDER_USERS_LIST_RESPONSES, AUTH_PROVIDER_USER_RESPONSES,
    BLOGS_LIST_RESPONSES, BLOGS_BY_TAGS_RESPONSES, BLOG_GET_RESPONSES, 
    BLOG_CREATE_RESPONSES, BLOG_UPDATE_RESPONSES, BLOG_DELETE_RESPONSES,
    COMMENTS_LIST_RESPONSES, COMMENT_CREATE_RESPONSES, REPLY_CREATE_RESPONSES,
    COMMENT_UPDATE_RESPONSES, COMMENT_DELETE_RESPONSES, LIKE_RESPONSES, LIKE_STATUS_RESPONSES
)
from app.services.blog import create_blog, delete_blog_by_id, delete_comment_reply, fetch_comments_and_replies, get_all_blogs, get_blog_by_id, get_blogs_byTags, reply_comment, update_Comment_Reply, update_blog, write_comment, like_or_unlike, check_user_like_status
from app.services.auth_provider import get_all_users, get_all_users_safely, get_user_by_id, get_user_by_id_safely
from app.services.status import get_comprehensive_health_check, get_request_headers_debug, get_auth_debug_info, get_system_info, is_debug_endpoint_enabled
from app.core.security import get_current_user_id

router = APIRouter()

# Schema for token request
class TokenRequest(BaseModel):
    username: str
    password: str

@router.get("/ping", tags=["Health"], summary="Ping the service to check if it's alive")
async def ping():
    return {"message": "Pong. Hey I am alive!"}

# Health check endpoint for blog service
@router.get("/health", response_model=HealthCheckResponse, tags=["Health"], summary="Blog Service Health Check", responses=HEALTH_CHECK_RESPONSES)
async def blog_service_health():
    """
    Comprehensive health check for the blog service.
    
    Checks:
    - auth provider service connectivity and authentication capability
    - MongoDB database connectivity and performance metrics
    - Overall service response time and status
    
    Returns detailed health information including:
    - Individual service status and response times  
    - Database metrics (blog counts, comment counts, etc.)
    - Authentication status
    - Overall service health assessment
    """
    health_result = await get_comprehensive_health_check()
    health_response = health_result["health_response"]
    status_code = health_result["status_code"]
    
    # Set response status code based on health
    if status_code != 200:
        response = Response()
        response.status_code = status_code
        return health_response
    
    return health_response

# NOTE: DO NOT turn these auth provider debug endpoints on in production. These can leak user information !!
# ============================================
@router.get("/debug/auth-users", response_model=List[AuthUserProfile], tags=["Debug"], summary="Get all auth users", responses=AUTH_PROVIDER_USERS_LIST_RESPONSES)
async def getAllUsers():
    # Do not use the safe functions here. We want to check for errors when debugging. 
    return await get_all_users()


@router.get("/debug/auth-users/{user_id}", response_model=AuthUserProfile, tags=["Debug"], summary="Get auth user by ID", responses=AUTH_PROVIDER_USER_RESPONSES)
async def getUserByID(user_id: str):
    # Do not use the safe functions here. We want to check for errors when debugging.
    return await get_user_by_id(user_id)

# Debug endpoints for header inspection and authentication verification
# NOTE: These endpoints should be disabled in production for security reasons

@router.get("/debug/headers", tags=["Debug"], summary="Get all request headers for debugging")
async def get_request_headers(request: Request):
    """
    Debug endpoint to inspect all incoming request headers.
    Useful for verifying request auth headers in debug mode.
    
    Returns all headers including:
    - Authorization header
    - Forwarding headers
    - Other custom headers
    
    NOTE: This endpoint should be disabled in production for security reasons.
    """
    if not is_debug_endpoint_enabled():
        return {"error": "Debug endpoints are disabled in this environment"}
    
    return await get_request_headers_debug(request)


@router.get("/debug/auth-info", tags=["Debug"], summary="Get authentication info from headers")
async def get_auth_info(request: Request, current_user_id: str = Depends(get_current_user_id)):
    """
    Debug endpoint to verify authentication flow and user ID extraction.
    
    Shows:
    - Processed current_user_id from dependency
    - Authorization header presence
    - Authentication flow validation
    
    NOTE: This endpoint should be disabled in production for security reasons.
    """
    if not is_debug_endpoint_enabled():
        return {"error": "Debug endpoints are disabled in this environment"}
    
    return await get_auth_debug_info(request, current_user_id)


@router.get("/debug/system-info", tags=["Debug"], summary="Get system information")
async def get_system_information():
    """
    Debug endpoint to get general system information.
    
    Returns:
    - Environment information
    - Service uptime and version
    - System configuration
    
    NOTE: This endpoint should be disabled in production for security reasons.
    """
    if not is_debug_endpoint_enabled():
        return {"error": "Debug endpoints are disabled in this environment"}
    
    return await get_system_info()


@router.get("/debug/test-auth-with-bearer", tags=["Debug"], summary="Test authentication with Bearer token")
async def test_auth_with_bearer(current_user_id: str = Depends(get_current_user_id)):
    """
    Debug endpoint to test Bearer token authentication for Swagger UI testing.
    
    Instructions for Swagger testing:
    1. Get a valid Bearer token from Supabase Auth sign-in flow.
    
    2. Click the 'Authorize' button in Swagger UI (lock icon in top right)
    
    3. Paste the token in the Bearer token field as: <token_value>
    
    4. Try this endpoint first to verify the token works
    
    5. Then try authenticated endpoints like POST /createblog
    
    NOTE: This endpoint is for development/testing only. Remove in production.
    """
    if not is_debug_endpoint_enabled():
        return {"error": "Debug endpoints are disabled in this environment"}
    
    return {
        "success": True,
        "message": "Bearer token authentication successful",
        "user_id": current_user_id,
        "note": "Your Bearer token is valid. You can now use authenticated endpoints."
    }


@router.post("/debug/get-bearer-token", tags=["Debug"], summary="Get Bearer token (Deprecated for Supabase)")
async def get_bearer_token(token_request: TokenRequest):
    """
    Deprecated debug endpoint kept for compatibility during auth migration.
    
    WARNING: This endpoint is for development/testing ONLY!
    It accepts username and password in plain text - DO NOT USE IN PRODUCTION.
    
    NOTE: Remove this endpoint in production for security reasons.
    """
    if not is_debug_endpoint_enabled():
        return {"error": "Debug endpoints are disabled in this environment"}
    
    return {
        "success": False,
        "error": "Direct token minting from this backend is disabled after Supabase migration.",
        "status_code": 410,
        "debug_info": {
            "note": "Use Supabase Auth sign-in on the frontend to obtain access tokens."
        }
    }

# ============================================

# NOTE: All endpoints with `Authenticated` tag require valid bearer auth.

@router.get('/public/blogs', response_model=List[AllBlogsBlogPost], tags=["Blog", "Unauthenticated"], summary="Get all blogs", responses=BLOGS_LIST_RESPONSES)
async def getAllBlogs():
    return await get_all_blogs()

@router.get('/public/blogsByTags', response_model=List[AllBlogsBlogPost], tags=["Blog", "Unauthenticated"], summary="Get blogs by tags", responses=BLOGS_BY_TAGS_RESPONSES)
async def Blogs_By_tags(tags : List[str]=Query(..., description="List of tags")): #Query(..., description="List of tags") added to make get request correctly as it includes tag numbers
    return await get_blogs_byTags(tags)

@router.get("/public/blog/{blog_id}", response_model=BlogPostWithUserData ,tags=["Blog", "Unauthenticated"], summary="Get Blog by ID", responses=BLOG_GET_RESPONSES)
async def get_blog_by_blog_id(blog_id: str): #data type change from int to str
    blog = await get_blog_by_id(blog_id) #{"p_id": blog_id} => blog_id -function parameter error,parameter was not in format used in get_blog_by_id()
    return blog

@router.post('/createblog', response_model=BlogPostWithUserData, tags=["Blog", "Authenticated"], summary="Create a new blog post", status_code=status.HTTP_201_CREATED, responses=BLOG_CREATE_RESPONSES)
async def createBlog(blog: BlogPostCreate, current_user_id: str = Depends(get_current_user_id)):
    # setting the user_id from the server-side. No need to pass it from the client side. (significantly more secure)
    return await create_blog(blog, current_user_id)

@router.put('/updateblog/{id}', response_model=BlogPostWithUserData, tags=["Blog", "Authenticated"], summary="Update an existing blog post", responses=BLOG_UPDATE_RESPONSES)
async def updateBlog(id: str, blog: BlogPostUpdate, current_user_id: str = Depends(get_current_user_id)):
    return await update_blog(id, blog, current_user_id)


@router.delete('/blogs/{id}', response_model=BlogPostWithUserData, tags=["Blog", "Authenticated"], summary="Delete a blog post by ID", responses=BLOG_DELETE_RESPONSES)
async def deleteBlog(id: str, current_user_id: str = Depends(get_current_user_id)):
    return await delete_blog_by_id(id, current_user_id)

@router.get('/public/blog/{id}/comments', response_model=List[CommentBase], tags=["Blog-Comment", "Unauthenticated"], summary="Get all comments and replies for a blog post", responses=COMMENTS_LIST_RESPONSES)
async def get_comments_and_replies(id:str):
    return await fetch_comments_and_replies(id)

@router.post('/write-comment', response_model=CommentBase, tags=["Blog-Comment", "Authenticated"], summary="Write a comment on a blog post", status_code=status.HTTP_201_CREATED, responses=COMMENT_CREATE_RESPONSES)
async def writeComment(comment: CommentCreate, current_user_id: str = Depends(get_current_user_id)):
    return await write_comment(comment, current_user_id)

@router.post('/reply-comment', response_model=ReplyBase, tags=["Blog-Comment", "Authenticated"], summary="Reply to a comment on a blog post", status_code=status.HTTP_201_CREATED, responses=REPLY_CREATE_RESPONSES)
async def replyComment(reply: ReplyCreate, current_user_id: str = Depends(get_current_user_id)):
    return await reply_comment(reply, current_user_id)

@router.put('/edit-comment-reply/{id}', response_model=Union[CommentBase, ReplyBase], tags=["Blog-Comment", "Authenticated"], summary="Update a comment or reply", responses=COMMENT_UPDATE_RESPONSES)
async def updateCommentReply(id: str, request: UpdateTextRequest, current_user_id: str = Depends(get_current_user_id)):
    # for the simple text update, we have to use a schema, otherwise FastAPI defaults to considering the `request` in string as a query param
    return await update_Comment_Reply(id, request.text, current_user_id)

@router.delete('/delete-comment-reply/{id}', tags=["Blog-Comment", "Authenticated"], summary="Delete a comment or reply", responses=COMMENT_DELETE_RESPONSES)
async def deleteCommentReply(id: str, current_user_id: str = Depends(get_current_user_id)):
    return await delete_comment_reply(id, current_user_id)

@router.post('/blog/{blog_id}/like', response_model=LikeResponse, tags=["Blog", "Authenticated"], summary="Like or unlike a blog post", responses=LIKE_RESPONSES)
async def likeUnlikeBlog(blog_id: str, like_request: LikeRequest, current_user_id: str = Depends(get_current_user_id)):
    """
    Like or unlike a blog post.
    - like_value: 0 to unlike, 1 to like

    NOTE: 0 & 1 used here so that in future if there will be capability to like more than once a blog
    (for example in Medium), API doesn't need to be changed.
    """
    return await like_or_unlike(blog_id, current_user_id, like_request.like_value)

@router.get('/blog/{blog_id}/like-status', response_model=LikeStatusResponse, tags=["Blog", "Authenticated"], summary="Check if user has liked a blog post", responses=LIKE_STATUS_RESPONSES)
async def getUserLikeStatus(blog_id: str, current_user_id: str = Depends(get_current_user_id)):
    """
    Check if the current user has liked a specific blog post.
    Returns like status, total likes count, and like details if applicable.
    """
    return await check_user_like_status(blog_id, current_user_id)
