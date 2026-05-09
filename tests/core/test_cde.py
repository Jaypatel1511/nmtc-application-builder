"""Tests for CDEProfile."""
import os
import tempfile

import pytest
import yaml

from nmtcapp.core.cde import CDEProfile


def test_cde_profile_creation():
    cde = CDEProfile(
        name="Test CDE LLC",
        cde_id="CDE-2020-0001",
        certification_date="2020-01-01",
        mission="Test mission",
        target_markets=["Illinois"],
        prior_awards=[],
        contact={"name": "Jane"},
        governance={"board_members": 5},
    )
    assert cde.name == "Test CDE LLC"
    assert cde.cde_id == "CDE-2020-0001"


def test_cde_profile_optional_website_defaults_to_none():
    cde = CDEProfile(
        name="Test CDE",
        cde_id="CDE-001",
        certification_date="2020-01-01",
        mission="Mission",
        target_markets=["IL"],
        prior_awards=[],
        contact={},
        governance={},
    )
    assert cde.website is None


def test_cde_profile_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        CDEProfile(
            name="",
            cde_id="CDE-001",
            certification_date="2020-01-01",
            mission="M",
            target_markets=["IL"],
            prior_awards=[],
            contact={},
            governance={},
        )


def test_cde_profile_empty_cde_id_raises():
    with pytest.raises(ValueError, match="cde_id"):
        CDEProfile(
            name="Test",
            cde_id="   ",
            certification_date="2020-01-01",
            mission="M",
            target_markets=["IL"],
            prior_awards=[],
            contact={},
            governance={},
        )


def test_cde_target_markets_must_be_list():
    with pytest.raises(ValueError, match="target_markets"):
        CDEProfile(
            name="Test",
            cde_id="CDE-001",
            certification_date="2020-01-01",
            mission="M",
            target_markets="Illinois",  # string, not list
            prior_awards=[],
            contact={},
            governance={},
        )


def test_cde_sample_returns_valid_profile():
    cde = CDEProfile.sample()
    assert isinstance(cde, CDEProfile)
    assert cde.name
    assert cde.cde_id
    assert len(cde.target_markets) > 0
    assert len(cde.prior_awards) > 0


def test_cde_sample_has_required_fields():
    cde = CDEProfile.sample()
    assert cde.mission
    assert cde.certification_date
    assert isinstance(cde.contact, dict)
    assert isinstance(cde.governance, dict)


def test_cde_total_prior_allocation():
    cde = CDEProfile(
        name="Test",
        cde_id="CDE-001",
        certification_date="2020-01-01",
        mission="M",
        target_markets=["IL"],
        prior_awards=[
            {"year": 2020, "amount": 40_000_000, "deployment_status": "fully_deployed"},
            {"year": 2022, "amount": 55_000_000, "deployment_status": "fully_deployed"},
        ],
        contact={},
        governance={},
    )
    assert cde.total_prior_allocation() == 95_000_000


def test_cde_to_dict():
    cde = CDEProfile.sample()
    d = cde.to_dict()
    assert isinstance(d, dict)
    assert "name" in d
    assert "total_prior_allocation" in d
    assert d["total_prior_allocation"] > 0


def test_cde_from_yaml_success():
    data = {
        "name": "YAML CDE LLC",
        "cde_id": "CDE-YAML-001",
        "certification_date": "2021-06-01",
        "mission": "YAML mission",
        "target_markets": ["IL", "OH"],
        "prior_awards": [],
        "contact": {"name": "Test"},
        "governance": {"board_members": 7},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        path = f.name
    try:
        cde = CDEProfile.from_yaml(path)
        assert cde.name == "YAML CDE LLC"
        assert cde.cde_id == "CDE-YAML-001"
    finally:
        os.unlink(path)


def test_cde_from_yaml_missing_fields_raises():
    data = {"name": "Incomplete CDE"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(data, f)
        path = f.name
    try:
        with pytest.raises(ValueError, match="missing required fields"):
            CDEProfile.from_yaml(path)
    finally:
        os.unlink(path)


def test_cde_from_yaml_file_not_found():
    with pytest.raises(FileNotFoundError):
        CDEProfile.from_yaml("/nonexistent/path.yaml")
