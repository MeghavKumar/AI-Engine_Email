from app.models import EmailAccount


def test_email_account_model():
    assert EmailAccount.__tablename__ == "email_accounts"

    columns = set(EmailAccount.__table__.columns.keys())

    assert columns == {
        "id",
        "user_id",
        "provider",
        "email_address",
        "provider_account_id",
        "is_active",
        "created_at",
        "updated_at",
    }
