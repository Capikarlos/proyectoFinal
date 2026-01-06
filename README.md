# Procesamiento de Imágenes
> Una herramienta profesional de ingeniería para la deformación de imágenes basada en mallas, implementada con algoritmos de transformación de perspectiva por tramos.

---

## Demo
![Interfaz de Usuario](https://miro.medium.com/v2/resize:fit:706/format:webp/1*sGVq7w-n59F3PkGlVykm_Q.png)
![](https://miro.medium.com/v2/resize:fit:1368/format:webp/1*GXlZbgJG0GMiUT2JwVJjUw.png)

*Interfaz gráfica moderna con modo oscuro, malla interactiva y controles en tiempo real.*

---

## Descripción

**Mesh Warp** es una aplicación de escritorio desarrollada en Python que permite la manipulación geométrica de imágenes mediante una malla de control interactiva. A diferencia de las transformaciones afines globales, este software utiliza **interpolación local** dividiendo la imagen en cuadrantes, permitiendo deformaciones no lineales complejas (efecto "líquido" o de tejido).

### Características Principales

* **Malla Interactiva:** Arrastra y suelta vértices con el mouse para deformar la imagen en tiempo real.
* **Densidad Ajustable:** Modifica la resolución de la malla (de 2x2 a 10x10) dinámicamente mediante sliders.
* **Motor de Renderizado Híbrido:**
    * *Modo Rápido:* Vecino más cercano (Nearest Neighbor).
    * *Modo Estándar:* Bilineal (Suavizado).
    * *Modo Alta:* Bicúbica (Máxima calidad para exportación).
* **Modo Fantasma (Ghosting):** Control de opacidad para comparar la deformación contra la imagen original (ground truth).
* **I/O Completo:** Carga imágenes de cualquier formato y exporta el resultado limpio (sin guías).
* **UI Moderna:** Interfaz basada en `CustomTkinter` con tema oscuro y panel de control lateral.


## Controles

| Tecla / Acción | Función |
| :--- | :--- |
| **Click Izquierdo** | Seleccionar y arrastrar vértice |
| **Slider "Malla"** | Cambiar número de celdas (**N × N**) |
| **Slider "Fantasma"** | Ajustar transparencia (Alpha Blending) |
| **Botón Reset** | Restaurar la imagen a su estado original |
| **Botón Guardar** | Exportar imagen (elimina automáticamente las guías) |

---

## Teoría y Algoritmos

Este software no utiliza una deformación global simple. Implementa una estrategia de **"Piecewise Perspective Warping"** (Deformación de Perspectiva por Tramos):

1.  **Discretización:** La imagen se divide en $N \times N$ celdas rectangulares.
2.  **Mapeo:** Cada celda se trata como un polígono independiente. Se calcula una **Matriz de Homografía (**N × N**)** única para cada celda basada en el desplazamiento de sus 4 vértices.
3.  **Enmascarado:** Se generan máscaras convexas para recortar y ensamblar las celdas deformadas en una sola imagen final sin "costuras" visibles.

---

## Autores y Créditos

Este proyecto fue desarrollado por estudiantes de **Ingeniería en Inteligencia Artificial**:

* **Arturo Salazar Soto**
* **Alejandro Esponda Meza**
* **Dante Molina López**
* **Carlos Antonio López**

---

## Licencia

Este proyecto está bajo la licencia de la UPIIT

---
*Hecho con lagrimas de los alumnos saludos profe.*
