import pytest
from app.intelligence.state import StateManager
from app.intelligence.debouncer import Debouncer

def test_state_manager():
    sm = StateManager()
    sm.set("test_key", "value")
    assert sm.get("test_key") == "value"
    sm.clear("test_key")
    assert sm.get("test_key") is None
    
    sm.update_dict("dict_key", "inner", 42)
    assert sm.get_dict("dict_key", "inner") == 42
    sm.remove_dict("dict_key", "inner")
    assert sm.get_dict("dict_key", "inner") is None

def test_debouncer_persistence():
    db = Debouncer()
    rule_key = "rule1"
    
    # Not met initially
    assert not db.check_persistence(rule_key, False, 5.0, 10.0)
    
    # Met at T=10, but not enough time
    assert not db.check_persistence(rule_key, True, 5.0, 10.0)
    
    # Met at T=12, still not enough (needs 5)
    assert not db.check_persistence(rule_key, True, 5.0, 12.0)
    
    # Met at T=15, now enough
    assert db.check_persistence(rule_key, True, 5.0, 15.0)
    
    # Breaks condition
    assert not db.check_persistence(rule_key, False, 5.0, 16.0)
    
    # Starts over at 17
    assert not db.check_persistence(rule_key, True, 5.0, 17.0)

def test_debouncer_cooldown():
    db = Debouncer()
    rule_key = "rule1"
    
    assert db.check_cooldown(rule_key, 60.0, 10.0)
    
    db.register_fire(rule_key, 10.0)
    
    # Too soon
    assert not db.check_cooldown(rule_key, 60.0, 20.0)
    
    # Passed cooldown
    assert db.check_cooldown(rule_key, 60.0, 71.0)
