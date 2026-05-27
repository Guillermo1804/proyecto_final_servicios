# Plan de Acción: Modernización Visual e Interactiva del Frontend (AGM BUAP)

Este plan de acción detalla los pasos para refactorizar la arquitectura de estilos del frontend de la aplicación Angular (`sistema_AGM`) del proyecto, migrando el esquema a variables de CSS dinámicas, implementando animaciones fluidas y elevando la estética visual en general para alinearse con un estándar premium.

---

## User Review Required

> [!IMPORTANT]
> **Paleta por Defecto:** Se implementará la paleta **Neo-BUAP** (azul marino institucional refinado con detalles en dorado y azul eléctrico interactivo) por defecto.
> **Enfoque SCSS:** Para garantizar un alto rendimiento y evitar añadir peso innecesario al bundle de Angular, las transiciones se manejarán de manera nativa utilizando animaciones y transiciones de CSS aplicadas por hardware (`opacity` y `transform`).
> **Despliegue Responsivo en Escritorio:** Modificaremos el diseño del contenedor global para admitir un sidebar (barra lateral) flotante limpio en desktop (min-width: 1024px) y ocultar el bottom-nav, mejorando la usabilidad.

---

## Open Questions

> [!NOTE]
> * **¿Prefieres que dejemos preparado el soporte para cambiar entre temas (Neo-BUAP y Cyber-FCC) en el futuro?** Esto se puede lograr de forma sencilla estructurando las variables de CSS en clases temáticas (ej: `.theme-neo-buap` y `.theme-cyber-fcc`).
> * **¿Hay alguna tipografía específica de la BUAP que debamos cargar desde Google Fonts?** Por defecto utilizaremos **Outfit** o **Inter** para títulos y **Roboto** para el cuerpo de texto, mejorando significativamente la apariencia actual.

---

## Proposed Changes

Trabajaremos este plan una fase a la vez. Al cerrar cada fase mostraré el avance obtenido, dejaré el siguiente tramo preparado y pediré permiso antes de continuar.

### Estado de avance

- Fase 1: Cimentación del sistema de diseño - completada
- Fase 2: Pantalla de acceso - completada
- Fase 3: Layouts de navegación - completada
- Fase 4: Dashboards y reportes - completada

Se separa la implementación en 4 fases ordenadas lógicamente para mitigar riesgos de regresión visual y asegurar una transición fluida.

---

### Fase 1: Cimentación del Sistema de Diseño (Design Tokens)

Implementaremos las variables CSS globales y las clases de utilidad para animaciones, layouts premium (Glassmorphic) y tipografía en el archivo principal de estilos.

**Criterio de cierre:** tokens globales disponibles, tipografía base unificada y utilidades visuales reutilizables para el resto de pantallas.

#### [MODIFY] [styles.scss](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/styles.scss)
* Carga de fuentes premium en el encabezado (ej. `@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Roboto:wght@300;400;500;700&display=swap')`).
* Declaración del bloque `:root` con las variables de la paleta **Neo-BUAP**.
* Clases utilitarias globales de animación (`.animate-fade-in-up`, `.stagger-*`).
* Definición de tarjetas comunes de cristal (`.card-glass`), botones premium (`.btn-premium`) y efectos de carga (`.shimmer-placeholder`).

---

### Fase 2: Pantalla de Acceso (Login Screen)

Refactorizaremos la pantalla de inicio de sesión para aplicar el diseño premium, dándole una apariencia limpia y atractiva a dos columnas.

#### [MODIFY] [login-screen.html](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/login-screen/login-screen.html)
* Ajustar clases para emplear los nuevos wrappers de entrada e iconos pulidos.
* Incorporar clases de animación staggered en las etiquetas de los formularios y botones.

#### [MODIFY] [login-screen.scss](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/login-screen/login-screen.scss)
* Reemplazar valores estáticos por variables CSS (`var(--bg-page)`, `var(--primary-deep)`, etc.).
* Aplicar el gradiente mesh en el panel de marca de la BUAP (`brand-panel`).
* Implementar foco dinámico con efecto *glow* en `.input-wrapper` e interacciones del botón de envío.

---

### Fase 3: Layouts de Navegación (Topbar & Navbars)

Estandarizaremos las barras de navegación de los 3 roles para hacerlas totalmente responsivas y ocultar adecuadamente el bottom navbar en desktop, sustituyéndolo por un layout limpio.

#### [MODIFY] [topbar-admin.html](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/partials/topbar-admin/topbar-admin.html) / [.scss](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/partials/topbar-admin/topbar-admin.scss)
* Modernizar el botón de salida e incluir bordes con gradientes sutiles.

#### [MODIFY] [bottom-navbar-admin.scss](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/partials/bottom-navbar-admin/bottom-navbar-admin.scss)
* Agregar comportamiento de ocultamiento en desktop (`@media (min-width: 1024px) { display: none; }`).
* Aplicar transiciones y efecto *active* de burbuja deslizante en los botones de navegación inferior.

---

### Fase 4: Modernización de Dashboards y Reportes

Actualizaremos los tableros del Administrador, Docente y Alumno usando las nuevas tarjetas de vidrio, listas animadas y paletas unificadas.

#### [MODIFY] [dashboard-screen.scss (Admin)](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/admin-screen/dashboard-screen.scss) / [.html](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/admin-screen/dashboard-screen.html)
* Convertir las tarjetas estadísticas a `.card-glass`.
* Añadir animaciones staggered a la tabla de actividades recientes.

#### [MODIFY] [dashboard-screen.scss (Docente)](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/docente-screen/dashboard-screen/dashboard-screen.scss) / [.html](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/docente-screen/dashboard-screen/dashboard-screen.html)
* Ajustar tarjetas de clases con bordes de color dinámicos.
* Pulir las alertas de pendientes académicos con íconos iluminados.

#### [MODIFY] [dashboard-screen.scss (Alumno)](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/alumno-screen/dashboard-screen/dashboard-screen.scss) / [.html](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/alumno-screen/dashboard-screen/dashboard-screen.html)
* Aplicar el gradiente mesh en la tarjeta principal (Hero).
* Modernizar el círculo de promedio general con micro-interacción flotante.

#### [MODIFY] [notas-screen.scss](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/alumno-screen/notas-screen/notas-screen.scss) / [.html](file:///c:/Users/Guizmarcito/Documents/GitHub/proyecto_final_servicios/frontend/sistema_AGM/src/app/screens/alumno-screen/notas-screen/notas-screen.html)
* Añadir animación al despliegue del desglose de parciales (acordeón).
* Estilizar el indicador de promedio parcial con un bar-loader fluido de carga progresiva.

---

## Verification Plan

### Manual Verification
1. **Validación de Login:** Entrar a la página principal y verificar la animación de carga, transiciones de inputs en focus y el botón de enviar.
2. **Prueba de Responsividad (Mobile vs Desktop):** Abrir las herramientas de desarrollo del navegador y alternar entre vistas móviles (iPhone/Pixel) y desktop. Confirmar que en móviles se use el bottom-bar y en desktop este se oculte.
3. **Validación de Transiciones en Dashboards:** Navegar a las secciones de Admin, Alumno y Docente y comprobar el efecto de entrada *fade-in-up* de las tarjetas y el comportamiento *hover* de las mismas.
4. **Verificación de Compilación:** Ejecutar `npm run build` o `ng build` para asegurar que el preprocesador de Sass compile sin errores todas las variables personalizadas importadas.
