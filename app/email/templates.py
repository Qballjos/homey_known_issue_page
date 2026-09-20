from app.config import settings


def render_base_email(title: str, content_html: str, unsubscribe_url: str = None) -> str:
    """Renders a clean, modern, responsive email consistent with the platform design."""
    unsub_section = ""
    if unsubscribe_url:
        unsub_section = f"""
        <div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #E5E7EB; font-size: 12px; color: #6B7280; text-align: center;">
            You received this email because you subscribed to updates for this issue.<br>
            <a href="{unsubscribe_url}" style="color: #4B5563; text-decoration: underline; margin-top: 8px; display: inline-block;">Unsubscribe from this issue</a>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F9FAFB; margin: 0; padding: 24px; color: #111827;">
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 580px; background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E5E7EB; box-shadow: 0 1px 3px rgba(0,0,0,0.05); overflow: hidden;">
        <tr>
            <td style="padding: 24px 32px 16px 32px; border-bottom: 1px solid #F3F4F6;">
                <div style="display: flex; align-items: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #00B86B; margin-right: 8px;"></span>
                    <span style="font-size: 16px; font-weight: 700; color: #111827; letter-spacing: -0.02em;">{settings.APP_NAME}</span>
                </div>
            </td>
        </tr>
        <tr>
            <td style="padding: 32px;">
                {content_html}
                {unsub_section}
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_confirmation_email(issue_title: str, confirm_url: str) -> tuple[str, str, str]:
    """Returns (subject, text_body, html_body) for double opt-in confirmation."""
    subject = f"Please confirm your subscription: {issue_title}"
    
    text_body = f"""Hello,

You recently requested to receive updates about the following known issue:
"{issue_title}"

To confirm your subscription, please visit the link below:
{confirm_url}

If you did not request this update, no action is needed and you will not be subscribed.

This email was sent by {settings.APP_NAME}.
"""

    html_content = f"""
    <h2 style="font-size: 20px; font-weight: 700; color: #111827; margin-top: 0; margin-bottom: 16px;">Confirm your subscription</h2>
    <p style="font-size: 14px; line-height: 1.6; color: #374151; margin-bottom: 24px;">
        You requested to receive email updates whenever new information or fixes become available for:
    </p>
    <div style="background-color: #F9FAFB; border-left: 4px solid #00B86B; padding: 16px; border-radius: 8px; font-weight: 600; color: #111827; margin-bottom: 28px;">
        {issue_title}
    </div>
    <div style="text-align: center; margin-bottom: 28px;">
        <a href="{confirm_url}" style="background-color: #00B86B; color: #FFFFFF; text-decoration: none; padding: 12px 28px; border-radius: 9999px; font-weight: 600; font-size: 14px; display: inline-block;">
            Confirm Subscription
        </a>
    </div>
    <p style="font-size: 12px; color: #6B7280; line-height: 1.5;">
        Or paste this link in your browser:<br>
        <a href="{confirm_url}" style="color: #00B86B; word-break: break-all;">{confirm_url}</a>
    </p>
    <p style="font-size: 12px; color: #9CA3AF; margin-top: 24px;">
        If you did not make this request, you can safely ignore this email.
    </p>
    """
    html_body = render_base_email(subject, html_content)
    return subject, text_body, html_body


def get_issue_update_email(
    issue_title: str,
    issue_status: str,
    update_title: str,
    update_description: str,
    issue_url: str,
    unsubscribe_url: str
) -> tuple[str, str, str]:
    """Returns (subject, text_body, html_body) for issue updates and status changes."""
    subject = f"Known Issue Update: {issue_title}"

    text_body = f"""Known Issue Update

The status of this issue is now: {issue_status}

Update: {update_title}
{update_description}

View full issue details:
{issue_url}

Unsubscribe from this issue:
{unsubscribe_url}
"""

    html_content = f"""
    <div style="margin-bottom: 16px;">
        <span style="display: inline-block; background-color: #E5E7EB; color: #1F2937; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; text-transform: uppercase;">
            Status: {issue_status}
        </span>
    </div>
    <h2 style="font-size: 20px; font-weight: 700; color: #111827; margin-top: 0; margin-bottom: 8px;">
        {issue_title}
    </h2>
    <div style="background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; margin: 24px 0;">
        <div style="font-size: 15px; font-weight: 600; color: #111827; margin-bottom: 8px;">
            {update_title}
        </div>
        <div style="font-size: 14px; line-height: 1.6; color: #374151; white-space: pre-line;">
            {update_description}
        </div>
    </div>
    <div style="text-align: center; margin: 28px 0 16px 0;">
        <a href="{issue_url}" style="background-color: #111827; color: #FFFFFF; text-decoration: none; padding: 12px 28px; border-radius: 9999px; font-weight: 600; font-size: 14px; display: inline-block;">
            View Issue Details
        </a>
    </div>
    """
    html_body = render_base_email(subject, html_content, unsubscribe_url=unsubscribe_url)
    return subject, text_body, html_body
