from app.db.repositories.research_audit_event import ResearchAuditEventRepository
from app.db.session import SessionLocal
from app.models import EmailAccount, ResearchAuditEvent, ResearchRun


def test_create_get_and_list_research_audit_event():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="research-audit-test-user",
            provider="gmail",
            email_address="research-audit@example.com",
        )
        session.add(account)
        session.flush()

        research_run = ResearchRun(
            run_id="research-audit-run-001",
            account_id=account.id,
            research_type="historical_recipient",
            status="completed",
        )
        session.add(research_run)
        session.flush()

        repository = ResearchAuditEventRepository(session)

        event = repository.create(
            research_run_id=research_run.id,
            event_type="research_completed",
            source_type="MAILBOX",
            source_reference="message:12345",
            confidence=0.95,
            verification_status="PENDING",
            candidate_count=2,
            decision="REVIEW",
        )

        assert event.id is not None
        assert event.research_run_id == research_run.id
        assert event.event_type == "research_completed"
        assert event.source_type == "MAILBOX"
        assert event.source_reference == "message:12345"
        assert event.confidence == 0.95
        assert event.verification_status == "PENDING"
        assert event.candidate_count == 2
        assert event.decision == "REVIEW"
        assert event.created_at is not None

        session.commit()

        loaded = repository.get(event.id)

        assert loaded is not None
        assert loaded.id == event.id
        assert loaded.research_run_id == research_run.id
        assert loaded.event_type == "research_completed"

        events = repository.list_by_research_run(research_run.id)

        assert len(events) == 1
        assert events[0].id == event.id

        session.delete(loaded)
        session.flush()
        session.delete(research_run)
        session.flush()
        session.delete(account)
        session.commit()
