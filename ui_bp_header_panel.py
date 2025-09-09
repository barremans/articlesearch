# ui_bp_header_panel.py
from PySide6.QtWidgets import QWidget, QGridLayout, QTextBrowser
from PySide6.QtCore import Qt
from ui_bp_helper import (
    make_caption_label, make_value_label, map_card_type,
    build_place, set_html_or_text, fmt_num,
    extract_bp_core, rich_html
)

SPACER_H = 12  # hoogte van de lege rij tussen 'Adres 2' en 'Plaats'

class HeaderPanel(QWidget):
    """
    Bovenste ‘basisgegevens’-blok met 3 kolommen:
      - Links: partner + 2 compacte blokken (A en B)
      - Midden: Notes / Free text
      - Rechts: Financieel (vulbaar via BP of CreditControl)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # ===== Hoofdgrid =====
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(6, 6, 6, 6)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(4)

        self.grid.setColumnStretch(0, 0)
        self.grid.setColumnStretch(1, 1)
        self.grid.setColumnStretch(2, 0)
        self.grid.setColumnStretch(3, 5)   # editors groot & iets naar links
        self.grid.setColumnStretch(4, 0)
        self.grid.setColumnStretch(5, 2)

        # ---------------- Left column: Partner code/naam ----------------
        r_left = 0

        def add_left_row(caption: str):
            nonlocal r_left
            c = make_caption_label(caption)
            v = make_value_label()
            self.grid.addWidget(c, r_left, 0)
            self.grid.addWidget(v, r_left, 1)
            r_left += 1
            return c, v

        self.code_c, self.code_v = add_left_row("Partner code:")
        self.name_c, self.name_v = add_left_row("Partner naam:")

        # kleine ruimte vóór blok A
        self.grid.setRowMinimumHeight(r_left, 4)
        r_left += 1

        # ---------------- Blok A: Type → GSM ----------------
        blockA = QWidget(self)
        blockA_grid = QGridLayout(blockA)
        blockA_grid.setContentsMargins(0, 0, 0, 0)
        blockA_grid.setHorizontalSpacing(12)
        blockA_grid.setVerticalSpacing(0)  # compact; spacer-rij komt er expliciet bij
        blockA.setMaximumWidth(420)

        ba_r = 0

        def add_blockA_row(caption: str, *, wordwrap=False):
            nonlocal ba_r
            c = make_caption_label(caption)
            v = make_value_label()
            if wordwrap:
                v.setWordWrap(True)
            blockA_grid.addWidget(c, ba_r, 0)
            blockA_grid.addWidget(v, ba_r, 1)
            ba_r += 1
            return c, v

        self.type_c,  self.type_v  = add_blockA_row("Type Partner:")
        self.addr_c,  self.addr_v  = add_blockA_row("Adres:",  wordwrap=True)
        self.addr2_c, self.addr2_v = add_blockA_row("Adres 2:", wordwrap=True)

        # === Lege spacer-rij tussen 'Adres 2' en 'Plaats' ===
        spacer = QWidget()
        spacer.setFixedHeight(SPACER_H)
        blockA_grid.addWidget(spacer, ba_r, 0, 1, 2)
        ba_r += 1

        self.place_c, self.place_v = add_blockA_row("Plaats:")
        self.tel1_c,  self.tel1_v  = add_blockA_row("Tel. 1:")
        self.tel2_c,  self.tel2_v  = add_blockA_row("Tel. 2:")
        self.gsm_c,   self.gsm_v   = add_blockA_row("GSM:")

        self.grid.addWidget(blockA, r_left, 0, 1, 2)
        r_left += 1

        # ruimte tussen blok A en B
        self.grid.setRowMinimumHeight(r_left, 12)
        r_left += 1

        # ---------------- Blok B: Contact → Actief ----------------
        blockB = QWidget(self)
        blockB_grid = QGridLayout(blockB)
        blockB_grid.setContentsMargins(0, 0, 0, 0)
        blockB_grid.setHorizontalSpacing(12)
        blockB_grid.setVerticalSpacing(0)
        blockB.setMaximumWidth(420)

        bb_r = 0

        def add_blockB_row(caption: str):
            nonlocal bb_r
            c = make_caption_label(caption)
            v = make_value_label()
            blockB_grid.addWidget(c, bb_r, 0)
            blockB_grid.addWidget(v, bb_r, 1)
            bb_r += 1
            return c, v

        self.contact_c, self.contact_v = add_blockB_row("Contact Pers.:")
        self.mail_c,    self.mail_v    = add_blockB_row("Mail:")
        self.email_c,   self.email_v   = add_blockB_row("Email:")
        self.vat_c,     self.vat_v     = add_blockB_row("BTW:")
        self.valid_c,   self.valid_v   = add_blockB_row("Actief:")

        self.grid.addWidget(blockB, r_left, 0, 1, 2)
        r_left += 1

        # ---------------- Middenkolom ----------------
        r_mid = 0
        self.notes_c = make_caption_label("Notes:")
        self.notes_v = QTextBrowser()
        self.notes_v.setOpenExternalLinks(True)
        self.notes_v.setMinimumHeight(150)
        self.grid.addWidget(self.notes_c, r_mid, 2)
        self.grid.addWidget(self.notes_v, r_mid, 3, 5, 1)
        r_mid += 5

        self.free_c = make_caption_label("Free text:")
        self.free_v = QTextBrowser()
        self.free_v.setOpenExternalLinks(True)
        self.free_v.setMinimumHeight(150)
        self.grid.addWidget(self.free_c, r_mid, 2)
        self.grid.addWidget(self.free_v, r_mid, 3, 5, 1)

        # ---------------- Rechterkolom (financieel) ----------------
        self.finPanel = QWidget(self)
        fin_grid = QGridLayout(self.finPanel)
        fin_grid.setContentsMargins(0, 0, 0, 0)
        fin_grid.setHorizontalSpacing(12)
        fin_grid.setVerticalSpacing(0)

        r_fin = 0

        def add_fin_row(caption: str):
            nonlocal r_fin
            c = make_caption_label(caption)
            v = make_value_label()
            fin_grid.addWidget(c, r_fin, 0)
            fin_grid.addWidget(v, r_fin, 1)
            r_fin += 1
            return c, v

        self.cur_c,    self.cur_v    = add_fin_row("Valuta:")
        self.clim_c,   self.clim_v   = add_fin_row("Krediet Limit:")
        self.bal_c,    self.bal_v    = add_fin_row("Balance:")
        self.oo_c,     self.oo_v     = add_fin_row("Total open orders:")
        self.oln_c,    self.oln_v    = add_fin_row("Total open leveringen:")
        self.ofa_c,    self.ofa_v    = add_fin_row("Open facturen:")
        self.odp_c,    self.odp_v    = add_fin_row("Open voorschotten:")
        self.ocn_c,    self.ocn_v    = add_fin_row("Open krediet notes:")
        self.ocred_c,  self.ocred_v  = add_fin_row("Totaal open waarde:")
        self.avail_c,  self.avail_v  = add_fin_row("Beschikbaar krediet:")
        self.stat_c,   self.stat_v   = add_fin_row("Krediet status:")
        self.used_c,   self.used_v   = add_fin_row("% opgebruikte kredit:")
        self.pg_c,     self.pg_v     = add_fin_row("Betalingsconditie:")
        self.upd_c,    self.upd_v    = add_fin_row("Laatste update:")
        self.inv_c,    self.inv_v    = add_fin_row("Laatste factuur datum:")

        self.iban_c,   self.iban_v   = add_fin_row("IBAN:")
        self.iban2_c,  self.iban2_v  = add_fin_row("IBAN 2:")

        self.grid.addWidget(self.finPanel, 0, 4, max(r_left, r_mid + 5), 2)

    # ---------------- API ----------------
    def clear(self):
        for v in [
            self.code_v, self.name_v,
            self.type_v, self.addr_v, self.addr2_v, self.place_v,
            self.tel1_v, self.tel2_v, self.gsm_v,
            self.contact_v, self.mail_v, self.email_v, self.vat_v, self.valid_v,
            self.cur_v,
            self.clim_v, self.bal_v, self.oo_v, self.oln_v,
            self.ofa_v, self.odp_v, self.ocn_v, self.ocred_v,
            self.avail_v, self.stat_v, self.used_v, self.pg_v, self.upd_v, self.inv_v,
            self.iban_v, self.iban2_v
        ]:
            v.setText("-")
        self.notes_v.setHtml("<i>-</i>")
        self.free_v.setHtml("<i>-</i>")

    # ------ BP basis + vrije tekst ------
    def fill_left_and_middle(self, bp: dict):
        core = extract_bp_core(bp)

        # boven
        self.code_v.setText(str(core.get("CardCode") or "-"))
        self.name_v.setText(str(core.get("CardName") or "-"))

        # blok A
        self.type_v.setText(map_card_type(str(core.get("CardType") or "")))
        self.addr_v.setText(str(core.get("Address") or "-"))
        self.addr2_v.setText(str(core.get("MailAddres") or "-"))
        self.place_v.setText(build_place(core.get("Country"), core.get("ZipCode"), core.get("City")))
        self.tel1_v.setText(str(core.get("Phone1") or "-"))
        self.tel2_v.setText(str(core.get("Phone2") or "-"))
        self.gsm_v.setText(str(core.get("Cellular") or "-"))

        # blok B
        self.contact_v.setText(str(core.get("ContactPerson") or "-"))
        self.mail_v.setText(str(core.get("MailAddres") or "-"))
        self.email_v.setText(str(core.get("EmailAddress") or "-"))
        self.vat_v.setText(str(core.get("FederalTaxID") or "-"))
        self.valid_v.setText("Ja" if str(core.get("Valid")).upper() == "Y" else "Nee")

        # midden
        set_html_or_text(self.notes_v, core.get("Notes"))
        set_html_or_text(self.free_v,  core.get("Free_Text"))

        # IBANs
        self.iban_v.setText(str(core.get("IBAN") or "-"))
        self.iban2_v.setText(str(core.get("HouseBankIBAN") or "-"))

        # Valuta meteen meenemen wanneer BP geladen werd
        self.cur_v.setText(str(core.get("Currency") or "-"))

    # ------ Rechterkolom met BP-fallback ------
    def fill_financial_bp(self, bp: dict):
        core = extract_bp_core(bp)
        self.cur_v.setText(str(core.get("Currency") or "-"))
        self.clim_v.setText(fmt_num(core.get("CreditLimit")))
        self.bal_v.setText(fmt_num(core.get("CurrentAccountBalance")))
        self.oln_v.setText(fmt_num(core.get("OpenDeliveryNotesBalance")))
        self.oo_v.setText(fmt_num(core.get("OpenOrdersBalance")))
        for v in [
            self.ofa_v, self.odp_v, self.ocn_v, self.ocred_v,
            self.avail_v, self.stat_v, self.used_v, self.pg_v, self.upd_v, self.inv_v
        ]:
            v.setText("-")

    # ------ Rechterkolom met CreditControl-data ------
    def fill_financial_cc(self, cc: dict):
        data = cc.get("BP", cc) if isinstance(cc, dict) else {}

        def fmt_pct(v):
            return f"{float(v):.2f} %" if isinstance(v, (int, float)) else "-"

        self.clim_v.setText(fmt_num(data.get("CreditLimit")))
        self.bal_v.setText(fmt_num(data.get("CurrentBalance")))
        self.oo_v.setText(fmt_num(data.get("TotalOpenOrders")))
        self.oln_v.setText(fmt_num(data.get("TotalOpenDeliveries")))
        self.ofa_v.setText(fmt_num(data.get("TotalOpenInvoices")))
        self.odp_v.setText(fmt_num(data.get("TotalOpenDownPayments")))
        self.ocn_v.setText(fmt_num(data.get("Info_TotalOpenCN")))
        self.ocred_v.setText(fmt_num(data.get("OpenCredit")))

        # Beschikbaar krediet → negatief in rood + vet
        avail = data.get("AvailableCredit")
        if isinstance(avail, (int, float)) and avail < 0:
            self.avail_v.setText(rich_html(fmt_num(avail), danger=True, bold=True))
        else:
            self.avail_v.setText(fmt_num(avail))

        # Krediet status
        status = str(data.get("CreditStatus") or "-").strip()
        if status.lower() == "over limit":
            self.stat_v.setText(f'❗ {rich_html(status, danger=True, bold=True)}')
        else:
            self.stat_v.setText(status)

        # % opgebruikte krediet
        used = data.get("CreditUsagePercent")
        if isinstance(used, (int, float)) and used > 100:
            self.used_v.setText(rich_html(fmt_pct(used), danger=True, bold=True))
        else:
            self.used_v.setText(fmt_pct(used))

        self.pg_v.setText(str(data.get("PaymentGroup") or "-"))
        self.upd_v.setText(str(data.get("LastUpdate") or "-"))
        self.inv_v.setText(str(data.get("LastInvoiceDate") or "-"))
