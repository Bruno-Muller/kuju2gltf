# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

import time

class StopWatch:
    def __init__(self):
        self._start = time.time()

    def get_elapsed(self) -> float:
        return time.time() - self._start
    
    def restart(self):
        self._start = time.time()