from abc import ABC, abstractmethod

from app.schemas.sync import SyncChanges, SyncPage


class PaginatedEmailSyncProvider(ABC):
    """Optional capability for provider-backed paginated inbox sync."""

    @abstractmethod
    def sync_page(
        self,
        account_id: str,
        cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncPage:
        """Return one page of inbox messages and an optional next cursor."""
        raise NotImplementedError


class IncrementalEmailSyncProvider(ABC):
    """Optional capability for provider-backed incremental mailbox synchronization."""

    @abstractmethod
    def sync_changes(
        self,
        account_id: str,
        checkpoint_cursor: str | None = None,
        page_cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncChanges:
        """Return incremental mailbox changes from a checkpoint or page cursor."""
        raise NotImplementedError
