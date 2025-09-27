# messaging_app/chats/filters.py
import django_filters
from .models import Message, Conversation

class MessageFilter(django_filters.FilterSet):
    # filter by participant email
    participant = django_filters.CharFilter(
        field_name="conversation__participants__email", lookup_expr="iexact"
    )
    # date range filters
    start_date = django_filters.DateTimeFilter(
        field_name="sent_at", lookup_expr="gte"
    )
    end_date = django_filters.DateTimeFilter(
        field_name="sent_at", lookup_expr="lte"
    )
    # filter by conversation
    conversation_id = django_filters.UUIDFilter(
        field_name="conversation__conversation_id"
    )

    class Meta:
        model = Message
        fields = ["participant", "start_date", "end_date", "conversation_id"]


class ConversationFilter(django_filters.FilterSet):
    participant = django_filters.CharFilter(
        field_name="participants__email", lookup_expr="iexact"
    )

    class Meta:
        model = Conversation
        fields = ["participant"]
