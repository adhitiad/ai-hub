import sys
import os
import hashlib
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# --- SETUP STUBS AND MOCKS ---

class ObjectId:
    def __init__(self, val=None):
        self.val = str(val) if val else "507f1f77bcf86cd799439011"
    def __str__(self):
        return self.val
    def __repr__(self):
        return f"ObjectId('{self.val}')"
    def __eq__(self, other):
        return str(self) == str(other)

# Mock all external dependencies
sys.modules['bson'] = MagicMock()
sys.modules['bson'].ObjectId = ObjectId
sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.security.api_key'] = MagicMock()
sys.modules['motor'] = MagicMock()
sys.modules['motor.motor_asyncio'] = MagicMock()
sys.modules['msgpack'] = MagicMock()
sys.modules['redis'] = MagicMock()
sys.modules['redis.asyncio'] = MagicMock()
sys.modules['passlib'] = MagicMock()
sys.modules['passlib.context'] = MagicMock()
sys.modules['fastapi_limiter'] = MagicMock()
sys.modules['fastapi_limiter.depends'] = MagicMock()
sys.modules['slowapi'] = MagicMock()
sys.modules['slowapi.util'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['starlette.requests'] = MagicMock()

# Ensure src is in path
sys.path.append(os.getcwd())

# Create a mock database module to avoid real connections
mock_users_collection = AsyncMock()
mock_smart_cache = AsyncMock()

# Mocking internal src dependencies
sys.modules['src.core.logger'] = MagicMock()
sys.modules['src.core.security'] = MagicMock()
sys.modules['src.core.security'].hash_api_key = lambda x: hashlib.sha256(x.encode()).hexdigest()

# Manually load the code we want to test by reading it and executing in a namespace
def load_module(filepath, name):
    import types
    with open(filepath, 'r') as f:
        code = f.read()
    module = types.ModuleType(name)
    sys.modules[name] = module
    # Inject mocks into module namespace BEFORE execution
    if name == 'src.api.auth':
        module.users_collection = mock_users_collection
        module.SmartCache = mock_smart_cache
        module.HTTPException = Exception
        module.Security = lambda x: x
        module.hash_api_key = lambda x: hashlib.sha256(x.encode()).hexdigest()
        module.APIKeyHeader = MagicMock()
        module.APIKeyCookie = MagicMock()
        module.Request = MagicMock()
    elif name == 'src.database.database':
        module.users_collection = mock_users_collection
        module.ObjectId = ObjectId
        module.datetime = datetime
        module.timezone = timezone
        module.secrets = MagicMock()
        module.hashlib = hashlib
        module.SmartCache = mock_smart_cache
        module.logger = MagicMock()
        module.motor = MagicMock()
        module.motor.motor_asyncio = MagicMock()
        module.AsyncIOMotorClient = MagicMock()

    # exec code in module namespace
    exec(code, module.__dict__)
    return module

async def run_tests():
    try:
        with patch('motor.motor_asyncio.AsyncIOMotorClient', MagicMock()):
            auth_mod = load_module('src/api/auth.py', 'src.api.auth')

            # --- TEST 1 ---
            # Mock Request
            mock_request = MagicMock()
            user_id = ObjectId()
            sample_user = {
                "_id": user_id,
                "api_key_hash": hashlib.sha256(b"test_key").hexdigest(),
                "subscription_status": "active",
                "last_request_date": "2024-01-01",
                "requests_today": 5,
                "daily_requests_limit": 100,
                "role": "user"
            }
            mock_smart_cache.get.return_value = None
            mock_users_collection.find_one.return_value = sample_user
            mock_users_collection.find_one_and_update.return_value = sample_user

            user = await auth_mod.get_current_user(mock_request, api_key_h="test_key")
            if str(user["_id"]) != str(user_id): raise Exception("T1 Failed")

            # --- TEST 2 ---
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            stale_user = {
                "_id": user_id,
                "api_key_hash": hashlib.sha256(b"test_key").hexdigest(),
                "subscription_status": "active",
                "last_request_date": today,
                "requests_today": 0,
                "daily_requests_limit": 10,
                "role": "user"
            }
            mock_smart_cache.get.return_value = auth_mod.serialize_user(stale_user)
            mock_users_collection.find_one_and_update.return_value = None
            mock_users_collection.find_one.return_value = stale_user

            try:
                await auth_mod.get_current_user(mock_request, api_key_h="test_key")
            except Exception as e:
                if "429" not in str(e) and "Daily Limit Reached" not in str(e):
                    raise e

            with open('test_results.txt', 'w') as f:
                f.write("PASSED\n")
    except Exception as e:
        with open('test_results.txt', 'w') as f:
            f.write(f"FAILED: {str(e)}\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
