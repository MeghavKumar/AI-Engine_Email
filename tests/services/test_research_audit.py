from app.db.session import SessionLocal
from app.models import EmailAccount, ResearchAuditEvent, ResearchRun
from app.services.research_audit import ResearchAuditService


def test_create_and_get_research_audit_event():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="research-audit-service-test-user",
            provider="gmail",
            email_address="research-audit-service@example.com",
        )
        session.add(account)
        session.flush()

        research_run = ResearchRun(
            run_id="research-audit-service-run-001",
            account_id=account.id,
            research_type="historical_recipient",
            status="completed",
        )
        session.add(research_run)
        session.flush()

        service = ResearchAuditService(session)

        created = service.create(
            research_run_id=research_run.id,
            event_type="research_completed",
            source_type="MAILBOX",
            source_reference="message:67890",
            confidence=0.91,
            verification_status="PENDING",
            candidate_count=1,
            decision="REVIEW",
        )

        assert created.research_run_id == research_run.id
        assert created.event_type == "research_completed"
        assert created.source_type == "MAILBOX"
        assert created.source_reference == "message:67890"
        assert created.confidence == 0.91
        assert created.verification_status == "PENDING"
        assert created.candidate_count == 1
        assert created.decision == "REVIEW"

        fetched = service.get(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.research_run_id == research_run.id

        session.delete(created)
        session.flush()
        session.delete(research_run)
        session.flush()
        session.delete(account)
        session.commit()


def test_research_audit_event_persists_only_minimized_metadata():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="research-audit-security-test-user",
            provider="gmail",
            email_address="research-audit-security@example.com",
        )
        session.add(account)
        session.flush()

        research_run = ResearchRun(
            run_id="research-audit-security-run-001",
            account_id=account.id,
            research_type="historical_recipient",
            status="completed",
        )
        session.add(research_run)
        session.flush()

        service = ResearchAuditService(session)

        event = service.create(
            research_run_id=research_run.id,
            event_type="research_completed",
            source_type="MAILBOX",
            source_reference="message:security-test-001",
            confidence=0.88,
            verification_status="PENDING",
            candidate_count=1,
            decision="REVIEW",
        )

        session.flush()

        persisted_values = {
            column.name: getattr(event, column.name)
            for column in ResearchAuditEvent.__table__.columns
        }

        prohibited_values = {
            "SECRET_EMAIL_BODY",
            "person@example.com",
            "Sensitive Person Name",
            "Sensitive research evidence",
            "private comment",
        }

        assert not any(
            value in prohibited_values
            for value in persisted_values.values()
        )

        assert set(persisted_values) == {
            "id",
            "research_run_id",
            "event_type",
            "source_type",
            "source_reference",
            "confidence",
            "verification_status",
            "candidate_count",
            "decision",
            "created_at",
        }

        session.delete(event)
        session.flush()
        session.delete(research_run)
        session.flush()
        session.delete(account)
        session.commit()


def test_research_audit_rejects_non_opaque_source_reference():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="research-audit-reference-test-user",
            provider="gmail",
            email_address="research-audit-reference@example.com",
        )
        session.add(account)
        session.flush()

        research_run = ResearchRun(
            run_id="research-audit-reference-run-001",
            account_id=account.id,
            research_type="historical_recipient",
            status="completed",
        )
        session.add(research_run)
        session.flush()

        service = ResearchAuditService(session)

        import pytest

        with pytest.raises(ValueError, match="opaque"):
            service.create(
                research_run_id=research_run.id,
                event_type="research_completed",
                source_type="WEB",
                source_reference="https://example.com/contact",
            )

        session.rollback()
