# test.py

import sys
import unittest
import requests
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication

# ——— Zorg voor precies één QApplication voor alle UI-tests ———
app = QApplication.instance() or QApplication(sys.argv)


# ——— StockInfo Tests ———
import stock_info

class StockInfoTests(unittest.TestCase):
    def setUp(self):
        # patch get_auth_header zodat we geen echte token nodig hebben
        p1 = patch('stock_info.get_auth_header', return_value={'Authorization': 'Bearer dummy'})
        self.mock_auth = p1.start()
        self.addCleanup(p1.stop)

        # patch requests.post
        p2 = patch('stock_info.requests.post')
        self.mock_post = p2.start()
        self.addCleanup(p2.stop)

    def _make_response(self, status_code=200, json_data=None):
        resp = MagicMock()
        resp.status_code = status_code
        # raise HTTPError bij niet-2xx
        def raise_if_needed():
            if not (200 <= status_code < 300):
                raise requests.exceptions.HTTPError(f"HTTP {status_code}")
        resp.raise_for_status.side_effect = raise_if_needed
        resp.json.return_value = json_data or {}
        return resp

    def test_successful_detail(self):
        data = {"item": {"code": "C25/00039", "name": "OK"}}
        payload = {"IsError": False, "Data": data}
        self.mock_post.return_value = self._make_response(200, payload)

        result = stock_info.get_item_detail_stockinfo("C25/00039")
        self.assertEqual(result, data)

    def test_http_error_raises_runtime(self):
        # Simuleer 500
        self.mock_post.return_value = self._make_response(500, None)
        with self.assertRaises(RuntimeError) as cm:
            stock_info.get_item_detail_stockinfo("C25/00039")
        self.assertIn("Fout tijdens verzoek naar stockinfo", str(cm.exception))

    def test_api_error_flag_raises_value(self):
        payload = {"IsError": True, "ErrorMessage": "FAIL"}
        self.mock_post.return_value = self._make_response(200, payload)
        with self.assertRaises(ValueError) as cm:
            stock_info.get_item_detail_stockinfo("C25/00039")
        self.assertIn("API-fout: FAIL", str(cm.exception))

    def test_invalid_data_type_raises_type(self):
        payload = {"IsError": False, "Data": [1,2,3]}
        self.mock_post.return_value = self._make_response(200, payload)
        with self.assertRaises(TypeError) as cm:
            stock_info.get_item_detail_stockinfo("C25/00039")
        self.assertIn("Detailresponse is geen dictionary", str(cm.exception))


# ——— UI MainWindow Tests ———
import ui_main

class MainUiTests(unittest.TestCase):
    def setUp(self):
        # patch send_data_request in ui_main zodat er geen echte HTTP-call gaat
        p = patch('ui_main.send_data_request')
        self.mock_send = p.start()
        self.addCleanup(p.stop)

    def make_window(self):
        win = ui_main.MainWindow()
        # nodig om alle widgets te initialiseren
        win.show()
        return win

    def test_empty_search_no_call(self):
        win = self.make_window()
        win.input_field.setText("")  
        win.perform_search()

        self.mock_send.assert_not_called()
        self.assertEqual(win.table.rowCount(), 0)
        self.assertEqual(win.result_count_label.text(), "Aantal resultaten: 0")

    def test_standard_search(self):
        dummy = [
            {"ItemCode": "A1", "ItemName": "Name1", "SuppCatNum": "SC1"},
            {"ItemCode": "B2", "ItemName": "Name2", "SuppCatNum": "SC2"}
        ]
        self.mock_send.return_value = dummy

        win = self.make_window()
        win.input_field.setText("foo")
        win.search_type_select.setCurrentText("Standaard")
        win.mode_select.setCurrentText("OR")
        win.perform_search()

        # NB: project_search=False, is_closed=""
        self.mock_send.assert_called_once_with("foo", "OR", project_search=False, is_closed="")
        self.assertEqual(win.table.rowCount(), 2)
        self.assertEqual(win.table.item(0, 1).text(), "A1")
        self.assertEqual(win.result_count_label.text(), "Aantal resultaten: 2")

    def test_search_error_shows_in_table(self):
        self.mock_send.side_effect = Exception("BOEM")

        win = self.make_window()
        win.input_field.setText("bar")
        win.search_type_select.setCurrentText("Standaard")
        win.mode_select.setCurrentText("AND")
        win.perform_search()

        self.assertEqual(win.table.rowCount(), 1)
        # Header van kolom 0
        self.assertEqual(win.table.horizontalHeaderItem(0).text(), "Fout")
        self.assertIn("BOEM", win.table.item(0, 0).text())

    def test_project_search(self):
        dummy = [{"ItemCode": "P1", "ItemName": "Proj1", "SuppCatNum": "PC1"}]
        self.mock_send.return_value = dummy

        win = self.make_window()
        win.input_field.setText("C25/00039")
        win.search_type_select.setCurrentText("Project")
        win.mode_select.setCurrentText("AND")
        win.perform_search()

        # In perform_search nu met project_search=True en is_closed=""
        self.mock_send.assert_called_once_with(
            "C25/00039",
            "AND",
            project_search=True,
            is_closed=""
        )
        self.assertEqual(win.table.rowCount(), 1)
        self.assertEqual(win.result_count_label.text(), "Aantal resultaten: 1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
