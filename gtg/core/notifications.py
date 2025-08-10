"""Desktop notification utilities"""

import subprocess


def send_desktop_notification(title: str, body: str, urgency: str = "critical") -> bool:
    """Send desktop notification using notify-send

    Args:
        title: Notification title
        body: Notification message body
        urgency: Notification urgency level (low, normal, critical)

    Returns:
        True if notification was sent successfully, False otherwise
    """
    try:
        subprocess.run(
            ["notify-send", "-u", urgency, "-i", "video-display", title, body],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to send desktop notification: {e}")
        return False
    except FileNotFoundError:
        print("Desktop notifications unavailable: notify-send not found")
        return False
