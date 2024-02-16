from pydantic import BaseModel
from typing import Optional
from torqeedo_controller import TorqeedoController
from api import API
from compilation_result import CompilationResult


class TorqeedoProgrammer(BaseModel):
    api: API
    torqeedo_controllers: list[TorqeedoController] = []
    selected_controller: TorqeedoController = None
    compilation_result: CompilationResult = None
