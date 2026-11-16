"""Data access layer. NO streamlit here.
DemoRepository keeps data in memory. For the real system, write a class with the
same methods that reads/writes Person D's database (SQLite / CSV) and return it
from ui.common.repo().
"""
import copy
from backend.demo_data import PATIENTS, VISITS


class DemoRepository:
    def __init__(self):
        self._p = copy.deepcopy(PATIENTS)
        self._v = copy.deepcopy(VISITS)

    def patients(self):
        return self._p

    def patient(self, pid):
        return next(p for p in self._p if p["id"] == pid)

    def add_patient(self, data):
        pid = max([p["id"] for p in self._p] + [0]) + 1
        self._p.append(dict(id=pid, **data))
        self._v[pid] = []
        return pid

    def visits(self, pid):
        return self._v.setdefault(pid, [])

    def add_visit(self, pid, visit):
        self.visits(pid).append(visit)

    def total_visits(self):
        return sum(len(v) for v in self._v.values())

    def last_visit(self, pid):
        v = self.visits(pid)
        return v[-1]["date"] if v else "-"
