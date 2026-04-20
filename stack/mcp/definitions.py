TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the vault. Returns the file contents as text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path within the vault (e.g., /vault/Tasks/foo.md)",
                    }
                },
                "required": ["path"],
            },
        },
    }
]
