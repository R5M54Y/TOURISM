import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsManager:
    def __init__(self):
        creds_json = os.getenv('GOOGLE_SHEETS_KEY')
        creds_dict = json.loads(creds_json)

        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        self.client = gspread.authorize(creds)

        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1y_HxN4Bbnr6I0Y1nGY6jM67QPp0au3epnn6WzGeHsX4/edit"
        self.sheet = self.client.open_by_url(spreadsheet_url).sheet1

    def add_article(self, article_data):
        """Add a new article row. Returns 1-based row id."""
        row = [
            datetime.now().isoformat(),                    # A: timestamp
            article_data['title'],                          # B: title
            article_data['content'],                        # C: content (JSON)
            article_data.get('image_url', ''),              # D: image_url
            article_data.get('keywords', ''),               # E: keywords
            'pending'                                       # F: status
        ]
        self.sheet.append_row(row)
        return len(self.sheet.get_all_values()) - 1

    def get_pending_articles(self, limit=10):
        """Return pending articles enriched with image_prompt from content JSON."""
        all_rows = self.sheet.get_all_values()
        pending = []
        for i, row in enumerate(all_rows[1:], start=2):  # skip header
            if len(row) < 6 or row[5] != 'pending':
                continue
            content_json = row[2] if len(row) > 2 else ''
            image_prompt = ''
            if content_json:
                try:
                    content_data = json.loads(content_json)
                    image_prompt = content_data.get('image_prompt', '')
                except (json.JSONDecodeError, TypeError):
                    image_prompt = ''
            pending.append({
                'row_id': i,
                'timestamp': row[0],
                'title': row[1],
                'content': content_json,
                'image_url': row[3] if len(row) > 3 else '',
                'keywords': row[4] if len(row) > 4 else '',
                'image_prompt': image_prompt,
            })
            if len(pending) >= limit:
                break
        return pending

    def set_image_url(self, row_id, image_url):
        """Write image_url (column D) for a given row."""
        row_data = self.sheet.row_values(row_id)
        while len(row_data) < 4:
            row_data.append('')
        row_data[3] = image_url
        self.sheet.update(f'D{row_id}:D{row_id}', [[image_url]])

    def update_status(self, row_id, status, platform_url=None):
        """Update status column (F) for a given row."""
        row_data = self.sheet.row_values(row_id)
        row_data[5] = status if len(row_data) > 5 else status
        if platform_url:
            if len(row_data) < 7:
                row_data.append(platform_url)
            else:
                row_data[6] = platform_url
        self.sheet.update(f'A{row_id}:G{row_id}', [row_data])
