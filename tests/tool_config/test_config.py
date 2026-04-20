from transparency.enforcement.config import ToolsConfig, ToolRule, TransferConfig

def test_toolsconfig_from_dict(sample_config_dict):
    config = ToolsConfig.from_dict(sample_config_dict)
    assert config.version == 1
    assert config.signed_by == "employer@company.com"
    assert len(config.allowed_tools) == 4
    assert len(config.denied_tools) == 1
    assert config.allowed_tools[0].name == "read_vault_file"
    assert "prosper0-vault/**" in config.allowed_tools[0].paths
    assert config.transfer.allowed is True
    assert config.transfer.employer_email == "employer@company.com"

def test_tool_rule_no_paths():
    rule = ToolRule(name="search_vault", paths=[])
    assert rule.paths == []
