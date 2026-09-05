import time

class Debouncer:
    def __init__(self):
        self._persistence_starts = {}
        self._last_event_times = {}

    def check_persistence(self, rule_key: str, condition_met: bool, min_persistence_seconds: float, current_time: float) -> bool:
        """
        Returns True if the condition has been met continuously for the required persistence time.
        """
        if not condition_met:
            if rule_key in self._persistence_starts:
                del self._persistence_starts[rule_key]
            return False

        if rule_key not in self._persistence_starts:
            self._persistence_starts[rule_key] = current_time
            return False

        elapsed = current_time - self._persistence_starts[rule_key]
        return elapsed >= min_persistence_seconds

    def check_cooldown(self, rule_key: str, cooldown_seconds: float, current_time: float) -> bool:
        """
        Returns True if the rule is allowed to fire (cooldown has passed).
        """
        if rule_key not in self._last_event_times:
            return True
        last_fired = self._last_event_times[rule_key]
        elapsed = current_time - last_fired
        return elapsed >= cooldown_seconds

    def register_fire(self, rule_key: str, current_time: float):
        self._last_event_times[rule_key] = current_time
        if rule_key in self._persistence_starts:
            del self._persistence_starts[rule_key]
