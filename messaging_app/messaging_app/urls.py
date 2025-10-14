# messaging_app/urls.py
"""
URL configuration for messaging_app project.
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chats.urls')),  # Include the Chats app URLs under api/
    path('api-auth/', include('rest_framework.urls')),  # DRF api-auth URLs
]

# This creates the following URL structure:
#
# Admin:
# /admin/                                          - Django admin interface
#
# API Authentication:
# /api-auth/login/                                 - DRF login page
# /api-auth/logout/                                - DRF logout page
#
# Conversations API:
# /api/conversations/                              - List/Create conversations
# /api/conversations/{id}/                         - Retrieve/Update/Delete conversation
# /api/conversations/{id}/add_participant/         - Add participant to conversation
# /api/conversations/{id}/remove_participant/      - Remove participant from conversation
# /api/conversations/{id}/messages/                - List/Create messages in conversation (nested)
# /api/conversations/{id}/messages/{msg_id}/       - Retrieve/Update/Delete specific message in conversation
#
# Messages API:
# /api/messages/                                   - List/Create messages (all conversations)
# /api/messages/{id}/                              - Retrieve/Update/Delete message
# /api/messages/{id}/mark_read/                    - Mark message as read
# /api/messages/unread/                            - Get unread messages