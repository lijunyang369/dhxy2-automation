from __future__ import annotations

from pathlib import Path

from src.app.account_loader import AccountBindingLoader
from src.platform import PyWin32WindowGateway, WindowFinder, WindowSearchCriteria, WindowSession


def resolve_window_session(
    account_config_path: Path,
    gateway: PyWin32WindowGateway | None = None,
) -> WindowSession:
    account_binding = AccountBindingLoader().load(account_config_path)
    resolved_gateway = gateway or PyWin32WindowGateway()
    finder = WindowFinder(resolved_gateway)
    return finder.find(
        WindowSearchCriteria(
            title_contains=account_binding.window.title,
            class_name=account_binding.window.class_name,
            handle=account_binding.window.handle,
            require_visible=True,
        )
    )
