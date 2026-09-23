from typing import TypeVar

from pydantic import BaseModel

WorkflowStateT = TypeVar("WorkflowStateT", bound=BaseModel)


class WorkflowPersistenceService:
    """Serialize and restore Pydantic workflow state for database persistence."""

    def serialize(self, state: BaseModel) -> dict:
        """Convert workflow state into JSON-safe data."""
        return state.model_dump(mode="json")

    def deserialize(
        self,
        data: dict,
        state_type: type[WorkflowStateT],
    ) -> WorkflowStateT:
        """Restore typed workflow state from persisted JSON data."""
        return state_type.model_validate(data)
