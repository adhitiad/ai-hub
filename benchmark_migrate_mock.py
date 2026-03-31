import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from migrate_timezone import migrate_timezone, FIELDS_BY_COLLECTION

# Create a mock collection with a bunch of documents
async def mock_async_generator(items):
    for item in items:
        yield item

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.find_calls = 0
        self.update_one_calls = 0
        self.bulk_write_calls = 0

    def find(self, *args, **kwargs):
        self.find_calls += 1
        mock_cursor = MagicMock()
        mock_cursor.batch_size.return_value = self
        return mock_cursor

    def __aiter__(self):
        # Generate 1000 docs
        fields = FIELDS_BY_COLLECTION.get(self.name, ["created_at"])
        docs = []
        for i in range(1000):
            doc = {"_id": i}
            for f in fields:
                doc[f] = datetime.now()
            docs.append(doc)
        return mock_async_generator(docs)

    async def update_one(self, *args, **kwargs):
        self.update_one_calls += 1
        await asyncio.sleep(0.001) # Simulate 1ms network latency

    async def bulk_write(self, requests, *args, **kwargs):
        self.bulk_write_calls += 1
        await asyncio.sleep(0.005) # Simulate 5ms network latency for bulk

class MockDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

class MockClient:
    def __init__(self, *args, **kwargs):
        self.db = MockDB()

    def __getitem__(self, name):
        return self.db

    def close(self):
        pass

async def run_benchmark():
    with patch('migrate_timezone.AsyncIOMotorClient', MockClient):
        with patch('migrate_timezone.MONGO_URI', 'mongodb://mock'):
            start_time = time.time()
            await migrate_timezone(apply=True)
            end_time = time.time()

            print(f"Time taken: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
