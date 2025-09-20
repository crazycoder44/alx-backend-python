# views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import filters
from rest_framework.decorators import action
from .models import Conversation, Message, User as CustomUser
from .serializers import ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    Provides CRUD operations and conversation-specific actions.
    """
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['participants__email', 'participants__first_name', 'participants__last_name']

    def create(self, request, *args, **kwargs):
        """Create a new conversation with participants."""
        participant_ids = request.data.get('participant_ids', [])
        title = request.data.get('title', '')
        
        if not participant_ids:
            return Response(
                {"error": "participant_ids list is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate that all participant IDs exist
        participants = CustomUser.objects.filter(id__in=participant_ids)
        if participants.count() != len(participant_ids):
            return Response(
                {"error": "One or more participant IDs are invalid."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create conversation
        conversation = Conversation.objects.create(title=title)
        conversation.participants.set(participants)
        conversation.save()
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to the conversation."""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CustomUser.objects.get(id=user_id)
            conversation.participants.add(user)
            return Response({'message': 'Participant added successfully'})
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from the conversation."""
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CustomUser.objects.get(id=user_id)
            
            # Prevent removing the last participant
            if conversation.participants.count() <= 1:
                return Response(
                    {'error': 'Cannot remove the last participant'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            conversation.participants.remove(user)
            return Response({'message': 'Participant removed successfully'})
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages.
    Provides CRUD operations and message-specific actions.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['sender__email', 'message_body', 'conversation__conversation_id']

    def get_queryset(self):
        """Filter messages by conversation if accessing via nested route."""
        queryset = super().get_queryset()
        conversation_pk = self.kwargs.get('conversation_pk')
        
        if conversation_pk:
            # Filter messages for specific conversation when accessing nested route
            queryset = queryset.filter(conversation__conversation_id=conversation_pk)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """Send a message to an existing conversation."""
        # Check if we're accessing via nested route
        conversation_pk = self.kwargs.get('conversation_pk')
        
        sender_id = request.data.get('sender_id')
        conversation_id = conversation_pk or request.data.get('conversation')
        message_body = request.data.get('message_body')
        message_type = request.data.get('message_type', 'text')
        
        if not sender_id or not conversation_id or not message_body:
            return Response(
                {"error": "sender_id, conversation, and message_body are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            sender = CustomUser.objects.get(id=sender_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Invalid sender ID."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            conversation = Conversation.objects.get(conversation_id=conversation_id)
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Invalid conversation ID."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify sender is a participant in the conversation
        if not conversation.participants.filter(id=sender_id).exists():
            return Response(
                {"error": "Sender is not a participant in this conversation."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create the message
        message = Message.objects.create(
            sender=sender,
            conversation=conversation,
            message_body=message_body,
            message_type=message_type
        )
        
        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read."""
        message = self.get_object()
        
        # Don't allow marking own messages as read
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if str(message.sender.id) == str(user_id):
            return Response(
                {'error': 'Cannot mark your own message as read'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For simplicity, just update the is_read field
        # In a more complex system, you'd track read status per user
        message.is_read = True
        message.save()
        
        return Response({'message': 'Message marked as read'})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread messages for a specific user."""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get unread messages where user is a participant but not the sender
        unread_messages = Message.objects.filter(
            conversation__participants=user,
            is_read=False
        ).exclude(sender=user).order_by('-sent_at')
        
        serializer = MessageSerializer(unread_messages, many=True)
        return Response({
            'messages': serializer.data,
            'count': unread_messages.count()
        })


