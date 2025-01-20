from django.conf import settings
from datetime import datetime

class CachedData:
    def __init__(self):
        self.collection = settings.MONGO_DB['cached_data']

    def cache_data(self, symbol, timeframe, start_date, end_date, data):
        self.collection.update_one(
            {
                'symbol': symbol,
                'timeframe': timeframe,
                'start_date': start_date,
                'end_date': end_date,
            },
            {
                '$set': {
                    'data': data,
                    'timestamp': datetime.utcnow()
                }
            },
            upsert=True
        )

    def get_cached_data(self, symbol, timeframe, start_date, end_date):
        return self.collection.find_one({
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date,
            'end_date': end_date,
        })