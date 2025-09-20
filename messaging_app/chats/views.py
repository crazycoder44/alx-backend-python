from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import Conversation, Message, CustomUser
from .serializers import ConversationSerializer, MessageSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new conversation with participants.
        Expected payload: { "participants": [user_id1, user_id2, ...] }
        """
        participants_ids = request.data.get('participants', [])
        if not participants_ids:
            return Response({"error": "Participants list is required."}, status=status.HTTP_400_BAD_REQUEST)

        conversation = Conversation.objects.create()
        participants = CustomUser.objects.filter(user_id__in=participants_ids)
        conversation.participants.set(participants)
        conversation.save()

        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def create(self, request, *args, **kwargs):
        """
        Send a message to an existing conversation.
        Expected payload: {
            "sender": user_id,
            "conversation": conversation_id,
            "message_body": "Your message here"
        }
        """
        sender_id = request.data.get('sender')
        conversation_id = request.data.get('conversation')
        message_body = request.data.get('message_body')

        if not sender_id or not conversation_id or not message_body:
            return Response({"error": "sender, conversation, and message_body are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        sender = get_object_or_404(CustomUser, user_id=sender_id)
        conversation = get_object_or_404(Conversation, conversation_id=conversation_id)

        message = Message.objects.create(
            sender=sender,
            conversation=conversation,
            message_body=message_body
        )

        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)