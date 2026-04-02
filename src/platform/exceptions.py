class PlatformError(Exception):
    pass


class WindowNotFoundError(PlatformError):
    pass


class WindowFocusError(PlatformError):
    pass


class WindowCaptureError(PlatformError):
    pass
