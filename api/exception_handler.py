"""
Custom Exception Handler for Django REST Framework
Ensures all API responses follow the envelope format: {ok, data, error}
"""
import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    APIException
)

logger = logging.getLogger(__name__)


def api_response(ok=True, data=None, error=None):
    """Standard API response envelope"""
    return {'ok': ok, 'data': data, 'error': error}


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns envelope format for all errors
    
    Requirements: 9.1, 12.1, 12.2, 12.3, 12.4
    """
    # Call DRF's default exception handler first
    response = drf_exception_handler(exc, context)
    
    # If DRF handled it, format the response
    if response is not None:
        error_data = None
        error_message = None
        
        # Handle validation errors (400)
        if isinstance(exc, ValidationError):
            if isinstance(response.data, dict):
                # Field-level validation errors
                error_data = response.data
                error_message = "Validation error"
            elif isinstance(response.data, list):
                # Non-field errors
                error_message = ' '.join(str(e) for e in response.data)
            else:
                error_message = str(response.data)
        
        # Handle authentication errors (401)
        elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            error_message = str(exc.detail) if hasattr(exc, 'detail') else "Authentication required"
        
        # Handle permission errors (403)
        elif isinstance(exc, PermissionDenied):
            error_message = str(exc.detail) if hasattr(exc, 'detail') else "Permission denied"
        
        # Handle not found errors (404)
        elif isinstance(exc, NotFound):
            error_message = str(exc.detail) if hasattr(exc, 'detail') else "Resource not found"
        
        # Handle other API exceptions
        elif isinstance(exc, APIException):
            error_message = str(
exc.detail) if hasattr(exc, 'detail') else str(exc)
        
        # Default error message
        else:
            error_message = "An error occurred"
        
        # Return envelope format
        response.data = api_response(
            ok=False,
            data=None,
            error=error_data if error_data else error_message
        )
        
        return response
    
    # Handle Django exceptions that DRF didn't catch
    
    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        logger.warning(f"Django ValidationError: {exc}")
        return Response(
            api_response(ok=False, error=str(exc)),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle Django Http404
    if isinstance(exc, Http404):
        logger.warning(f"Http404: {exc}")
        return Response(
            api_response(ok=False, error="Resource not found"),
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Handle unexpected exceptions (500)
    logger.error(
        f"Unexpected error in {context.get('view', 'unknown view'
)}",
        exc_info=exc
    )
    
    return Response(
        api_response(
            ok=False,
            error="Internal server error"
        ),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
