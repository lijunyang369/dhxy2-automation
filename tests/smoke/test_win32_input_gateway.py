from __future__ import annotations

import unittest
from unittest.mock import patch

from src.executor.win32_input_gateway import Win32SendInputGateway


class Win32SendInputGatewayTestCase(unittest.TestCase):
    def test_click_records_single_client_operation(self) -> None:
        gateway = Win32SendInputGateway()

        with patch("src.executor.win32_input_gateway._client_to_screen", return_value=(500, 600)):
            with patch("src.executor.win32_input_gateway._send_inputs") as send_inputs:
                gateway.click(100, 200)

        self.assertEqual([("click", (100, 200))], gateway.operations)
        send_inputs.assert_called_once()

    def test_click_screen_records_screen_operation(self) -> None:
        gateway = Win32SendInputGateway()

        with patch("src.executor.win32_input_gateway._send_inputs") as send_inputs:
            gateway.click_screen(500, 600)

        self.assertEqual([("click_screen", (500, 600))], gateway.operations)
        send_inputs.assert_called_once()


if __name__ == "__main__":
    unittest.main()
