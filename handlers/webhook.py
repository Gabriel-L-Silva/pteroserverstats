import requests
from discord import SyncWebhook, Embed
from colorama import Fore

def send_webhook_notification(embed, config):
    """Send webhook notification"""
    if not config.get('notifier.enable'):
        return
    
    try:
        webhook_url = config.get('notifier.webhook')
        if not webhook_url:
            return
        
        # Create Discord webhook using SyncWebhook
        webhook = SyncWebhook.from_url(webhook_url)
        
        # Create the embed with notifier configuration
        notification_embed = Embed(
            title=embed.title,
            description=embed.description,
            color=embed.color
        )
        
        # Set author if configured
        author_name = config.get('notifier.embed.author.name')
        author_icon = config.get('notifier.embed.author.icon')
        if author_name or author_icon:
            notification_embed.set_author(name=author_name, icon_url=author_icon)
        
        # Set footer if configured
        footer_text = config.get('notifier.embed.footer.text')
        footer_icon = config.get('notifier.embed.footer.icon')
        if footer_text or footer_icon:
            notification_embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        # Set thumbnail and image if configured
        thumbnail_url = config.get('notifier.embed.thumbnail')
        if thumbnail_url:
            notification_embed.set_thumbnail(url=thumbnail_url)
        
        image_url = config.get('notifier.embed.image')
        if image_url:
            notification_embed.set_image(url=image_url)
        
        # Set timestamp if enabled
        if config.get('notifier.embed.timestamp'):
            notification_embed.timestamp = embed.timestamp
        
        webhook.send(embed=notification_embed)
        
    except Exception as error:
        print(f"{Fore.CYAN}[PSS] {Fore.RED}Invalid Webhook URL")
        if config.get('log_error'):
            print(f"Webhook error: {error}") 