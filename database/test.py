from dataclasses import dataclass, asdict, field, Field, MISSING, is_dataclass

class ModifiedField(Field):
    def __repr__(self):
        return "ModifiedField"

def column(*, default=MISSING, default_factory=MISSING, repr=True, hash=None, init=True, compare=True, metadata=None):
    return ModifiedField(default=default, default_factory=default_factory, repr=repr, init=init, compare=compare, metadata=metadata, hash=None, kw_only=False)

@dataclass
class User:
    username: str
    password: str = "Hiii"
    id: int = field(default_factory=int)

a = User.__dict__['__dataclass_fields__']
print(a['password'])
