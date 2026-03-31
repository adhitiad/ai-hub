import re

with open('migrate_timezone.py', 'r') as f:
    content = f.read()

replacement = """        coll_scanned = 0
        coll_updated = 0
        coll_fields = 0
        bulk_operations = []
        BATCH_SIZE = 1000

        async for doc in cursor:
            total_docs += 1
            coll_scanned += 1
            updates = {}
            for field in fields:
                value = doc.get(field)
                if isinstance(value, datetime) and value.tzinfo is None:
                    updates[field] = value.replace(tzinfo=timezone.utc)

            if updates:
                updated_fields += len(updates)
                updated_docs += 1
                coll_fields += len(updates)
                coll_updated += 1
                if apply:
                    bulk_operations.append(UpdateOne({"_id": doc["_id"]}, {"$set": updates}))
                    if len(bulk_operations) >= BATCH_SIZE:
                        await collection.bulk_write(bulk_operations)
                        bulk_operations.clear()

        if apply and bulk_operations:
            await collection.bulk_write(bulk_operations)
            bulk_operations.clear()"""

# Replace the inner loop logic
pattern = re.compile(r'        coll_scanned = 0.*?if apply:\s*await collection\.update_one\(\{"_id": doc\["_id"\]\}, \{"\$set": updates\}\)', re.DOTALL)
new_content = pattern.sub(replacement, content)

with open('migrate_timezone.py', 'w') as f:
    f.write(new_content)
