from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Message detail view with history
    path('message/<uuid:message_id>/', views.message_detail, name='message_detail'),
    
    # API endpoint for message history as JSON
    path('api/message/<uuid:message_id>/history/', views.message_history_json, name='message_history_json'),
    
    # User's messages view
    path('my-messages/', views.user_messages, name='user_messages'),
    
    # User account deletion views
    path('account/delete/', views.delete_user_account, name='delete_user_account'),
    path('account/delete/confirm/', views.delete_user, name='delete_user'),
    path('account/deleted/', views.account_deleted, name='account_deleted'),
    
    # API endpoint for user data summary
    path('api/user/data-summary/', views.user_data_summary, name='user_data_summary'),
]