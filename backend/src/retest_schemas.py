from pydantic import BaseModel,ConfigDict,Field
class Input(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
class RetestInput(Input):
    request_id:str=Field(min_length=8,max_length=80)
    weight_kg:float=Field(gt=0,le=100)
    temperature:float=Field(ge=-10,le=50)
    weight_error_kg:float=Field(ge=0,le=5)
    temperature_error_c:float=Field(ge=0,le=10)
    expected_version:int=Field(ge=0)
