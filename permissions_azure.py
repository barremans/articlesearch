#permissions_azure.py
import msal
import requests

TENANT_ID = "526b32fa-8cb1-4d6a-9e2b-fd48e2a0e296"
CLIENT_ID = "58f55e10-e404-4307-9fa2-7b40431782fe"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["User.Read", "Group.Read.All"]

GRAPH_ME_ENDPOINT = "https://graph.microsoft.com/v1.0/me"
GRAPH_GROUPS_ENDPOINT = "https://graph.microsoft.com/v1.0/me/memberOf"

_app = None
_cached_user = None
_cached_groups = []


def _get_app():
    """Initialiseer de MSAL client (singleton)."""
    global _app
    if _app is None:
        _app = msal.PublicClientApplication(
            client_id=CLIENT_ID,
            authority=AUTHORITY
        )
    return _app


def _get_token_interactive():
    """Verkrijg een access token via silent of interactive flow."""
    app = _get_app()
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    result = app.acquire_token_interactive(scopes=SCOPES, prompt="select_account")
    if "access_token" not in result:
        raise Exception("Kon geen access token ophalen via Azure AD.")
    return result["access_token"]


def connect_to_azure_ad() -> bool:
    """
    Meld de gebruiker aan bij Azure AD en haal gebruikersinfo + groepen op.
    Wordt enkel bij app-start gebruikt.
    """
    global _cached_user, _cached_groups
    try:
        token = _get_token_interactive()
        headers = {"Authorization": f"Bearer {token}"}

        # --- Gebruikersinfo ophalen ---
        resp_user = requests.get(GRAPH_ME_ENDPOINT, headers=headers)
        if resp_user.status_code != 200:
            print(f"[AD] ❌ Kon gebruiker niet ophalen: {resp_user.status_code} {resp_user.text}")
            return False

        _cached_user = resp_user.json()
        print(f"[AD] ✅ Ingelogd als: {_cached_user.get('displayName')} ({_cached_user.get('userPrincipalName')})")

        # --- Groepen ophalen ---
        groups = []
        url = GRAPH_GROUPS_ENDPOINT
        while url:
            resp_groups = requests.get(url, headers=headers)
            if resp_groups.status_code != 200:
                print(f"[AD] ⚠️ Kon groepen niet ophalen: {resp_groups.status_code} {resp_groups.text}")
                break

            data = resp_groups.json()
            for g in data.get("value", []):
                if g.get("displayName"):
                    groups.append(g["displayName"])
            url = data.get("@odata.nextLink")

        _cached_groups = groups
        print(f"[AD] ✅ {len(groups)} groepen opgehaald.")
        for g in groups:
            print(" -", g)

        return True

    except Exception as e:
        print(f"[AD] ❌ Fout bij verbinden met Azure AD: {e}")
        return False


def list_user_groups():
    """Retourneer de opgehaalde groepnamen (cached)."""
    return _cached_groups or []


def user_in_azure_group(group_name: str) -> bool:
    """Controleer of de gebruiker lid is van de opgegeven Azure AD-groep."""
    try:
        group_name = group_name.strip().lower()
        return any((g or "").lower() == group_name for g in list_user_groups())
    except Exception as e:
        print(f"[AD] ❌ Fout bij controle groepslidmaatschap: {e}")
        return False


def print_groups():
    """Print alle groepen in de console."""
    groups = list_user_groups()
    if not groups:
        print("[AD] ⚠️ Geen groepen beschikbaar (nog niet aangemeld?).")
        return
    print("[AD] Groepen van gebruiker:")
    for g in groups:
        print(" -", g)

def get_access_token(scope="https://cgkgroupbvba.sharepoint.com/.default") -> str:
    """
    Haal een geldige access token op (silent indien mogelijk).
    Hergebruikt de huidige ingelogde Azure AD-gebruiker.
    """
    app = _get_app()
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent([scope], account=accounts[0])

    if not result or "access_token" not in result:
        result = app.acquire_token_interactive(scopes=[scope], prompt="select_account")

    return result["access_token"]
