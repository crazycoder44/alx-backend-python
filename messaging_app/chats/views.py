from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import filters

from .models import Conversation, Message, CustomUser
from .serializers import ConversationSerializer, MessageSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['participants__email', 'participants__first_name', 'participants__last_name']

    def create(self, request, *args, **kwargs):
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
    filter_backends = [filters.SearchFilter]
    search_fields = ['sender__email', 'message_body', 'conversation__conversation_id']

    def create(self, request, *args, **kwargs):
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