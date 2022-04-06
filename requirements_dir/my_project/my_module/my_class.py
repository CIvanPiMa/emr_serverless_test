print("Try to import the module `pydantic`")
import pydantic

print("Create the class `USER`")
class User(pydantic.BaseModel):
    id: str
    user: str
    num: str
    date: str
