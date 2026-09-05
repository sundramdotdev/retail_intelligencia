from typing import Dict, Any

class StateManager:
    def __init__(self):
        self.state: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def set(self, key: str, value: Any):
        self.state[key] = value

    def clear(self, key: str):
        if key in self.state:
            del self.state[key]

    def update_dict(self, key: str, dict_key: str, value: Any):
        if key not in self.state:
            self.state[key] = {}
        self.state[key][dict_key] = value

    def get_dict(self, key: str, dict_key: str, default: Any = None) -> Any:
        d = self.state.get(key, {})
        return d.get(dict_key, default)
    
    def remove_dict(self, key: str, dict_key: str):
        if key in self.state and dict_key in self.state[key]:
            del self.state[key][dict_key]
