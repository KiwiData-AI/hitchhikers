from enum import StrEnum


class DocumentState(StrEnum):
    NEW = "NEW"
    EXTRACTED = "EXTRACTED"
    TRANSFORMED = "TRANSFORMED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    EXTRACT_ERROR = "EXTRACT_ERROR"
    TRANSFORM_ERROR = "TRANSFORM_ERROR"
    PUBLISH_ERROR = "PUBLISH_ERROR"
    ERROR = "ERROR"
    LOCKED = "LOCKED"
    PUBLISHED = "PUBLISHED"
    DELETED = "DELETED"

    @property
    def is_in_progress(self) -> bool:
        return self in (self.NEW, self.EXTRACTED, self.TRANSFORMED)

    @property
    def is_done(self) -> bool:
        return self in (self.LOCKED, self.PUBLISHED)

    @property
    def is_error(self) -> bool:
        return self in (
            self.ERROR,
            self.EXTRACT_ERROR,
            self.TRANSFORM_ERROR,
            self.PUBLISH_ERROR,
            self.HUMAN_REVIEW,
        )
