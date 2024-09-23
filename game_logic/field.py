from game_logic.utils import load_field_data
from game_logic.evaluator import FieldEvaluation

class Field:
    def __init__(self, id, name, image, state):
        self.id = id
        self.name = name
        self.image = image
        self.state = state

    @classmethod
    def form(cls, id):
        field_data = load_field_data(id)
        return cls(
            id=field_data["id"],
            name=field_data["name"],
            image=field_data["image"],
            state=field_data["default_state"]
        )
    
    @classmethod
    def from_dict(cls, data):
        field = cls(id=data["id"],
                    name=data["name"],
                    image=data["image"],
                    state=data["state"])
        return field
    
    def to_dict(self):
        return {"id": self.id,
                "name": self.name,
                "image": self.image,
                "state": self.state}
    
    def update_state(self, state: FieldEvaluation):
        self.state = state.aftermath