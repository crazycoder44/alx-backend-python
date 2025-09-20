# chats/urls.py
from django.urls import path, include
from rest_framework import routers
from .views import ConversationViewSet, MessageViewSet

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
# Conversation endpoints:
# GET    /conversations/                           - List all conversations
# POST   /conversations/                           - Create new conversation
# GET    /conversations/{id}/                      - Get conversation details
# PUT    /conversations/{id}/                      - Update conversation
# PATCH  /conversations/{id}/                      - Partially update conversation
# DELETE /conversations/{id}/                      - Delete conversation
# POST   /conversations/{id}/add_participant/      - Add participant to conversation
# POST   /conversations/{id}/remove_participant/   - Remove participant from conversation
#
# Message endpoints:
# GET    /messages/                               - List all messages
# POST   /messages/                               - Send new message
# GET    /messages/{id}/                          - Get message details
# PUT    /messages/{id}/                          - Update message
# PATCH  /messages/{id}/                          - Partially update message
# DELETE /messages/{id}/                          - Delete message
# POST   /messages/{id}/mark_read/                - Mark message as read
# GET    /messages/unread/?user_id={id}           - Get unread messages for user