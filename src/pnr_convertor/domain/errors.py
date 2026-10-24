class PnrConvertorError(Exception):
    code: str = "pnr_convertor_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UnsupportedFormatError(PnrConvertorError):
    code = "unsupported_format"


class PnrParseError(PnrConvertorError):
    code = "parse_error"
