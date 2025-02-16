# bsi_project/middleware.py
from django.http import Http404
from django.shortcuts import render
from django.urls import resolve

class InvalidUrlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request URL matches any valid URL pattern
        try:
            resolve(request.path)  # Try to resolve the URL
            response = self.get_response(request)  # Continue processing if valid
        except Http404:
            # If Http404 is raised (invalid URL), render the custom 404 page
            return render(request, '404.html', status=404)
        return response
