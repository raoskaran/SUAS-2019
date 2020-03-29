"""Views middleware."""

import logging
import time

logger = logging.getLogger(__name__)


class LoggingMiddleware(object):
    """Logging middleware for custom request/response logging."""

    def process_request(self, request):
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        delta_time = 'Unknown Runtime'
        if hasattr(request, 'start_time'):
            delta_time = '%.4fs' % (time.time() - request.start_time)

        req_logger = None
        if response.status_code < 400:
            req_logger = logger.info
        elif response.status_code < 500:
            req_logger = logger.warning
        else:
            req_logger = logger.error

        req_logger('[%d] %s (%s)\n>>>\n%s\n===\n%s\n<<<', response.status_code,
                   request.get_full_path(), delta_time,
                   str(request), str(response))

        return response
