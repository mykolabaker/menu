class MenuAnalyzerError(Exception):
    """Base exception for menu analyzer."""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class ImageValidationError(MenuAnalyzerError):
    """Raised when image validation fails."""

    pass


class OCRError(MenuAnalyzerError):
    """Raised when OCR processing fails."""

    pass


class ParsingError(MenuAnalyzerError):
    """Raised when text parsing fails."""

    pass


class MCPError(MenuAnalyzerError):
    """Raised when MCP server communication fails."""

    pass


class MCPUnavailableError(MCPError):
    """Raised when MCP server is unreachable."""

    pass


class ReviewNotFoundError(MenuAnalyzerError):
    """Raised when review request_id is not found."""

    pass
