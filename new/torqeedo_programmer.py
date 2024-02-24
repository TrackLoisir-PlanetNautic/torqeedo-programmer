from pydantic import BaseModel
from torqeedo_controller import TorqeedoController
from api import API
from compilation_result import CompilationResult


class TorqeedoProgrammer(BaseModel):
    api: API
    torqeedo_controllers: list[TorqeedoController] = []
    filtered_controllers: list[TorqeedoController] = []
    selected_controller: TorqeedoController = None
    selected_serial_port: str = None
    compilation_result: CompilationResult = None
