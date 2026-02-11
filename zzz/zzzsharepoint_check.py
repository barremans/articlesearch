#sharepointcheck.py
import msal
from office365.sharepoint.client_context import ClientContext

# === CONFIGUREER DIT ===
TENANT_ID = "526b32fa-8cb1-4d6a-9e2b-fd48e2a0e296"
CLIENT_ID = "58f55e10-e404-4307-9fa2-7b40431782fe"
SHAREPOINT_SITE = "https://cgkgroupbvba.sharepoint.com/sites/IT-team"
LIBRARY_PATH = "Gedeelde documenten/Applicaties/Evac_App/WeekLogs"

# === AUTHENTICATIE VIA MSAL ===
AUTHORITY_URL = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://cgkgroupbvba.sharepoint.com/.default"]

print("🌐 Start interactieve Microsoft-login...")
app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY_URL)

result = None
accounts = app.get_accounts()
if accounts:
    result = app.acquire_token_silent(SCOPES, account=accounts[0])

if not result:
    # Open een browser voor login
    result = app.acquire_token_interactive(scopes=SCOPES)

if "access_token" not in result:
    raise Exception(f"❌ Geen token ontvangen: {result.get('error_description')}")

print("✅ Token verkregen, verbinden met SharePoint...")

# === TOKEN WRAPPER FIX ===
class TokenResponse:
    def __init__(self, access_token):
        self.tokenType = "Bearer"
        self.accessToken = access_token

token = TokenResponse(result["access_token"])

# === VERBINDING MET SHAREPOINT ===
ctx = ClientContext(SHAREPOINT_SITE).with_access_token(lambda: token)
folder = ctx.web.get_folder_by_server_relative_url(LIBRARY_PATH)
files = folder.files
ctx.load(files)
ctx.execute_query()

print(f"📁 Inhoud van map '{LIBRARY_PATH}':")
for file in files:
    print(f"  - {file.properties['Name']}")

print("✅ Verbinding gelukt en bestanden opgehaald.")
