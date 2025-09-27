# chats/urls.py
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import ConversationViewSet, MessageViewSet
from .auth import (
    CustomTokenObtainPairView,
    register_user,
    logout_user,
    user_profile,
    update_profile,
    change_password
)

# Create a custom nested router class
class NestedDefaultRouter(routers.DefaultRouter):
    """
    Custom router that creates nested routes for messages within conversations.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = '/?'

# Create the main router using DefaultRouter
router = routers.DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

# Create nested router instance
nested_router = NestedDefaultRouter()

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/register/', register_user, name='auth_register'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/logout/', logout_user, name='auth_logout'),
    
    # User profile endpoints
    path('auth/profile/', user_profile, name='user_profile'),
    path('auth/profile/update/', update_profile, name='update_profile'),
    path('auth/change-password/', change_password, name='change_password'),
    
    # Main API routes
    path('', include(router.urls)),
    
    # Add nested routes manually for messages within conversations
    path('conversations/<uuid:conversation_pk>/messages/',
         MessageViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='conversation-messages-list'),
    path('conversations/<uuid:conversation_pk>/messages/<uuid:pk>/',
         MessageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='conversation-messages-detail'),
]

# This creates the following endpoints:
#
# Authentication endpoints:
# POST   /auth/login/                             - Login and get JWT tokens
# POST   /auth/register/                          - Register new user
# POST   /auth/token/refresh/                     - Refresh JWT token
# POST   /auth/token/verify/                      - Verify JWT token
# POST   /auth/logout/                            - Logout (blacklist refresh token)
# GET    /auth/profile/                           - Get current user profile
# PUT    /auth/profile/update/                    - Update user profile
# PATCH  /auth/profile/update/                    - Partially update user profile
# POST   /auth/change-password/                   - Change user password
#
# Conversation endpoints:
# GET    /conversations/                          - List all conversations
# POST   /conversations/                          - Create new conversation
# GET    /conversations/{id}/                     - Get conversation details
# PUT    /conversations/{id}/                     - Update conversation
# PATCH  /conversations/{id}/                     - Partially update conversation
# DELETE /conversations/{id}/                     - Delete conversation
# POST   /conversations/{id}/add_participant/     - Add participant to conversation
# POST   /conversations/{id}/remove_participant/  - Remove participant from conversation
#
# Message endpoints:
# GET    /messages/                               - List all messages
# POST   /messages/                               - Send new message
# GET    /messages/{id}/                          - Get message details
# PUT    /messages/{id}/                          - Update message
# PATCH  /messages/{id}/                          - Partially update message
# DELETE /messages/{id}/                          - Delete message
# POST   /messages/{id}/mark_read/                - Mark message as read
# GET    /messages/unread/                        - Get unread messages for user
#
# Nested message endpoints:
# GET    /conversations/{id}/messages/            - List messages in conversation
# POST   /conversations/{id}/messages/            - Send message to conversation
# GET    /conversations/{id}/messages/{msg_id}/   - Get specific message in conversation
# PUT    /conversations/{id}/messages/{msg_id}/   - Update message in conversation
# PATCH  /conversations/{id}/messages/{msg_id}/   - Partially update message in conversation
# DELETE /conversations/{id}/messages/{msg_id}/   - Delete message in conversation