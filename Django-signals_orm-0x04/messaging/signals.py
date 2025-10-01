from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Notification


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal handler that creates a notification when a new message is created.
    
    Args:
        sender: The model class (Message)
        instance: The actual Message instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Create notification for the recipient
        notification_content = f"You have a new message from {instance.sender.username}"
        
        Notification.objects.create(
            user=instance.recipient,
            message=instance,
            notification_type='message',
            content=notification_content
        )
        
        print(f"Notification created for {instance.recipient.username} about message from {instance.sender.username}")


@receiver(post_save, sender=Message)
def log_message_creation(sender, instance, created, **kwargs):
    """
    Additional signal handler to log message creation.
    This demonstrates that multiple signals can listen to the same event.
    
    Args:
        sender: The model class (Message)
        instance: The actual Message instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        print(f"New message logged: {instance.message_id} from {instance.sender.username} to {instance.recipient.username}")