# ui_CcBP_helper.py
"""
Helpermodule voor ui_CcBP.py
Bevat kolomvolgorde, labels en (later) kleur-/formatlogica.
"""

# -----------------------------------------------
# Kolomvolgorde: bepaalt in welke volgorde de kolommen in de tabel verschijnen.
# -----------------------------------------------
COLUMN_ORDER = [
    "CardCode",
    "CardName",
    "CreditLine",
    "Balance",
    "OpenOrders",
    "DownPayments",
    "OpenDeliveries",
    "OpenInvoices",
    "CreditExposure",
    "AvailableCredit",
    "CreditOverLimit",
    "Risk_For_CGK",
    "PercentageUsedCredit",
    "SafetyBufferPercent",
    "RiskCategory",
    "SalesEmployee",
    "DocumentOwner",
    "ProposedCreditLine",
    "SuggestedAction",
    "CreditLimitStatusText",
    "IsCreditLimitExceeded",
    "AtradiusLandGroup",
    "MaxSelfAssessmentLimit",
    "AtradiusCoveragePercent",
    "Exposure_vs_Atradius_Coverage",
    "U_UpdateDate",
    "LastInvoiceDate",
]

# -----------------------------------------------
# Kolomlabels: API-kolomnamen → leesbare namen voor de gebruiker.
# -----------------------------------------------
COLUMN_LABELS = {
    "CardCode": "Klantcode",
    "CardName": "Klantnaam",
    "SalesEmployee": "Sales",
    "DocumentOwner": "Doc. Owner",
    "RiskCategory": "Risicocategorie",
    "RiskColorType": "Risicokleur",
    "CreditLine": "Kredietlijn",
    "ProposedCreditLine": "Voorgestelde CL",
    "SuggestedAction": "Actie",
    "CreditLimitStatusText": "Status",
    "IsCreditLimitExceeded": "CL overschreden",
    "Balance": "Saldo",
    "OpenOrders": "Open Orders",
    "DownPayments": "Voorschotten",
    "OpenDeliveries": "Open Leveringen",
    "OpenInvoices": "Open Facturen",
    "CreditExposure": "Kredietblootstelling",
    "AvailableCredit": "Beschikbaar krediet",
    "CreditOverLimit": "Over kredietlimiet",
    "Risk_For_CGK": "Risico (CGK)",
    "PercentageUsedCredit": "% gebruikt krediet",
    "SafetyBufferPercent": "Buffer %",
    "AtradiusLandGroup": "Atradius groep",
    "MaxSelfAssessmentLimit": "Zelflimiet max.",
    "AtradiusCoveragePercent": "Atradius dekking %",
    "Exposure_vs_Atradius_Coverage": "Blootstelling vs Dekking",
    "U_UpdateDate": "Update datum",
    "LastInvoiceDate": "Laatste factuur",
}

# -----------------------------------------------
# Hulpfunctie om dataframe te herordenen en labels toe te passen
# -----------------------------------------------
def prepare_dataframe(df):
    """
    Zorgt dat DataFrame netjes wordt weergegeven:
    - Kolommen in vaste volgorde
    - Kolomnamen vervangen door labels
    - Nieuwe/extra velden van API blijven zichtbaar achteraan
    """
    if df.empty:
        return df

    # Volgorde toepassen
    cols = [c for c in COLUMN_ORDER if c in df.columns]
    df = df[cols + [c for c in df.columns if c not in cols]]

    # Labels toepassen
    df.rename(columns=COLUMN_LABELS, inplace=True)

    return df
