from typing import Any, Optional

import msgpack

from src.core.redis_client import redis_client


class SmartCache:
    @staticmethod
    async def set(key: str, data: Any, ttl: int = 3600):
        """
        Simpan data ke Redis dalam format Binary (MessagePack).
        """
        try:
            # Serialize: Object -> Binary
            packed_data = msgpack.packb(data, use_bin_type=True)
            if packed_data:
                await redis_client.set(key, packed_data.hex(), ex=ttl)
        except Exception as e:
            print(f"Cache Set Error: {e}")

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """
        Ambil data binary dari Redis dan kembalikan ke Object asli.
        """
        try:
            packed_data = await redis_client.get(key)
            if not packed_data:
                return None

            # Deserialize: Binary -> Object
            return msgpack.unpackb(bytes.fromhex(packed_data), raw=False)
        except Exception as e:
            print(f"Cache Get Error: {e}")
            return None

    @staticmethod
    async def delete(key: str):
        await redis_client.delete(key)
