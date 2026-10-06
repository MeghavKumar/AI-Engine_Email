from app.models import ResearchAuditEvent


def test_research_audit_event_contains_no_sensitive_content_columns():
    column_names = set(ResearchAuditEvent.__table__.columns.keys())

    prohibited_columns = {
        "body",
        "body_text",
        "evidence",
        "evidence_hash",
        "candidate_email",
        "candidate_name",
        "metadata",
        "reason",
        "comment",
    }

    assert column_names.isdisjoint(prohibited_columns)
