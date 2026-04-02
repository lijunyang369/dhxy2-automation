from __future__ import annotations

import sys
import unittest
from pathlib import Path

from scripts.launch_dhxy2_platform import (
    _ensure_project_root_on_sys_path,
    _resolve_project_root,
)


class LaunchDhxy2PlatformScriptTestCase(unittest.TestCase):
    def test_resolve_project_root_points_to_repository_root(self) -> None:
        project_root = _resolve_project_root()

        self.assertEqual("dhxy2-automation", project_root.name)
        self.assertTrue((project_root / "src").is_dir())
        self.assertTrue((project_root / "scripts").is_dir())

    def test_ensure_project_root_on_sys_path_inserts_root_once(self) -> None:
        project_root = Path("virtual-project-root")
        original_sys_path = list(sys.path)
        sys.path = [entry for entry in sys.path if entry != str(project_root)]
        try:
            _ensure_project_root_on_sys_path(project_root)
            _ensure_project_root_on_sys_path(project_root)
            self.assertEqual(1, sys.path.count(str(project_root)))
            self.assertEqual(str(project_root), sys.path[0])
        finally:
            sys.path = original_sys_path


if __name__ == "__main__":
    unittest.main()
