from app.models import EmailWorkflow


def test_email_workflow_model():
    assert EmailWorkflow.__tablename__ == "email_workflows"

    columns = set(EmailWorkflow.__table__.columns.keys())

    assert columns == {
        "id",
        "workflow_id",
        "email_account_id",
        "user_id",
        "workflow_type",
        "provider",
        "message_id",
        "thread_id",
        "status",
        "state",
        "created_at",
        "updated_at",
        "closed_at",
    }
