# test_main_ui.py

import sys
import test
from unittest.mock import patch
from PySide6.QtWidgets import QApplication

# Ensure the QApplication exists for widget tests
@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

# Import after QApplication fixture to avoid issues
import ui_main

def make_window():
    """Helper om een verse MainWindow te krijgen voor elke test."""
    win = ui_main.MainWindow()
    # Nodig om status bar en widgets correct te initialiseren
    win.show()
    return win

def test_empty_search_no_call(qapp):
    """
    Als het zoekveld leeg is en je op Zoeken drukt,
    wordt er geen API-call gedaan en blijft de tabel leeg.
    """
    win = make_window()
    win.input_field.setText("")
    win.perform_search()

    # Geen oproep tot send_data_request én lege tabel
    assert win.table.rowCount() == 0
    assert win.result_count_label.text() == "Aantal resultaten: 0"

@patch('ui_main.send_data_request')
def test_standard_search_populates(mock_send, qapp):
    """
    Voor een standaard zoekopdracht worden zoekterm en mode
    doorgegeven en vult de tabel met de teruggegeven data.
    """
    # Dummy-antwoord uit de API
    dummy = [
        {"ItemCode": "A1", "ItemName": "Name1", "SuppCatNum": "SC1"},
        {"ItemCode": "B2", "ItemName": "Name2", "SuppCatNum": "SC2"}
    ]
    mock_send.return_value = dummy

    win = make_window()
    win.input_field.setText("foo")
    win.search_type_select.setCurrentText("Standaard")
    win.mode_select.setCurrentText("OR")

    win.perform_search()

    mock_send.assert_called_once_with("foo", "OR", project_search=False, is_closed="")
    assert win.table.rowCount() == 2
    # Kolom 1 = ItemCode
    assert win.table.item(0, 1).text() == "A1"
    assert win.result_count_label.text() == "Aantal resultaten: 2"

@patch('ui_main.send_data_request')
def test_search_error_shows_in_table(mock_send, qapp):
    """
    Bij een exception in send_data_request moet de tabel één
    rij tonen met header 'Fout' en de foutmelding.
    """
    mock_send.side_effect = Exception("BOEM")

    win = make_window()
    win.input_field.setText("bar")
    win.search_type_select.setCurrentText("Standaard")
    win.mode_select.setCurrentText("AND")

    win.perform_search()

    assert win.table.rowCount() == 1
    assert win.table.horizontalHeaderItem(0).text() == "Fout"
    assert "BOEM" in win.table.item(0, 0).text()

@patch('ui_main.send_data_request')
def test_perform_search_project(mock_send, qapp):
    """
    Voor een Project-search wordt naast term & mode ook
    project_search=True en is_closed=""
    doorgegeven aan send_data_request.
    """
    dummy = [{"ItemCode": "P1", "ItemName": "Proj1", "SuppCatNum": "PC1"}]
    mock_send.return_value = dummy

    win = make_window()
    win.input_field.setText("C25/00039")
    win.search_type_select.setCurrentText("Project")
    win.mode_select.setCurrentText("AND")

    win.perform_search()

    mock_send.assert_called_once_with(
        "C25/00039",         # zoekterm
        "AND",               # mode
        project_search=True, # project-flag
        is_closed=""         # lege filter
    )
    assert win.table.rowCount() == 1
    assert win.result_count_label.text() == "Aantal resultaten: 1"
