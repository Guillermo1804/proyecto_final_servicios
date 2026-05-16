# Sistema de Gestión y Automatización de Calificaciones
### Manual de Usuario — Versión 1.0

**Autores:**
- Luis Yael Méndez Sánchez
- Gustavo Emilio Mendoza Olguín

---

## Índice

1. [Conectarse al Sistema](#1-conectarse-al-sistema)
2. [Indicaciones generales del sistema](#2-indicaciones-generales-del-sistema)
3. [Roles del sistema](#3-roles-del-sistema)
   - [3.1 Rol Administrador](#31-rol-administrador)
   - [3.2 Rol Docente](#32-rol-docente)
   - [3.3 Rol Alumno](#33-rol-alumno)

---

## Introducción

El presente manual de usuario tiene como finalidad orientar de manera clara, ordenada y comprensible el uso del **Sistema de Gestión y Automatización de Calificaciones**, una aplicación web desarrollada para apoyar la administración de procesos académicos relacionados con el registro, consulta, seguimiento y control de calificaciones en instituciones de educación superior.

Esta aplicación ha sido concebida como una herramienta de apoyo para la gestión de información académica asociada a actividades de evaluación, tales como tareas, exámenes, prácticas y proyectos, permitiendo centralizar dichos procesos dentro de un entorno digital organizado y accesible.

El sistema se estructura en distintos roles: **administrador**, **docente** y **alumno**, por lo que las funcionalidades disponibles varían conforme al perfil con el que se accede.

> El Sistema de Gestión y Automatización de Calificaciones es una obra desarrollada de manera independiente por sus autores y no constituye un producto oficial ni institucional.

---

## 1. Conectarse al Sistema

### 1.1. Utilizar la aplicación web

La pantalla de inicio de sesión (login principal) puede utilizarse en equipos móviles, tabletas y otros dispositivos de uso cotidiano por parte de estudiantes y docentes.

### 1.2. Acceso a la aplicación

En los campos de inicio de sesión se solicitará:
- **Correo electrónico institucional**
- **Contraseña** (única y confidencial)

Esta información de acceso será proporcionada cuando el usuario haya sido dado de alta en el sistema. Una vez capturados los datos correctamente, oprimir el botón **Iniciar sesión**.

### 1.3. ¿Olvidaste tu contraseña?

En caso de no recordar la contraseña, el usuario puede utilizar la opción **¿Olvidaste tu contraseña?** para iniciar el proceso de recuperación de acceso.

---

## 2. Indicaciones generales del sistema

El sistema está diseñado con una estructura común que se mantiene visible en las distintas pantallas, independientemente del usuario que haya iniciado sesión y del rol asignado.

### 2.1. Elementos comunes en cada pantalla

#### 2.1.1. Barra de navegación

En la parte superior de la pantalla se ubica la **barra de navegación**, la cual permite el acceso a los módulos principales del sistema y se mantiene visible en todo momento. Las opciones disponibles pueden variar de acuerdo con el rol del usuario autenticado.

#### 2.1.2. Información del usuario

En la esquina superior derecha se encuentra una **pestaña de perfil** que muestra:
- Nombre y apellidos
- Matrícula
- Correo electrónico
- Rol asignado
- Opción para cerrar sesión

Desde este mismo apartado, el usuario puede **cambiar su contraseña** capturando la contraseña actual, la nueva contraseña y su confirmación.

> **Nota:** Si hay inconvenientes con el reconocimiento del perfil tras cambiar la contraseña, se recomienda cerrar sesión e iniciarla nuevamente con las nuevas credenciales.

### 2.2. Pie de página

El pie de página se encuentra en la parte inferior de la aplicación y contiene información general de apoyo al usuario, así como enlaces de consulta relacionados con la operación del sistema.

---

## 3. Roles del sistema

El sistema maneja distintos roles de usuarios, cada uno con funcionalidades y permisos específicos.

---

### 3.1. Rol Administrador

El rol Administrador gestiona la configuración académica del sistema. Tiene acceso a los siguientes módulos en la barra de navegación:

| Módulo | Descripción |
|---|---|
| **ADMINISTRADOR** | Vista principal de la aplicación |
| **Periodos** | Gestión de periodos académicos |
| **Docentes** | Gestión de la información de los docentes |

#### 3.1.1. Vista principal

Al iniciar sesión, el Administrador es dirigido a la vista principal **ADMINISTRADOR**, desde la cual se visualiza la información general del periodo académico actual y la fecha/hora del sistema. Si no hay un periodo activo, aparecerá el mensaje correspondiente.

#### 3.1.2. Gestión de periodos — Crear periodo

El módulo de **Gestión de Periodos** permite registrar y administrar los periodos del sistema.

**Para crear un periodo:**

1. Seleccionar el **Nombre del periodo** en el desplegable (Primavera, Verano, Otoño). El sistema asigna automáticamente las fechas de inicio y fin.
2. **Verificar las fechas** de inicio y fin; pueden ajustarse manualmente si es necesario.
3. Seleccionar el **Plan de estudios** (actualmente solo disponible: *Profesional Semestral*).
4. Una vez completos todos los campos, oprimir el botón **Crear periodo**.

El sistema registrará el nuevo periodo y mostrará un mensaje de confirmación.

**Visualización de periodos creados:**

Los periodos se muestran como tarjetas con código de color:
- 🟢 **Verde** → Periodo activo
- 🔴 **Rojo** → Periodo desactivado

> **Consideraciones importantes:**
> - Solo debe haber **un periodo activo** a la vez.
> - El periodo activo se utiliza como referencia para todos los procesos académicos.

#### 3.1.3. Gestión de periodos — Administrar periodos existentes

Cada tarjeta de periodo ofrece las siguientes opciones:

##### 3.1.3.1. Editar

Permite ajustar la información del periodo. El sistema solicita confirmación mediante un cuadro modal y carga automáticamente los datos previamente registrados. Después de realizar los cambios, seleccionar **Actualizar periodo**.

##### 3.1.3.2. Eliminar

Permite eliminar definitivamente un periodo académico. El sistema solicita confirmación. Una vez eliminado, **no puede recuperarse**.

##### 3.1.3.3. Activar o desactivar

Controla el estado del periodo (activo/desactivado). El cambio se refleja visualmente en la tarjeta mediante el código de color.

##### 3.1.3.4. Importar materias

Función para asignar las materias correspondientes al periodo seleccionado, cargando el archivo de programación académica en **formato PDF**.

**Puntos importantes:**
- El archivo debe ser el **documento oficial** proporcionado por la instancia académica, descargado desde su página web oficial.
- El archivo debe corresponder a la programación académica **original, sin modificaciones**.
- El documento debe coincidir con el plan de estudios y la unidad académica del periodo configurado.

**Proceso de importación:**

1. Usar el botón **Elegir archivo** y seleccionar el PDF de programación académica.
2. Verificar que el nombre del archivo se muestre correctamente.
3. Presionar **Importar Materias** y confirmar en el cuadro modal.
4. El sistema mostrará una barra de progreso durante el procesamiento.
5. Al finalizar, se muestra un resumen de resultados en el apartado **Materias importadas**.

La vista cuenta con **barra de búsqueda** y **paginación** para facilitar la navegación del contenido.

#### 3.1.4. Gestión de docentes

El módulo **Docentes** permite importar, visualizar y gestionar la información de los docentes registrados. Está conformado por dos pestañas:

##### 3.1.4.1. Administrar Docentes

Muestra un listado con los siguientes campos:

| Campo | Descripción |
|---|---|
| **Docente** | Nombre completo |
| **Correo** | Correo institucional |
| **Cubículo** | Espacio asignado (o "SIN CUBÍCULO") |
| **Acciones** | Opción para restablecer contraseña |

> Si aún no se ha realizado la importación, esta sección no mostrará información.

##### 3.1.4.2. Importar docentes

Permite cargar la información de los docentes mediante un archivo PDF. El archivo se obtiene desde el directorio institucional siguiendo estos pasos:

1. Acceder al sitio web administrativo correspondiente (accesible desde el pie de página del sistema).
2. Dirigirse a la sección del **directorio institucional**.
3. Seleccionar **Personal Docente** para visualizar el listado completo.
4. Usar **Ctrl + P** (o equivalente del navegador) y seleccionar **Guardar como PDF**.
5. En las opciones avanzadas, **deshabilitar obligatoriamente**: encabezado, pie de página y gráficos de fondo.
6. Seleccionar la ubicación de descarga y guardar.

> ⚠️ Si las opciones del paso 5 no se desactivan, el archivo puede generar errores durante la importación.

##### 3.1.4.3. Proceso de importación en el sistema

1. Usar **Elegir archivo** y seleccionar el PDF de personal docente.
2. Verificar que el nombre del archivo se muestre correctamente.
3. Presionar **Importar Docentes**.
4. El sistema mostrará una barra de progreso.
5. Al finalizar, se muestra un mensaje de resultados y la información queda disponible en **Docentes importados** y en la pestaña **Administrar**.

---

### 3.2. Rol Docente

**Objetivo:** Permite al docente consultar su información, visualizar grupos y registrar asistencia.

#### 3.2.1. Inicio de sesión

Ingresar usuario y contraseña. Al acceder, se abre el **Panel Docente**.

#### 3.2.2. Módulo de dashboard de docente

**Encabezado:**
- Título: "Dashboard del Docente"
- Saludo personalizado: "Bienvenido, [Nombre Completo]"
- Email institucional y cubículo (si están registrados)
- Fecha actual (esquina superior derecha)

**Estadísticas principales** — tres tarjetas con métricas clave:

| Tarjeta | Datos | Ejemplo |
|---|---|---|
| Total Materias | Número de materias asignadas | 5 |
| Total Alumnos | Suma de alumnos en todas las materias | 126 |
| Asistencia Hoy | Porcentaje y ratio presentes/total | 78% (98/126) |

**Tabla de materias ("Mis Materias"):**

Columnas: Materia · NRC · Alumnos

Si el docente no tiene materias asignadas, se muestra el mensaje: *"Sin materias cargadas."*

#### 3.2.3. Módulo de materias

**Pestaña "Administrar"** — Vista Materias:

Búsqueda por nombre de materia o NRC. Cada tarjeta de materia muestra:
- Avatar con inicial del nombre
- Nombre de materia y Sección
- NRC y Período académico
- Estado (activo/inactivo)
- Fecha de creación

Acciones por materia:
- **Ver alumnos** — abre diálogo con la lista de inscritos (Matrícula, Nombre, Apellidos, Correo, opción de reiniciar contraseña).
- **Ponderaciones** — gestiona criterios de calificación.

**Pestaña "Importar"** — Importar Alumnos:

Flujo:
1. Seleccionar materia en el dropdown.
2. Cargar archivo Excel (`.xlsx`, `.xls`, CSV).
3. Revisar vista previa con los datos extraídos.
4. Confirmar importación.

Se puede descargar una **plantilla CSV** con encabezados: Nombre, Apellidos, Matrícula, Correo institucional.

> Si una fila no tiene matrícula, se crea el registro de alumno pero no se generan credenciales.

**Ponderaciones:**

Criterios de calificación con porcentaje (ej: Examen 50%, Tareas 30%, Asistencia 20%).

- Ver ponderaciones existentes
- Importar desde Excel (columnas: Nombre de criterio, Porcentaje)
- Editar manualmente (agregar/eliminar filas)

> ⚠️ Los porcentajes deben sumar exactamente **100%**.

#### 3.2.4. Módulo de historial

La pantalla se divide en dos áreas:

**Barra lateral (Sidebar):**
- Título: "Periodos"
- Lista de botones por periodo (activo = destacado, inactivo = atenuado)

**Área principal:**
- Encabezado: "Pase de Asistencia" / Subtítulo: "Historial de materias impartidas"
- Contador de materias
- Cada periodo agrupa las materias impartidas en ese semestre/cuatrimestre

#### 3.2.5. Módulo de pase de lista / Asistencia

**Requisitos previos:** El navegador debe tener permiso de acceso a la **cámara**.

**Selección de materia:** Obligatorio seleccionar una materia en el dropdown antes de iniciar.

**Iniciar pase de lista:**

- Botón: 🕒 **Iniciar Asistencia (10 min)** — activa la cámara e inicia sesión de 600 segundos.
- Temporizador en formato MM:SS (texto en rojo cuando quedan menos de 60 segundos).
- Indicador de modo: "Pase de Lista" o "Inactivo".

**Área de escaneo:**
- Vista en vivo de la cámara con marco de referencia para el código QR.

**Resultados de escaneo:**

| Resultado | Color | Significado |
|---|---|---|
| ✅ Asistencia registrada | Verde | Alumno marcado presente |
| ⚠️ Retardo | Naranja | Alumno llega tarde (después de 5 min) |
| ❌ Error / QR inválido | Rojo | Problema al procesar QR |
| 📷 Escaneando... | Azul | Esperando escaneo |

- Botón 🛑 **Detener Escaneo**: termina la sesión y detiene la cámara.
- Al llegar a 0:00, la sesión se cierra automáticamente.

**Clasificación de asistencia:**
- **Presente**: escaneo dentro de los primeros 5 minutos.
- **Retardo**: escaneo después de 5 minutos.

**Resumen de asistencias:**
- ✅ Presentes: total de alumnos que escanearon QR.
- 📋 Alumnos en clase: total de estudiantes inscritos.
- Botón 🗑️ **Limpiar Registros**: elimina todos los registros del día.

**Tabla de registros del día:**

| Columna | Descripción |
|---|---|
| # | Número de fila |
| Matrícula | ID único del alumno |
| Nombre | Nombre completo |
| Fecha | Fecha del registro |
| Tipo | ✅ Presente o ⚠️ Retardo |
| Hora de Registro | Hora exacta (HH:MM:SS) |

---

### 3.3. Rol Alumno

Al ingresar, el alumno accede a la pantalla principal con los siguientes elementos en la **barra de navegación**:
- Logotipo del sistema
- **Área Alumno** — pantalla principal
- **Materias** — consulta de materias inscritas
- **Pasar Lista** — módulo de asistencia
- Perfil del alumno (nombre, correo, cierre de sesión)

#### 3.3.1. Bienvenida del alumno

En la parte central superior se muestra:
- Nombre del alumno y Matrícula
- Tipo de formación y periodo académico

**Materias Actuales** (panel derecho):

| Columna | Descripción |
|---|---|
| NRC | Clave única de la materia |
| Materia | Nombre de la asignatura |
| Docente | Profesor asignado |
| Sección | Grupo correspondiente |

#### 3.3.2. Sección "Materias"

Al hacer clic en **Materias**, el alumno puede:
- Consultar el listado completo de sus materias.
- Revisar información detallada de cada asignatura.
- Consultar actividades entregadas y calificaciones.
- Dar de baja materias.

*(El contenido puede variar según la configuración del sistema.)*

#### 3.3.3. Sección "Pasar Lista"

Esta sección permite al alumno:
- Mostrar un **código QR** con su información (nombre, matrícula, fecha y hora) para ser escaneado por el profesor.
- Ver el estado de asistencia de sus clases.

> Generalmente esta sección se utiliza durante el horario de clase.
