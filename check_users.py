import asyncio

from src.core.database import users_collection


async def check_users():
    users = await users_collection.find(
        {}, {"email": 1, "api_key": 1, "role": 1, "subscription_status": 1}
    ).to_list(100)
    print("Total users:", len(users))
    for user in users:
        print(
            "Email:",
            user.get("email"),
            "API Key:",
            user.get("api_key"),
            "Role:",
            user.get("role"),
            "Status:",
            user.get("subscription_status"),
        )


asyncio.run(check_users())
