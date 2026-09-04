"""
Tests for security features - PHI guard and audit trail.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import warnings
import pytest
from agents.base import (
    PHIGuard,
    AuditTrail,
    AuditLogger,
    SecurityException,
    assert_no_phi,
    GLOBAL_AUDIT,
)


class TestPHIGuard:
    """Tests for PHI detection and redaction."""

    def test_detects_mrn(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive")

    def test_detects_ssn(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_detects_phone(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_detects_email(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_detects_dob(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1985")

    def test_detects_patient_name(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient Name: John Smith")

    def test_detects_john_doe(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Test patient John Doe admitted")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("CYP3A4 substrate interaction check")

    def test_empty_text_passes(self):
        PHIGuard.assert_no_phi("")

    def test_none_text_passes(self):
        PHIGuard.assert_no_phi(None)

    def test_redact_phi(self):
        result = PHIGuard.redact_phi("Patient MRN-12345 has SSN 123-45-6789")
        assert "REDACTED_IDENTIFIER" in result
        assert "MRN" not in result
        assert "123-45-6789" not in result

    def test_redact_preserves_clean_text(self):
        result = PHIGuard.redact_phi("CYP3A4 inhibitor ketoconazole")
        assert result == "CYP3A4 inhibitor ketoconazole"


class TestAuditTrail:
    """Tests for HMAC-SHA256 audit trail."""

    def test_audit_trail_with_explicit_key(self):
        trail = AuditTrail(secret_key="test-key-123")
        entry = trail.log("test_actor", "test_tier", "TEST_EVENT", {"data": "value"})
        assert "current_hash" in entry
        assert "audit_id" in entry
        assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"

    def test_audit_trail_chaining(self):
        trail = AuditTrail(secret_key="test-key-123")
        entry1 = trail.log("actor1", "tier1", "EVENT1", {"data": "value1"})
        entry2 = trail.log("actor2", "tier2", "EVENT2", {"data": "value2"})
        assert entry2["prev_hash"] == entry1["current_hash"]

    def test_audit_trail_integrity_verification(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("actor1", "tier1", "EVENT1", {"data": "value1"})
        trail.log("actor2", "tier2", "EVENT2", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_audit_trail_empty_integrity(self):
        trail = AuditTrail(secret_key="test-key-123")
        assert trail.verify_integrity() is True

    def test_audit_trail_generates_ephemeral_key_without_env(self):
        """When no key is provided and env var not set, should generate ephemeral key."""
        # Remove env var if present
        old_key = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                trail = AuditTrail()
                assert len(w) == 1
                assert "AUDIT_SECRET_KEY not set" in str(w[0].message)
                assert issubclass(w[0].category, RuntimeWarning)
        finally:
            if old_key is not None:
                os.environ["AUDIT_SECRET_KEY"] = old_key

    def test_audit_trail_uses_env_var_when_set(self):
        """When AUDIT_SECRET_KEY env var is set, it should be used."""
        old_key = os.environ.get("AUDIT_SECRET_KEY")
        os.environ["AUDIT_SECRET_KEY"] = "env-based-key-123"
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                trail = AuditTrail()
                # Should not warn when env var is set
                assert len(w) == 0
        finally:
            if old_key is not None:
                os.environ["AUDIT_SECRET_KEY"] = old_key
            else:
                os.environ.pop("AUDIT_SECRET_KEY", None)

    def test_audit_trail_blocks_phi_in_details(self):
        """Audit trail should reject PHI in log details."""
        trail = AuditTrail(secret_key="test-key-123")
        with pytest.raises(SecurityException):
            trail.log("actor", "tier", "EVENT", {"patient": "MRN-12345"})


class TestAuditLogger:
    """Tests for the global AuditLogger."""

    def test_log_and_verify(self):
        entry = AuditLogger.log("test", "tier", "TEST", {"key": "value"})
        assert "current_hash" in entry
        assert AuditLogger.verify_integrity() is True

    def test_get_trail(self):
        trail = AuditLogger.get_trail()
        assert isinstance(trail, list)
