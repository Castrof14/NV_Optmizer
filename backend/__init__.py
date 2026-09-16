"""
NV Optimizer 2.0 - Backend
Camada de backend responsável pela execução real das operações no Windows.
"""

from .api import BackendAPI
from .backend_core import (
    isAdmin, require_admin, OperationResult,
    ProgressEmitter, SecurityValidator
)

__all__ = [
    'BackendAPI',
    'isAdmin',
    'require_admin',
    'OperationResult',
    'ProgressEmitter',
    'SecurityValidator',
]
