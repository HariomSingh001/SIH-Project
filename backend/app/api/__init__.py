from .centres import router as centres_router
from .attendance import router as attendance_router
from .inventory import router as inventory_router
from .telemetry import router as telemetry_router
from .discrepancy import router as discrepancy_router
from .dashboard import router as dashboard_router
from .pipeline import router as pipeline_router
from .edge import router as edge_router

__all__ = [
    "centres_router",
    "attendance_router",
    "inventory_router",
    "telemetry_router",
    "discrepancy_router",
    "dashboard_router",
    "pipeline_router",
    "edge_router",
]
