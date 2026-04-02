class ExecutorError(Exception):
    pass


class ActionExecutionError(ExecutorError):
    pass


class ActionTranslationError(ExecutorError):
    pass
