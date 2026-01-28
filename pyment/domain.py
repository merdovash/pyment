import dataclasses


@dataclasses.dataclass(slots=True)
class ParamsConfig:
    param: str = ''
    type: str = ''
    default: str = ''
