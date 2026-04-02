from __future__ import annotations

from pathlib import Path


def configs_root(path: Path) -> Path:
    resolved = Path(path).resolve()
    for candidate in resolved.parents:
        if candidate.name == "configs":
            return candidate
    raise ValueError(f"unable to resolve configs root from path={resolved}")


def resolve_config_reference(base_path: Path, relative_ref: str, allowed_root: Path) -> Path:
    base_file = Path(base_path).resolve()
    target_path = (base_file.parent / str(relative_ref)).resolve()
    normalized_allowed_root = Path(allowed_root).resolve()

    try:
        target_path.relative_to(normalized_allowed_root)
    except ValueError as exc:
        raise ValueError(
            "config reference escapes allowed root: "
            f"base={base_file} ref={relative_ref} allowed_root={normalized_allowed_root}"
        ) from exc

    return target_path
