class WorkpackageCreationError(RuntimeError):
    """Raised when creating a work package in OpenProject fails."""


class AttachmentUploadError(RuntimeError):
    """Raised when uploading one or more attachments fails after ticket creation."""