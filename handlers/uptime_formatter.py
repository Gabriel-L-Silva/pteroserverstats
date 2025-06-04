def format_uptime(time_ms):
    """Format uptime from milliseconds to human readable format"""
    text = []
    days = time_ms // 86400000
    hours = (time_ms // 3600000) % 24
    minutes = (time_ms // 60000) % 60
    seconds = (time_ms // 1000) % 60
    
    if days > 0:
        text.append(f"{days} days")
    if hours > 0:
        text.append(f"{hours} hours")
    if minutes > 0:
        text.append(f"{minutes} minutes")
    
    if len(text) > 0:
        text.append(f"and {seconds} seconds")
    else:
        text.append(f"{seconds} seconds")
    
    return ", ".join(text).replace(", and", " and") 