"""
Unit Tests for API Response Helper

Tests standardized API response formatting.
"""

import pytest
from utils.api_response import APIResponse, timed_endpoint, handle_api_errors


class TestAPIResponse:
    """Tests for APIResponse class."""
    
    def test_success_response(self):
        """Test creation of successful response."""
        data = {'key': 'value', 'number': 42}
        response = APIResponse.success(data=data)
        
        assert response['success'] is True
        assert response['data'] == data
        assert response['error'] is None
        assert 'timestamp' in response
        assert 'meta' in response
        assert response['meta']['version'] == '1.0'
    
    def test_success_response_with_message(self):
        """Test successful response with message."""
        response = APIResponse.success(data={'id': 123}, message='Created successfully')
        
        assert response['success'] is True
        assert response['message'] == 'Created successfully'
    
    def test_error_response(self):
        """Test creation of error response."""
        error_msg = 'Something went wrong'
        response, status_code = APIResponse.error(error_msg)
        
        assert response['success'] is False
        assert response['data'] is None
        assert response['error']['message'] == error_msg
        assert status_code == 400
        assert 'timestamp' in response
    
    def test_error_response_with_code(self):
        """Test error response with error code."""
        response, status_code = APIResponse.error(
            'Not found',
            error_code='NOT_FOUND',
            status_code=404
        )
        
        assert response['error']['code'] == 'NOT_FOUND'
        assert status_code == 404
    
    def test_paginated_response(self):
        """Test creation of paginated response."""
        data = [{'id': i} for i in range(10)]
        response = APIResponse.paginated(
            data=data,
            page=2,
            per_page=10,
            total=45
        )
        
        assert response['success'] is True
        assert len(response['data']) == 10
        assert response['meta']['pagination']['page'] == 2
        assert response['meta']['pagination']['per_page'] == 10
        assert response['meta']['pagination']['total'] == 45
        assert response['meta']['pagination']['total_pages'] == 5
        assert response['meta']['pagination']['has_next'] is True
        assert response['meta']['pagination']['has_prev'] is True
    
    def test_paginated_first_page(self):
        """Test paginated response for first page."""
        response = APIResponse.paginated(
            data=[],
            page=1,
            per_page=10,
            total=5
        )
        
        assert response['meta']['pagination']['has_prev'] is False
        assert response['meta']['pagination']['has_next'] is False
    
    def test_timed_endpoint_decorator(self):
        """Test timed_endpoint decorator adds execution time."""
        @timed_endpoint
        def sample_endpoint():
            return APIResponse.success(data={'test': True})
        
        response = sample_endpoint()
        
        assert 'execution_time_ms' in response['meta']
        assert isinstance(response['meta']['execution_time_ms'], float)
        assert response['meta']['execution_time_ms'] >= 0
    
    def test_handle_api_errors_decorator(self):
        """Test handle_api_errors decorator catches exceptions."""
        @handle_api_errors
        def failing_endpoint():
            raise ValueError("Invalid input")
        
        response, status_code = failing_endpoint()
        
        assert response['success'] is False
        assert 'Invalid input' in response['error']['message']
        assert status_code == 400
    
    def test_handle_api_errors_permission_error(self):
        """Test handle_api_errors catches permission errors."""
        @handle_api_errors
        def forbidden_endpoint():
            raise PermissionError("Access denied")
        
        response, status_code = forbidden_endpoint()
        
        assert status_code == 403
        assert response['error']['code'] == 'PERMISSION_DENIED'
    
    def test_handle_api_errors_not_found(self):
        """Test handle_api_errors catches FileNotFoundError."""
        @handle_api_errors
        def not_found_endpoint():
            raise FileNotFoundError("Resource not found")
        
        response, status_code = not_found_endpoint()
        
        assert status_code == 404
        assert response['error']['code'] == 'NOT_FOUND'
    
    def test_handle_api_errors_generic_exception(self):
        """Test handle_api_errors catches generic exceptions."""
        @handle_api_errors
        def error_endpoint():
            raise RuntimeError("Unexpected error")
        
        response, status_code = error_endpoint()
        
        assert status_code == 500
        assert response['error']['code'] == 'INTERNAL_ERROR'
        assert 'Internal server error' in response['error']['message']
