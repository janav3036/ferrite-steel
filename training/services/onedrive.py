import os 
import requests
import msal

def _get_access_token():
    authority = f"https://login.microsoftonline.com/{os.environ['MS_TENANT_ID']}"
    app = msal.ConfidentialClientApplication(
        os.environ['MS_CLIENT_ID'],
        authority=authority,
        client_credential=os.environ['MS_CLIENT_SECRET'],
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"OneDrive auth failed: {result.get('error_description')}")
    return result["access_token"]

def upload_file(file_bytes, filename):
    user_email = os.environ['ONEDRIVE_USER_EMAIL']
    folder = os.environ.get('ONEDRIVE_FOLDER', 'FeriteSteelDocs')
    token = _get_access_token()
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{folder}/{filename}:/content"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
    }
    response = requests.put(url, headers=headers, data=file_bytes)
    response.raise_for_status()
    return response.json().get("webUrl", "")