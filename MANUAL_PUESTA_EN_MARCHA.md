# 🚀 Manual de Puesta en Marcha Rápida
## Actualizador Automático de Programas (03-IA) — Windows

Este manual te explica de forma rápida, sencilla y directa cómo iniciar y utilizar la aplicación para mantener siempre al día todos los programas instalados en tu equipo.

---

## 📌 1. ¿Cómo Iniciar la Aplicación?

Tienes tres formas cómodas de abrir la aplicación:

### ⭐ Opción A: Desde el Acceso Directo del Escritorio (La más rápida)
1. Ve a tu **Escritorio** de Windows.
2. Haz doble clic sobre el icono **`Actualizador de Programas`**.
3. La aplicación se abrirá directamente en su propia ventana de escritorio (sin consolas negras molestas).

### Opción B: Inicio Silencioso desde la Carpeta
1. Abre la carpeta del proyecto:
   `c:\Users\josed\Desktop\9-P-SEP.26\03-IA-ACTUALIZADOR-PROGRAMAS-WINDOWS`
2. Haz doble clic sobre el archivo **`iniciar-silencioso.vbs`**.

### Opción C: Inicio con Consola de Registro
Si en algún momento quieres ver la consola tradicional de fondo mientras pruebas la aplicación:
1. Haz doble clic sobre **`iniciar.bat`**.

---

## 🖥️ 2. Guía Paso a Paso de Uso

Al abrir la aplicación, verás el panel de control con fondo oscuro y efecto cristal:

### Paso 1: Comprobar el Escaneo Automático
- La aplicación realiza un **escaneo automático inicial** nada más abrirse.
- En la tarjeta **ACTUALIZACIONES DISPONIBLES** verás el número de programas que tienen una versión más reciente lista para instalar (por ejemplo, 58 programas).
- En **PROGRAMAS DETECTADOS** verás el total de programas instalados en tu sistema (ej. 447 programas).

### Paso 2: Elige cómo quieres actualizar

#### ⚡ Modo 1 Clic (Recomendado): "Actualizar Todo"
1. Pulsa el botón morado **`⚡ Actualizar Todo`** en la esquina superior derecha.
2. Confirma en el mensaje que aparecerá en pantalla.
3. La aplicación pasará automáticamente a la pestaña **`Terminal en Vivo`** y empezará a descargar e instalar en segundo plano y de manera silenciosa las nuevas versiones de todos los programas.

#### 🎯 Modo Selectivo: "Actualizar Seleccionados"
1. En la pestaña **`Actualizaciones Pendientes`**, desmarca o marca las casillas de los programas que desees actualizar.
2. Puedes usar el buscador superior para encontrar rápidamente cualquier programa por su nombre o ID.
3. Haz clic en **`Actualizar Seleccionados (X)`** para actualizar únicamente los elegidos.

#### 🔹 Actualización de un Programa Individual
- Al final de la fila de cada programa tienes un botón individual **`Actualizar`**. Al pulsarlo, sólo se procesará ese software específico.

### Paso 3: Seguimiento en Tiempo Real
- Haz clic en la pestaña **`Terminal en Vivo`** para ver en pantalla las descargas, porcentajes de progreso y mensajes de confirmación de cada instalador.

---

## 💡 3. Preguntas Frecuentes y Consejos

### ¿Qué ocurre si un programa pide permisos de Administrador?
- Algunos programas de nivel del sistema (drivers, Visual Studio, etc.) pueden mostrar una ventana emergente de Windows (UAC) solicitando "¿Deseas permitir que esta aplicación haga cambios en el dispositivo?". Simplemente pulsa **Sí** para que continúe la instalación.

### ¿Se puede volver a escanear en cualquier momento?
- Sí. Solo tienes que hacer clic en el botón **`🔄 Escanear Ahora`** y el sistema volverá a consultar los repositorios oficiales de Microsoft para comprobar si hay nuevas versiones.

### ¿Cómo restauro el acceso directo del escritorio si se borra?
- Dentro de la carpeta del proyecto, haz clic derecho sobre **`Crear-Acceso-Directo.ps1`** y selecciona **Ejecutar con PowerShell**.

---

## 🌐 4. Repositorio y Control de Versiones en GitHub

El proyecto está sincronizado con tu repositorio público en GitHub:
- **URL del Repositorio:** [https://github.com/josedpdiaz/03-ia-actualizador-programas-windows](https://github.com/josedpdiaz/03-ia-actualizador-programas-windows)
- **Para subir futuras mejoras:**
  ```powershell
  git add .
  git commit -m "Descripción de la mejora"
  git push origin main
  ```
