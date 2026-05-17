from rest_framework.routers import DefaultRouter

from apps.core.views import PeriodoViewSet, MateriaViewSet

router = DefaultRouter()
router.register(r"periodos", PeriodoViewSet, basename="periodos")
router.register(r"materias", MateriaViewSet, basename="materias")

urlpatterns = router.urls
