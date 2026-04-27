"""
Status and debug service module.

This module contains services for:
- Health checks for various system components
- Debug utilities for header inspection
- System status monitoring
"""

import time
import os
import sys
from datetime import datetime
from typing import Dict, Any
from fastapi import Request
from app.schemas.blog import HealthCheckResponse, AuthProviderHealth, DatabaseHealth
from app.services.auth_provider import check_auth_provider_health
from app.services.blog import check_database_health


async def get_comprehensive_health_check() -> Dict[str, Any]:
    """
    Perform comprehensive health check for the blog service.
    
    Checks:
    - auth provider connectivity and authentication capability
    - MongoDB database connectivity and performance metrics
    - Overall service response time and status
    
    Returns detailed health information including:
    - Individual service status and response times  
    - Database metrics (blog counts, comment counts, etc.)
    - Authentication status
    - Overall service health assessment
    """
    start_time = time.time()
    
    try:
        auth_provider_health_raw = await check_auth_provider_health()
        auth_provider_health = AuthProviderHealth(**auth_provider_health_raw)
    except Exception as e:
        auth_provider_health = AuthProviderHealth(
            status="unhealthy",
            response_time_ms=None,
            service="supabase-auth", 
            authenticated=False,
            error=str(e)
        )
    
    try:
        database_health_raw = await check_database_health()
        database_health = DatabaseHealth(**database_health_raw)
    except Exception as e:
        database_health = DatabaseHealth(
            status="unhealthy",
            response_time_ms=None,
            service="mongodb",
            error=str(e),
            metrics=None
        )
    
    # Calculate overall response time
    overall_response_time = round((time.time() - start_time) * 1000, 2)
    
    # Determine overall health status
    auth_provider_healthy = auth_provider_health.status == "healthy"
    database_healthy = database_health.status == "healthy"
    
    if auth_provider_healthy and database_healthy:
        overall_status = "healthy"
        status_code = 200
    elif database_healthy:  # Database is critical, if it's healthy but auth provider isn't, we're degraded
        overall_status = "degraded"
        status_code = 503
    else:  # Database is unhealthy, service is unhealthy
        overall_status = "unhealthy"
        status_code = 503
    
    # Calculate uptime from actual service start time
    from app.core.service_tracker import get_uptime_info
    uptime_info = get_uptime_info()
    
    health_response = HealthCheckResponse(
        service="blog-service",
        status=overall_status,
        timestamp=datetime.utcnow(),
        service_start_time=uptime_info.get("service_start_time"),
        uptime_seconds=uptime_info.get("uptime_seconds"),
        uptime_formatted=uptime_info.get("uptime_formatted"),
        timezone=uptime_info.get("timezone", "GMT+5:30 (IST)"),
        auth_provider=auth_provider_health,
        database=database_health,
        overall_response_time_ms=overall_response_time
    )
    
    return {
        "health_response": health_response,
        "status_code": status_code
    }


async def get_request_headers_debug(request: Request) -> Dict[str, Any]:
    """
    Debug utility to inspect all incoming request headers.
    Useful for verifying incoming authentication headers.
    
    Args:
        request: FastAPI Request object containing headers
        
    Returns:
        Dictionary containing:
        - All headers
        - Important authentication-related headers highlighted
        - Header count and other metadata
    """
    headers = dict(request.headers)
    
    # Highlight important authentication-related headers
    auth_headers = {
        "authorization": headers.get("authorization"),
        "x-forwarded-for": headers.get("x-forwarded-for"),
        "x-real-ip": headers.get("x-real-ip"),
        "x-forwarded-proto": headers.get("x-forwarded-proto"),
        "x-forwarded-host": headers.get("x-forwarded-host"),
        "host": headers.get("host"),
        "user-agent": headers.get("user-agent"),
    }
    
    # Remove None values for cleaner output
    auth_headers = {k: v for k, v in auth_headers.items() if v is not None}
    
    return {
        "message": "Request headers debug information",
        "timestamp": datetime.utcnow().isoformat(),
        "important_auth_headers": auth_headers,
        "all_headers": headers,
        "headers_count": len(headers),
        "nginx_headers_present": {
            "x_forwarded_for_present": "x-forwarded-for" in headers,
            "x_real_ip_present": "x-real-ip" in headers,
            "authorization_present": "authorization" in headers,
        }
    }


async def get_auth_debug_info(request: Request, current_user_id: str) -> Dict[str, Any]:
    """
    Debug utility to verify authentication flow and user ID extraction.
    
    Args:
        request: FastAPI Request object containing headers
        current_user_id: Processed user ID from the security dependency
        
    Returns:
        Dictionary containing:
        - Processed current_user_id from dependency
        - Authorization presence
        - Authentication flow validation
    """
    auth_header = request.headers.get("authorization")
    
    # Additional debugging info
    debugging_info = {
        "header_case_variations": {
            "authorization": request.headers.get("authorization"),
            "Authorization": request.headers.get("Authorization"),
        },
        "all_x_headers": {k: v for k, v in request.headers.items() if k.lower().startswith("x-")},
    }
    
    return {
        "message": "Authentication debug information",
        "timestamp": datetime.utcnow().isoformat(),
        "processed_current_user_id": current_user_id,
        "authorization_header_present": auth_header is not None,
        "authorization_header_type": auth_header.split(" ")[0] if auth_header else None,
        "user_authenticated": current_user_id is not None,
        "debugging_info": debugging_info
    }


async def get_system_info() -> Dict[str, Any]:
    """
    Get general system information for debugging purposes.
    
    Returns:
        Dictionary containing system and environment information
    """
    from app.core.service_tracker import get_uptime_info
    
    uptime_info = get_uptime_info()
    
    return {
        "message": "System information",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "service_info": {
            "name": "blog-service",
            "version": os.getenv("SERVICE_VERSION", "unknown"),
            "uptime": uptime_info,
        },
        "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
        "python_version": sys.version,
    }


def is_debug_endpoint_enabled() -> bool:
    """
    Check if debug endpoints should be enabled based on environment.
    
    Returns:
        True if debug endpoints should be enabled, False otherwise
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    debug_enabled = os.getenv("DEBUG_ENDPOINTS_ENABLED", "true").lower() == "true"
    
    # Enable debug endpoints in development and staging, or if explicitly enabled
    return environment in ["development", "staging", "dev", "test"] or debug_enabled
