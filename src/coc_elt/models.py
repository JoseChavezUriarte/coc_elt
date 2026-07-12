from typing import Any, List
from pydantic import BaseModel, ConfigDict, model_validator

def normalize_envelope(data: Any) -> Any:
    if isinstance(data, dict):
        if "items" in data:
            return data
        raise ValueError(f"Expected pagination envelope with an 'items' array. Received keys: {list(data.keys())}")
    if isinstance(data, list):
        return {"items": data}
    raise ValueError(f"Root payload must be a dictionary envelope or a list. Received type: {type(data).__name__}")

class ClanRecord(BaseModel):
    model_config = ConfigDict(extra='allow')
    tag: str
    name: str

class MemberRecord(BaseModel):
    model_config = ConfigDict(extra='allow')
    tag: str
    name: str

class MemberListResponse(BaseModel):
    items: List[MemberRecord]

    @model_validator(mode='before')
    @classmethod
    def validate_envelope(cls, data: Any) -> Any:
        return normalize_envelope(data)

class WarRecord(BaseModel):
    model_config = ConfigDict(extra='allow')
    state: str

class CapitalRaidRecord(BaseModel):
    model_config = ConfigDict(extra='allow')
    state: str
    startTime: str

class CapitalRaidListResponse(BaseModel):
    items: List[CapitalRaidRecord]

    @model_validator(mode='before')
    @classmethod
    def validate_envelope(cls, data: Any) -> Any:
        return normalize_envelope(data)
