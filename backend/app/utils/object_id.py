from bson import ObjectId
from bson.errors import InvalidId


def validate_object_id(oid: str) -> ObjectId:
    """Validate and convert string to ObjectId, raising ValueError if invalid."""
    try:
        return ObjectId(oid)
    except (InvalidId, TypeError):
        raise ValueError(f"Invalid ObjectId: {oid}")


def str_to_object_id(oid: str) -> ObjectId:
    return validate_object_id(oid)


def serialize_doc(doc: dict) -> dict:
    """Recursively convert ObjectId and datetime fields to JSON-safe types."""
    if doc is None:
        return None
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_doc(item) if isinstance(item, dict) else (str(item) if isinstance(item, ObjectId) else item)
                for item in value
            ]
        else:
            result[key] = value
    return result
