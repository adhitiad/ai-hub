import datetime
import json
import os

SNAPSHOT_FILE = "signal_snapshot.json"


class InternalSignalBus:
    _instance = None
    _storage = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InternalSignalBus, cls).__new__(cls)
            cls._instance.load_snapshot()
        return cls._instance

    def update_signal(self, symbol, data):
        self._storage[symbol] = {
            "data": data,
            "updated_at": str(datetime.datetime.now()),
        }

    def get_signal(self, symbol):
        record = self._storage.get(symbol)
        return record["data"] if record else None

    def get_all_signals(self):
        return {k: v["data"] for k, v in self._storage.items()}

    def save_snapshot(self):
        try:
            with open(SNAPSHOT_FILE, "w") as f:
                json.dump(self._storage, f)
        except:
            pass

    def load_snapshot(self):
        if os.path.exists(SNAPSHOT_FILE):
            try:
                with open(SNAPSHOT_FILE, "r") as f:
                    self._storage = json.load(f)
            except:
                pass

    def get_active_threads_count(self):
        return len(self._storage)


signal_bus = InternalSignalBus()
