from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.reportes_home, name="home"),

    # ===================== SOLICITANTE (2 hojas) =====================
    path("u1-mis-reservas.xlsx", views.u1_mis_reservas_excel, name="u1_mis_reservas_excel"),
    path("u2-mis-recursos.xlsx", views.u2_mis_recursos_excel, name="u2_mis_recursos_excel"),
    path("u3-mis-espacios.xlsx", views.u3_mis_espacios_excel, name="u3_mis_espacios_excel"),

    # ===================== ADMIN PACK 8 (2 hojas) =====================
    path("r1-recursos-global.xlsx", views.r1_recursos_global_excel, name="r1_recursos_global_excel"),
    path("r2-recursos-por-area.xlsx", views.r2_recursos_por_area_excel, name="r2_recursos_por_area_excel"),
    path("r3-espacios-global.xlsx", views.r3_espacios_global_excel, name="r3_espacios_global_excel"),
    path("r4-espacios-por-area.xlsx", views.r4_espacios_por_area_excel, name="r4_espacios_por_area_excel"),
    path("r5-uso-por-area.xlsx", views.r5_uso_por_area_excel, name="r5_uso_por_area_excel"),
    path("r6-tendencia-mensual-por-area.xlsx", views.r6_tendencia_mensual_por_area_excel, name="r6_tendencia_mensual_por_area_excel"),
    path("r7-estados-por-area.xlsx", views.r7_estados_por_area_excel, name="r7_estados_por_area_excel"),
    path("r8-auditoria-detallada.xlsx", views.r8_auditoria_detallada_excel, name="r8_auditoria_detallada_excel"),
]
