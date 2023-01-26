import discord


def sec_to_min(time: float):
    time = round(time)
    hours, seconds = divmod(time, 60 * 60)
    minutes, seconds = divmod(seconds, 60)
    if not hours:
        return f"{minutes}m {str(seconds).zfill(2)}s"
    return f"{hours}h {minutes}m {str(seconds).zfill(2)}s"


async def fetch_or_get_message(client: discord.Bot, message_id: int, channel_id: int) -> discord.Message:
    message = client.get_message(message_id)
    if message is not None:
        return message
    else:
        partial_msg = client.get_partial_messageable(channel_id)
        return await partial_msg.fetch_message(message_id)
