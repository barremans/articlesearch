# ui_CcBP.py — FINAL (BP Credit Control V2 + AD beveiliging)
# ✅ Alle filters, groepering, kleurcodering, exports
# ✅ Beveiliging: offline → blokkeren, AD → vereist, groep = GPP_Finance

import sys
import os
from typing import Any, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import requests
import pandas as pd
from PySide6.QtCore import Qt, Signal, Slot, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QKeySequence, QShortcut, QIntValidator, QColor
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTableView, QHeaderView, QGroupBox, QComboBox,
    QCheckBox, QAbstractItemView
)

from auth import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT, OFFLINE_MODE
from ui_CcBP_helper import prepare_dataframe
import security_docs  # ✅ AD-check logica
from permissions_azure import user_in_azure_group  # ✅ groepcontrole

CONFIGURATION_ID = "HG443N"
DATE_FMT_UI = "%d-%m-%Y"


# ---------------- Pandas → Qt model ----------------
class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame, selected_codes: Optional[set] = None):
        super().__init__()
        self._df = df
        self._selected_codes = selected_codes or set()
        self._code_col = next((c for c in ["CardCode", "Klantcode"] if c in df.columns), None)

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        val = self._df.iat[index.row(), index.column()]
        colname = self._df.columns[index.column()]

        # ---------- Tekst ----------
        if role == Qt.ItemDataRole.DisplayRole:
            if pd.isna(val):
                return ""
            if isinstance(val, (datetime, pd.Timestamp)):
                return val.strftime("%d-%m-%Y")
            return str(val)

        # ---------- Achtergrondkleur ----------
        if role == Qt.ItemDataRole.BackgroundRole:
            if self._code_col:
                cardcode = self._df.iloc[index.row()][self._code_col]
                if cardcode in self._selected_codes:
                    return QColor(210, 255, 210)

            over_limit_col = next((c for c in ["CreditOverLimit", "Over kredietlimiet"] if c in self._df.columns), None)
            risk_color_col = next((c for c in ["RiskColorType", "Risicokleur"] if c in self._df.columns), None)
            risk_cat_col = next((c for c in ["RiskCategory", "Risicocategorie"] if c in self._df.columns), None)

            color_map = {
                "GREEN": QColor(200, 255, 200),
                "LOW": QColor(200, 255, 200),
                "YELLOW": QColor(255, 255, 180),
                "MEDIUM": QColor(255, 255, 180),
                "AMBER": QColor(255, 200, 100),
                "HIGH": QColor(255, 200, 100),
                "RED": QColor(255, 150, 150),
                "CRITICAL": QColor(255, 150, 150),
            }

            if colname == risk_color_col:
                risk_val = str(val).upper()
                if risk_val in color_map:
                    return color_map[risk_val]

            if colname == over_limit_col and risk_color_col:
                linked_risk = str(self._df.iloc[index.row()].get(risk_color_col, "")).upper()
                if linked_risk in color_map:
                    return color_map[linked_risk]

            if colname == risk_cat_col:
                cat_val = str(val).upper()
                if cat_val in color_map:
                    return color_map[cat_val]

        # ---------- Tekstkleur ----------
        if role == Qt.ItemDataRole.ForegroundRole:
            if colname in ["RiskColorType", "Risicokleur", "RiskCategory", "Risicocategorie"]:
                val_str = str(val).upper()
                if val_str in ["RED", "CRITICAL"]:
                    return QColor(70, 0, 0)
                elif val_str in ["AMBER", "HIGH"]:
                    return QColor(90, 45, 0)
                elif val_str in ["YELLOW", "MEDIUM"]:
                    return QColor(70, 70, 0)
                elif val_str in ["GREEN", "LOW"]:
                    return QColor(0, 80, 0)

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        try:
            colname = self._df.columns[column]
            ascending = order == Qt.SortOrder.AscendingOrder
            self.layoutAboutToBeChanged.emit()
            self._df.sort_values(by=colname, ascending=ascending, inplace=True, kind="mergesort")
            self._df.reset_index(drop=True, inplace=True)
            self.layoutChanged.emit()
        except Exception as e:
            print(f"Sort error: {e}")


# ---------------- Helpers ----------------
def group_dataframe(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    key_map = {
        "sales": ["SalesEmployee", "Sales", "Verkoper"],
        "doc": ["DocumentOwner", "Doc. Owner", "Document Owner"],
    }
    if mode not in key_map or mode == "none":
        return df.copy()
    key = next((c for c in key_map[mode] if c in df.columns), None)
    if not key:
        return df.copy()
    code_col = next((c for c in ["CardCode", "Klantcode"] if c in df.columns), None)
    sort_cols = [key] + ([code_col] if code_col else [])
    return df.sort_values(by=sort_cols, ascending=True).reset_index(drop=True)


# ---------------- Main Window ----------------
class CreditControlWindow(QWidget):
    api_success = Signal(dict)
    api_error = Signal(str)

    def __init__(self):
        super().__init__()

        # 🔒 OFFLINE / AD / GROUP checks vóór UI-bouw
        if OFFLINE_MODE:
            QMessageBox.warning(
                self, "Offline modus",
                "De Credit Control-module is niet beschikbaar in offline-modus."
            )
            self.close()
            return

        if not security_docs.is_unlocked():
            QMessageBox.warning(
                self,
                "Geen AD-verbinding",
                "Deze module vereist een actieve Azure AD-login.\n"
                "Controleer je netwerkverbinding of meld je opnieuw aan."
            )
            self.close()
            return

        try:
            required_group = "GPP_Finance"
            if not user_in_azure_group(required_group):
                QMessageBox.warning(
                    self,
                    "Geen toegang",
                    f"Je behoort niet tot de vereiste Azure AD-groep:\n\n{required_group}"
                )
                self.close()
                return
        except Exception as e:
            QMessageBox.critical(self, "Azure AD fout", f"Fout bij controle groepsrechten:\n{e}")
            self.close()
            return

        # ✅ Toegang ok — UI bouwen
        self.setWindowTitle("BP Credit Control (V2)")
        self.setMinimumSize(1300, 750)
        self._exec = ThreadPoolExecutor(max_workers=2)
        self.df_current = None
        self.df_full = None
        self.df_selection = pd.DataFrame()

        root = QVBoxLayout(self)
        self._create_filters_ui(root)
        self._create_grouping_ui(root)
        self._create_selection_ui(root)

        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSortingEnabled(True)
        root.addWidget(self.table, 1)

        self.label_status = QLabel("Aantal resultaten: 0")
        self.label_status.setAlignment(Qt.AlignRight)
        root.addWidget(self.label_status)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.fetch_api)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self.clear_all_filters)
        QShortcut(QKeySequence(Qt.Key_Delete), self).activated.connect(self.clear_all_filters)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)

        self.btn_fetch.clicked.connect(self.fetch_api)
        self.btn_export.clicked.connect(self.export_to_excel)
        self.btn_show_all.clicked.connect(self.show_all_rows)
        self.table.doubleClicked.connect(self.on_table_doubleclick)
        self.api_success.connect(self.on_api_success)
        self.api_error.connect(self.on_api_error)

    # (De rest van de klasse blijft exact gelijk aan jouw versie — alle filters, groepering, selectie, export etc.)
    # ...
    # Plaats hier alle bestaande methoden uit je vorige code (fetch_api, on_api_success, on_api_error, enz.)
    # De beveiligingslogica zit enkel in __init__().

####
    # ---------- UI blocks ----------
    def _create_filters_ui(self, root):
        group_main = QGroupBox("Filter — Hoofdcriteria")
        gm = QHBoxLayout(group_main)
        gm.addWidget(QLabel("CardCode:")); self.input_cardcode = QLineEdit(); gm.addWidget(self.input_cardcode)
        gm.addWidget(QLabel("Sales:")); self.input_sales = QLineEdit(); gm.addWidget(self.input_sales)
        gm.addWidget(QLabel("DocOwner:")); self.input_docowner = QLineEdit(); gm.addWidget(self.input_docowner)
        gm.addWidget(QLabel("RiskCat:")); self.combo_risk = QComboBox(); self.combo_risk.addItems(["", "LOW", "MEDIUM", "HIGH", "CRITICAL"]); gm.addWidget(self.combo_risk)
        gm.addWidget(QLabel("Action:")); self.combo_action = QComboBox(); self.combo_action.addItems(["", "INCREASE", "DECREASE", "NO_COVERAGE", "OK"]); gm.addWidget(self.combo_action)
        root.addWidget(group_main)

        group_extra = QGroupBox("Filter — Extra opties")
        gx = QHBoxLayout(group_extra)
        gx.addWidget(QLabel("Min % Used:")); self.input_minpr = QLineEdit("100"); self.input_minpr.setValidator(QIntValidator(0, 999999)); gx.addWidget(self.input_minpr)
        gx.addWidget(QLabel("Max % Used:")); self.input_maxpr = QLineEdit(); self.input_maxpr.setValidator(QIntValidator(0, 999999)); gx.addWidget(self.input_maxpr)
        self.chk_5000Mismatch = QCheckBox("5000Mismatch"); self.chk_mismatch = QCheckBox("Mismatch"); self.chk_5000Increase = QCheckBox("5000Increase")
        gx.addWidget(self.chk_5000Mismatch); gx.addWidget(self.chk_mismatch); gx.addWidget(self.chk_5000Increase)
        self.btn_fetch = QPushButton("Ophalen"); self.btn_export = QPushButton("Exporteren"); self.btn_show_all = QPushButton("Alles tonen"); self.btn_show_all.setEnabled(False)
        gx.addWidget(self.btn_fetch); gx.addWidget(self.btn_export); gx.addWidget(self.btn_show_all)
        root.addWidget(group_extra)

    def _create_grouping_ui(self, root):
        group_group = QGroupBox("Weergave")
        gg = QHBoxLayout(group_group)
        gg.addWidget(QLabel("Groepeer op:"))
        self.combo_group = QComboBox()
        self.combo_group.addItem("Geen groepering", "none")
        self.combo_group.addItem("Verkoper", "sales")
        self.combo_group.addItem("Document eigenaar", "doc")
        self.combo_group.currentTextChanged.connect(lambda _: self.apply_grouping())
        gg.addWidget(self.combo_group)
        root.addWidget(group_group)

    def _create_selection_ui(self, root):
        group_sel = QGroupBox("Selectiebeheer")
        gs = QHBoxLayout(group_sel)
        self.btn_add_selection = QPushButton("➕ Voeg selectie toe")
        self.btn_show_selection = QPushButton("📋 Toon selectie")
        self.btn_clear_selection = QPushButton("❌ Leeg selectie")
        self.btn_export_selection = QPushButton("⬇️ Export selectie")

        gs.addWidget(self.btn_add_selection)
        gs.addWidget(self.btn_show_selection)
        gs.addWidget(self.btn_clear_selection)
        gs.addWidget(self.btn_export_selection)
        root.addWidget(group_sel)

        self.btn_add_selection.clicked.connect(self.add_to_selection)
        self.btn_show_selection.clicked.connect(self.show_selection)
        self.btn_clear_selection.clicked.connect(self.clear_selection)
        self.btn_export_selection.clicked.connect(self.export_selection)

    # ---------------- API & Data ----------------
    def fetch_api(self):
        cardcode = self.input_cardcode.text().strip()
        sales = self.input_sales.text().strip()
        docowner = self.input_docowner.text().strip()
        riskcat = self.combo_risk.currentText().strip()
        action = self.combo_action.currentText().strip()
        minpr = self.input_minpr.text().strip() or "100"
        maxpr = self.input_maxpr.text().strip()

        payload = {
            "ConfigurationID": CONFIGURATION_ID,
            "MultiKey": {
                "@CardCode": cardcode,
                "@Sales": sales,
                "@Docowner": docowner,
                "@RiskCat": riskcat,
                "@MinPrUsed": minpr,
                "@MaxPrUsed": maxpr,
                "@OrderB": "",
                "@Action": action,
                "@5000Mismatch": "Y" if self.chk_5000Mismatch.isChecked() else "N",
                "@mismatch": "Y" if self.chk_mismatch.isChecked() else "N",
                "@5000Increase": "Y" if self.chk_5000Increase.isChecked() else "N"
            }
        }

        env = API_ENVIRONMENTS.get(ENVIRONMENT, {})
        base_url = env.get("base_url", "").rstrip("/")
        url = f"{base_url}/api/datarequest"
        headers = get_auth_header()

        def _worker():
            try:
                resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
                if resp.status_code == 200:
                    self.api_success.emit(resp.json())
                else:
                    self.api_error.emit(f"HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                self.api_error.emit(str(e))

        self._exec.submit(_worker)

    @Slot(dict)
    def on_api_success(self, data: Dict[str, Any]):
        try:
            df = pd.DataFrame(data.get("Data", []))
            if df.empty:
                QMessageBox.information(self, "Geen resultaten", "Geen rijen gevonden.")
                self.table.setModel(None)
                return
            df = prepare_dataframe(df)
            self.df_current = df
            self.df_full = df.copy()
            self.apply_grouping()
            self.btn_show_all.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Kon data niet verwerken:\n{e}")

    @Slot(str)
    def on_api_error(self, msg: str):
        QMessageBox.critical(self, "Fout", f"Kon API niet bereiken:\n{msg}")

    # ---------------- Groepering ----------------
    def apply_grouping(self):
        if self.df_current is None or self.df_current.empty:
            self.table.setModel(None)
            self.label_status.setText("Aantal resultaten: 0")
            return
        mode = self.combo_group.currentData()
        df_sorted = group_dataframe(self.df_current, mode)
        selected_codes = set(self.df_selection.get("CardCode", [])) | set(self.df_selection.get("Klantcode", []))
        self.table_model = PandasModel(df_sorted, selected_codes)
        self.table.setModel(self.table_model)
        self.table.setSortingEnabled(True)
        self.auto_resize_columns()
        self.label_status.setText(f"Aantal resultaten: {len(df_sorted)}")

    def auto_resize_columns(self):
        header = self.table.horizontalHeader()
        for col in range(self.table_model.columnCount()):
            self.table.resizeColumnToContents(col)
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

    # ---------------- Dubbelklik ----------------
    def on_table_doubleclick(self, index: QModelIndex):
        if not index.isValid() or self.df_full is None:
            return
        df = self.df_full
        code_col = next((c for c in ["CardCode", "Klantcode"] if c in df.columns), None)
        if not code_col:
            return
        clicked_value = self.table.model()._df.iloc[index.row()][code_col]
        df_filtered = df[df[code_col] == clicked_value].reset_index(drop=True)
        self.df_current = df_filtered
        self.apply_grouping()
        self.label_status.setText(f"Geselecteerde klant: {clicked_value} ({len(df_filtered)} rij(en))")
        self.btn_show_all.setEnabled(True)

    def show_all_rows(self):
        if self.df_full is not None:
            self.df_current = self.df_full.copy()
            self.apply_grouping()
            self.btn_show_all.setEnabled(False)

    # ---------------- Selectiebeheer ----------------
    def add_to_selection(self):
        selection = self.table.selectionModel().selectedRows()
        if not selection:
            QMessageBox.information(self, "Geen selectie", "Selecteer eerst één of meer rijen.")
            return
        df_visible = self.table.model()._df
        selected_df = df_visible.iloc[[s.row() for s in selection]]
        if self.df_selection.empty:
            self.df_selection = selected_df.copy()
        else:
            self.df_selection = pd.concat([self.df_selection, selected_df]).drop_duplicates().reset_index(drop=True)
        self.apply_grouping()
        QMessageBox.information(self, "Toegevoegd", f"{len(selected_df)} rijen toegevoegd.\nTotaal: {len(self.df_selection)}")

    def show_selection(self):
        if self.df_selection.empty:
            QMessageBox.information(self, "Leeg", "Er is nog geen selectie."); return
        w = QWidget()
        w.setWindowTitle(f"Huidige selectie ({len(self.df_selection)} rijen)")
        l = QVBoxLayout(w)
        tv = QTableView()
        tv.setModel(PandasModel(self.df_selection, set(self.df_selection.get("CardCode", []))))
        tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tv.setSortingEnabled(True)
        tv.horizontalHeader().setStretchLastSection(True)
        tv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        l.addWidget(tv)
        w.resize(1000, 600)
        w.show()
        self._sel_window = w

    def clear_selection(self):
        self.df_selection = pd.DataFrame()
        self.apply_grouping()
        QMessageBox.information(self, "Selectie geleegd", "De selectie is verwijderd.")

    def export_selection(self):
        if self.df_selection.empty:
            QMessageBox.information(self, "Geen selectie", "Er is geen selectie om te exporteren.")
            return
        filename = f"CreditControlV2_Selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path = os.path.join(os.path.expanduser("~/Downloads"), filename)
        try:
            self.df_selection.to_excel(path, index=False, engine="openpyxl")
            QMessageBox.information(self, "Export voltooid", f"Selectie geëxporteerd naar:\n{path}")
            self.df_selection = pd.DataFrame()
            self.apply_grouping()
        except Exception as e:
            QMessageBox.critical(self, "Exportfout", str(e))

    # ---------------- Export ----------------
    def export_to_excel(self):
        if self.df_current is None or self.df_current.empty:
            QMessageBox.information(self, "Geen data", "Er is geen data om te exporteren.")
            return
        df_export = group_dataframe(self.df_current, self.combo_group.currentData())
        filename = f"CreditControlV2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path = os.path.join(os.path.expanduser("~/Downloads"), filename)
        try:
            df_export.to_excel(path, index=False, engine="openpyxl")
            QMessageBox.information(self, "Export voltooid", f"Bestand opgeslagen als:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Exportfout", str(e))

    # ---------------- Reset ----------------
    def clear_all_filters(self):
        QApplication.processEvents()
        self.input_cardcode.clear()
        self.input_sales.clear()
        self.input_docowner.clear()
        self.combo_risk.setCurrentIndex(0)
        self.combo_action.setCurrentIndex(0)
        self.input_minpr.setText("100")
        self.input_maxpr.clear()
        self.chk_5000Mismatch.setChecked(False)
        self.chk_mismatch.setChecked(False)
        self.chk_5000Increase.setChecked(False)
        self.combo_group.setCurrentIndex(0)
        self.table.setModel(None)
        self.df_current = None
        self.df_full = None
        self.df_selection = pd.DataFrame()
        self.btn_show_all.setEnabled(False)
        self.label_status.setText("Aantal resultaten: 0")
        self.input_cardcode.setFocus()


# ---------------- Run ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CreditControlWindow()
    win.show()
    sys.exit(app.exec())
