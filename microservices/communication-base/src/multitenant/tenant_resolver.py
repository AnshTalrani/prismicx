"""
Tenant Resolver Module

This module provides utilities for resolving tenant information from various sources
such as headers, query parameters, path parameters, etc.
"""

import logging
import re
from typing import Optional, Dict, Any, List, Union, Pattern
from fastapi import Request

logger = logging.getLogger(__name__)


class TenantResolver:
    """
    Resolver for extracting tenant information from various sources.
    
    This class provides methods to extract tenant identifiers from HTTP requests,
    URLs, and other sources.
    """
    
    def __init__(
        self,
        tenant_header: str = "X-Tenant-ID",
        domain_tenant_pattern: Optional[Union[str, Pattern]] = None,
        subdomain_tenant_pattern: Optional[Union[str, Pattern]] = None
    ):
        """
        Initialize the tenant resolver.
        
        Args:
            tenant_header: The HTTP header name for tenant ID.
            domain_tenant_pattern: Pattern for extracting tenant ID from domain.
            subdomain_tenant_pattern: Pattern for extracting tenant ID from subdomain.
        """
        self.tenant_header = tenant_header
        
        # Compile regex patterns if provided as strings
        if isinstance(domain_tenant_pattern, str):
            self.domain_tenant_pattern = re.compile(domain_tenant_pattern)
        else:
            self.domain_tenant_pattern = domain_tenant_pattern
            
        if isinstance(subdomain_tenant_pattern, str):
            self.subdomain_tenant_pattern = re.compile(subdomain_tenant_pattern)
        else:
            self.subdomain_tenant_pattern = subdomain_tenant_pattern
    
    def resolve_from_request(self, request: Request) -> Optional[str]:
        """
        Resolve tenant ID from an HTTP request.
        
        This method tries multiple sources in the following order:
        1. HTTP header
        2. Query parameter
        3. Path parameter
        4. Host (domain/subdomain)
        
        Args:
            request: The HTTP request.
            
        Returns:
            The resolved tenant ID or None if not found.
        """
        tenant_id = self.resolve_from_header(request)
        if tenant_id:
            return tenant_id
            
        tenant_id = self.resolve_from_query(request)
        if tenant_id:
            return tenant_id
            
        tenant_id = self.resolve_from_path(request)
        if tenant_id:
            return tenant_id
            
        tenant_id = self.resolve_from_host(request)
        if tenant_id:
            return tenant_id
            
        return None
    
    def resolve_from_header(self, request: Request) -> Optional[str]:
        """
        Resolve tenant ID from HTTP header.
        
        Args:
            request: The HTTP request.
            
        Returns:
            The tenant ID from header or None if not found.
        """
        return request.headers.get(self.tenant_header)
    
    def resolve_from_query(self, request: Request) -> Optional[str]:
        """
        Resolve tenant ID from query parameter.
        
        Args:
            request: The HTTP request.
            
        Returns:
            The tenant ID from query parameter or None if not found.
        """
        return request.query_params.get("tenant_id")
    
    def resolve_from_path(self, request: Request) -> Optional[str]:
        """
        Resolve tenant ID from path parameter.
        
        Args:
            request: The HTTP request.
            
        Returns:
            The tenant ID from path parameter or None if not found.
        """
        path_params = getattr(request, "path_params", {})
        return path_params.get("tenant_id")
    
    def resolve_from_host(self, request: Request) -> Optional[str]:
        """
        Resolve tenant ID from host (domain/subdomain).
        
        Args:
            request: The HTTP request.
            
        Returns:
            The tenant ID from host or None if not found.
        """
        host = request.headers.get("host", "")
        
        # Try subdomain pattern first
        if self.subdomain_tenant_pattern:
            match = self.subdomain_tenant_pattern.match(host)
            if match and match.groups():
                return match.group(1)
        
        # Then try domain pattern
        if self.domain_tenant_pattern:
            match = self.domain_tenant_pattern.match(host)
            if match and match.groups():
                return match.group(1)
                
        return None
    
    def resolve_from_url(self, url: str) -> Optional[str]:
        """
        Resolve tenant ID from URL.
        
        Args:
            url: The URL to extract tenant ID from.
            
        Returns:
            The tenant ID from URL or None if not found.
        """
        # Extract tenant from path parameter
        path_pattern = re.compile(r'/tenants/([^/]+)')
        match = path_pattern.search(url)
        if match:
            return match.group(1)
            
        # Extract tenant from query parameter
        query_pattern = re.compile(r'tenant_id=([^&]+)')
        match = query_pattern.search(url)
        if match:
            return match.group(1)
            
        # Extract tenant from domain/subdomain
        if self.domain_tenant_pattern or self.subdomain_tenant_pattern:
            # Extract host from URL
            host_pattern = re.compile(r'https?://([^/]+)')
            host_match = host_pattern.search(url)
            if not host_match:
                return None
                
            host = host_match.group(1)
            
            # Try subdomain pattern
            if self.subdomain_tenant_pattern:
                match = self.subdomain_tenant_pattern.match(host)
                if match and match.groups():
                    return match.group(1)
            
            # Try domain pattern
            if self.domain_tenant_pattern:
                match = self.domain_tenant_pattern.match(host)
                if match and match.groups():
                    return match.group(1)
                    
        return None


# Default subdomain pattern: {tenant}.example.com
DEFAULT_SUBDOMAIN_PATTERN = re.compile(r'^([^.]+)\.')

# Default resolver instance
_tenant_resolver: Optional[TenantResolver] = None


def get_tenant_resolver() -> TenantResolver:
    """
    Get the singleton tenant resolver instance.
    
    Returns:
        The tenant resolver instance.
    """
    global _tenant_resolver
    if _tenant_resolver is None:
        _tenant_resolver = TenantResolver(
            subdomain_tenant_pattern=DEFAULT_SUBDOMAIN_PATTERN
        )
    return _tenant_resolver 