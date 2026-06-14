import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsManager:
    def __init__(self):
        # Lo harus download service account key dari Google Cloud Console
        # Simpen sebagai JSON, trus copy isinya ke env variable
        creds_json = os.getenv('GOOGLE_SHEETS_KEY')
        creds_dict = json.loads(creds_json)
        
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        self.client = gspread.authorize(creds)
        
        # Open spreadsheet by name (buat dulu di Google Sheets)
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1y_HxN4Bbnr6I0Y1nGY6jM67QPp0au3epnn6WzGeHsX4/edit"
        self.sheet = self.client.open_by_url(spreadsheet_url).sheet1
    
    def add_article(self, article_data):
        """Simpan artikel ke spreadsheet"""
        row = [
            datetime.now().isoformat(),  # timestamp
            article_data['title'],        # judul
            article_data['content'],      # konten
            article_data.get('image_url', ''),  # gambar
            article_data.get('keywords', ''),   # keywords
            'pending'                     # status
        ]
        
        self.sheet.append_row(row)
        return len(self.sheet.get_all_values()) - 1  # return row number
    
    def get_pending_articles(self, limit=5):
        """Ambil artikel yang belum diposting"""
        all_rows = self.sheet.get_all_values()
        
        pending = []
        for i, row in enumerate(all_rows[1:], start=2):  # skip header
            if len(row) > 5 and row[5] == 'pending':  # status column
                pending.append({
                    'row_id': i,
                    'timestamp': row[0],
                    'title': row[1],
                    'content': row[2],
                    'image_url': row[3],
                    'keywords': row[4]
                })
                
                if len(pending) >= limit:
                    break
        
        return pending
    
    def update_status(self, row_id, status, platform_url=None):
        """Update status artikel setelah diposting"""
        # Get current row
        row_data = self.sheet.row_values(row_id)
        
        # Update status
        row_data[5] = status
        
        if platform_url:
            # Add to new column or update existing
            if len(row_data) < 7:
                row_data.append(platform_url)
            else:
                row_data[6] = platform_url
        
        # Update range
        cell_range = f'A{row_id}:G{row_id}'
        self.sheet.update(cell_range, [row_data])
