# performance_monitoring.py - Clean, professional version
import time
import logging
from django.db import connection
from functools import wraps

# Monitor query performance
def monitor_queries(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_queries = len(connection.queries)
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        query_count = len(connection.queries) - start_queries
        execution_time = time.time() - start_time
        
        logger = logging.getLogger('performance')
        logger.info(f"{func.__name__}: {query_count} queries, {execution_time:.3f}s")
        
        return result
    return wrapper

# Add performance metrics to API
class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        start_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        query_count = len(connection.queries) - start_queries
        execution_time = time.time() - start_time
        
        response['X-Query-Count'] = str(query_count)
        response['X-Execution-Time'] = f"{execution_time:.3f}"
        
        return response