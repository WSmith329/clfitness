import os

import gspread
import pandas as pd


class GoogleSheetsClient:
    def __init__(self):  # pragma: no cover
        self.client = gspread.service_account_from_dict(self._get_credentials())
        self.share_email = os.getenv('GOOGLE_SHEET_SHARE_EMAIL')

    @staticmethod
    def _get_credentials():  # pragma: no cover
        return {
            'type': os.getenv('GOOGLE_SA_TYPE'),
            'project_id': os.getenv('GOOGLE_SA_PROJECT_ID'),
            'private_key_id': os.getenv('GOOGLE_SA_PRIVATE_KEY_ID'),
            'private_key': os.getenv('GOOGLE_SA_PRIVATE_KEY').replace('\\n', '\n'),
            'client_email': os.getenv('GOOGLE_SA_CLIENT_EMAIL'),
            'client_id': os.getenv('GOOGLE_SA_CLIENT_ID'),
            'auth_uri': os.getenv('GOOGLE_SA_AUTH_URI'),
            'token_uri': os.getenv('GOOGLE_SA_TOKEN_URI'),
            'auth_provider_x509_cert_url': os.getenv('GOOGLE_SA_AUTH_PROVIDER_X509_CERT_URL'),
            'client_x509_cert_url': os.getenv('GOOGLE_SA_CLIENT_X509_CERT_URL'),
            'universe_domain': os.getenv('GOOGLE_SA_UNIVERSE_DOMAIN')
        }

    def create_spreadsheet(self, sheet_name):  # pragma: no cover
        spreadsheet = self.client.create(sheet_name)
        spreadsheet.share(self.share_email, perm_type='user', role='writer')
        return spreadsheet

    def create_sheet_from_dataframe(self, df: pd.DataFrame, sheet_name):  # pragma: no cover
        spreadsheet = self.create_spreadsheet(sheet_name)
        spreadsheet.get_worksheet(0).update([df.columns.values.tolist()] + df.values.tolist())
