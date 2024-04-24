from discord import Client, Intents

intents = Intents.default()
intents.message_content = True
intents.members = True

client = Client(intents=intents)


def client_id() -> int:
    """
    取得機器人的客戶端ID(即Discord中的User ID)
    """
    if client.user is None:
        raise Exception("The client is not ready yet.")

    return client.user.id
