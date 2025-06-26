import threading
from collections import defaultdict

class ProgressTracker:
    def __init__(self):
        self._progress = defaultdict(dict)
        self._lock = threading.Lock()

    def update(self, problem_key, status, detail=None):
        with self._lock:
            self._progress[problem_key]['status'] = status
            if detail is not None:
                self._progress[problem_key]['detail'] = detail

    def get(self, problem_key):
        with self._lock:
            return self._progress.get(problem_key, {})
        
    def reset(self, problem_key=None):
        with self._lock:
            if problem_key is not None:
                self._progress[problem_key] = {}
            else:
                self._progress.clear()

    def all(self):
        with self._lock:
            return dict(self._progress)
