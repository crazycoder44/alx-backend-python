import time
from django.http import HttpResponseForbidden
from datetime import datetime

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        user = request.user if request.user.is_authenticated else "Anonymous"
        log_message = f"[{datetime.now()}] User: {user} - Path: {request.path}\n"

        # Log the message to a file
        with open("requests.log", "a") as log_file:
            log_file.write(log_message)

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
    
class RestrictAccessByTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Define the allowed time range (9 AM to 6 PM)
        start_hour = 9
        end_hour = 18
        current_hour = datetime.now().hour

        # Check if the current hour is outside the allowed range
        if not (start_hour <= current_hour < end_hour):
            return HttpResponseForbidden("Access is restricted outside of 9 AM to 6 PM.")

        # If within the allowed time, proceed as normal
        response = self.get_response(request)
        return response  

class OffensiveLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # This dictionary will store IP addresses and their request timestamps
        self.requests = {}

    def __call__(self, request):
        # We only want to rate-limit POST requests for sending messages
        if request.method == 'POST' and request.path.endswith('/messages/'):
            ip_address = request.META.get("REMOTE_ADDR")
            current_time = time.time()

            # Get the list of timestamps for this IP, or an empty list if it's new
            request_times = self.requests.get(ip_address, [])

            # Keep only the timestamps from the last 60 seconds
            valid_times = [t for t in request_times if current_time - t < 60]

            # If the user has made 5 or more requests in the last minute, block them
            if len(valid_times) >= 5:
                return HttpResponseForbidden("Rate limit exceeded. Please try again in a minute.")

            # Add the current timestamp and update the dictionary
            valid_times.append(current_time)
            self.requests[ip_address] = valid_times

        # Allow the request to continue
        response = self.get_response(request)
        return response 

class RolepermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        # First, check if the user is even logged in.
        # If not, let other parts of the app (like DRF permissions) handle it.
        if user.is_authenticated:
            # Check if the user's role is NOT one of the allowed roles.
            # Based on your User model, we'll allow ADMIN and HOST.
            if user.role not in ['admin', 'host', 'guest']:
                return HttpResponseForbidden("You do not have the required role to access this page.")

        # If the user is anonymous or has the correct role, let the request continue.
        response = self.get_response(request)
        return response         