from typing import Any, Type 
from collections.abc import Callable

class State:
    def repr(self) -> str:
        return type(self).__name__

'''
- required_data: []str
- required_bindings: []str
- states: []State
'''
class StateMachine:

    def __init__(self, required_data: list[str], required_bindings: list[str]):
        self.states = []
        self.active = None
        self.required_data = required_data
        self.required_bindings = required_bindings

    def add_state(self, state: Type[State]): # -> Self:

        for already_state in self.states:
            if already_state.__name__ == state.__name__:
                raise ValueError(f'State {state.__name__} already exists.')

        for required_data_name in self.required_data:
            attr = getattr(state, required_data_name, None)
            if attr == None:
                raise ValueError(f'Missing member {required_data_name} in state {state.__name__}')
            if callable(attr):
                raise ValueError(f'Method {required_data_name} should be a member instead, in state {state.__name__}')
        for required_binding_name in self.required_bindings:
            attr = getattr(state, required_binding_name, None)
            if attr == None:
                raise ValueError(f'Missing method {required_data_name} in state {state.__name__}')
            if not callable(attr):
                raise ValueError(f'Member {required_data_name} should be a method instead, in state {state.__name__}')

        self.states.append(state)
        return self

    def spin(self, default_state_name: str) -> State:
        for state in self.states:
            if state.__name__ == default_state_name:
                self.active = state()
                return self.active
        raise ValueError(f'Trying to spin non-existing state {default_state_name}')

    def call(self, method: str, *args) -> Any:
        if self.active == None:
            raise ValueError(f'Trying to call method while StateMachine is stopped')
        result = getattr(self.active, method)(*args)
        if isinstance(result, dict) and result['__NEW_STATE__']:
            newvalues = {name: getattr(self.active, name) for name in self.required_data}
            self.spin(result['__NEW_STATE__'])
            for key, value in newvalues.items():
                setattr(self.active, key, value)
            if 'RESULT' in result.keys():
                return result['RESULT']
            return None
        return result

    def stop(self):
        if self.active == None:
            raise ValueError('Trying to stop already stopped StateMachine')
        self.active = None
