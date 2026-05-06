from dataclasses import dataclass, field


@dataclass
class ToolRule:
    name: str
    paths: list[str] = field(default_factory=list)


@dataclass
class TransferConfig:
    allowed: bool
    max_size_kb: int
    employer_email: str


@dataclass
class ToolsConfig:
    version: int
    signed_by: str
    allowed_tools: list[ToolRule]
    denied_tools: list[ToolRule]
    transfer: TransferConfig

    @classmethod
    def from_dict(cls, data: dict) -> "ToolsConfig":
        tools = data.get("tools", {})
        allowed = [
            ToolRule(name=t["name"], paths=t.get("paths", []))
            for t in tools.get("allowed", [])
        ]
        denied = [
            ToolRule(name=t["name"], paths=t.get("paths", []))
            for t in tools.get("denied", [])
        ]
        t = data["transfer"]
        transfer = TransferConfig(
            allowed=t["allowed"],
            max_size_kb=t["max_size_kb"],
            employer_email=t["employer_email"],
        )
        return cls(
            version=data["version"],
            signed_by=data["signed_by"],
            allowed_tools=allowed,
            denied_tools=denied,
            transfer=transfer,
        )
