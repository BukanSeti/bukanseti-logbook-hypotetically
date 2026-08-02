from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_render_blueprint_has_required_private_configuration() -> None:
    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    services = blueprint["services"]
    assert len(services) == 1
    service = services[0]
    assert service["type"] == "web"
    assert service["runtime"] == "docker"
    assert service["dockerfilePath"] == "./Dockerfile.reference-api"
    assert service["healthCheckPath"] == "/health"
    assert service["autoDeployTrigger"] == "checksPass"

    env_vars = {item["key"]: item for item in service["envVars"]}
    secret_keys = {
        "LION_AIR_CREW_SHEET_ID",
        "LION_AIR_AIRCRAFT_SHEET_ID",
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        "CORADINE_API_TOKEN_HASHES",
    }
    assert secret_keys <= set(env_vars)
    for key in secret_keys:
        assert env_vars[key] == {"key": key, "sync": False}


def test_render_blueprint_contains_no_secret_material() -> None:
    text = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "private_key" not in text
    assert "BEGIN PRIVATE KEY" not in text
    assert "token_urlsafe" not in text
