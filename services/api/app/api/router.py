from fastapi import APIRouter

from app.api.routes.addresses import router as addresses_router
from app.api.routes.admin_auth import owner as protected_admin_auth_router
from app.api.routes.admin_auth import router as admin_auth_router
from app.api.routes.admin_catalogue import router as admin_catalogue_router
from app.api.routes.admin_dashboard import router as admin_dashboard_router
from app.api.routes.admin_orders import router as admin_orders_router
from app.api.routes.catalogue import router as catalogue_router
from app.api.routes.configuration import router as configuration_router
from app.api.routes.customer_auth import router as customer_auth_router
from app.api.routes.favourites import router as favourites_router
from app.api.routes.health import router as health_router
from app.api.routes.images import router as images_router
from app.api.routes.orders import router as orders_router
from app.api.routes.whatsapp_webhooks import router as whatsapp_webhooks_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(configuration_router)
api_router.include_router(catalogue_router)
api_router.include_router(customer_auth_router)
api_router.include_router(addresses_router)
api_router.include_router(favourites_router)
api_router.include_router(orders_router)
api_router.include_router(whatsapp_webhooks_router)
api_router.include_router(admin_auth_router)
api_router.include_router(protected_admin_auth_router)
api_router.include_router(admin_dashboard_router)
api_router.include_router(admin_catalogue_router)
api_router.include_router(images_router)
api_router.include_router(admin_orders_router)
