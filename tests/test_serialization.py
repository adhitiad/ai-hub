import hashlib
from datetime import datetime, timezone

# Mock ObjectId for simplicity
class ObjectId:
    def __init__(self, val="507f1f77bcf86cd799439011"):
        self.val = val
    def __str__(self): return self.val
    def __repr__(self): return f"ObjectId('{self.val}')"

def serialize_user(user):
    serialized = user.copy()
    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])
    for key, value in serialized.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
    return serialized

def deserialize_user(user):
    deserialized = user.copy()
    if "_id" in deserialized:
        deserialized["_id"] = ObjectId(deserialized["_id"])
    for key, value in deserialized.items():
        if isinstance(value, str):
            try:
                deserialized[key] = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                pass
    return deserialized

def test_serialization():
    dt = datetime.now(timezone.utc)
    oid = ObjectId()
    user = {
        "_id": oid,
        "name": "Test",
        "created_at": dt
    }

    ser = serialize_user(user)
    assert ser["_id"] == str(oid)
    assert ser["created_at"] == dt.isoformat()

    deser = deserialize_user(ser)
    assert str(deser["_id"]) == str(oid)
    assert deser["created_at"] == dt
    print("Serialization test passed!")

if __name__ == "__main__":
    test_serialization()
