from dataclasses import dataclass

@dataclass
class TypesafeDataclass:
    """
    Data class, that enforces typesafe assignments (TODO nested data structures)
    """
    def __init__(self):
        self._type_dict: dict = self._create_type_dict()

    def _create_type_dict(self) -> dict:
        type_dict = {}
        for key in dir(self):
            type_dict[key] = type(getattr(self, key))
        return type_dict

    def __set_change_type__(self, key: str, value):
        """
        set existing value and overrides type
        """
        self._type_dict[key] = type(value)
        self.__dict__[key] = value

    def __setattr__(self, key, value):
        """
        typesafe attribute setter
        """
        try:
            if key == "_type_dict":
                self.__dict__[key] = value
            else:
                attr = self.__getattribute__(key)
                # Allow only same type except setting to None
                if self._type_dict[key] is not type(value) and not(type(value) == type(None)):
                    raise TypeError(f"{value} for attribute {key} is not of type {type(attr)}")
                else:
                    self.__dict__[key] = value
        except AttributeError:
            self._type_dict[key] = type(value)
            self.__dict__[key] = value


if __name__ == "__main__":
    ar = TypesafeDataclass()
    ar.__set_change_type__('db_name', 1)

