# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

from pliskin.stopwatch import StopWatch

class Logger:
    _watch = StopWatch()
    
    @staticmethod
    def log(text: str) -> None:
        print(f"{Logger._watch.get_elapsed():3.2f} {text}")

    @staticmethod
    def warn(text: str) -> None:
        print(f"\033[33m{Logger._watch.get_elapsed():3.2f} {text}\033[0m")

    @staticmethod
    def error(text: str) -> None:
        print(f"\033[31m{Logger._watch.get_elapsed():3.2f} {text}\033[0m")