"""
Run this ONCE on your local Mac to generate token.json.
Then upload token.json to PythonAnywhere.

Usage:
  python generate_token.py
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive']

flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
creds = flow.run_local_server(port=0)

with open('token.json', 'w') as f:
    f.write(creds.to_json())

print("✅ token.json generated successfully. Upload it to ~/wault/token.json on PythonAnywhere.")
