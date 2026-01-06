import customtkinter as ctk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AppMalla(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- VENTANA ---
        self.title("capi")
        self.geometry("1300x800")
        
        # --- ESTADO ---
        self.ruta = "lena.jpg" 
        self.margen = 60
        self.N = 4
        self.sel = None
        self.drag = False
        
        # Opciones de interpolación
        self.modos_interp = {
            "Rápida (Vecino)": cv2.INTER_NEAREST,
            "Estándar (Bilineal)": cv2.INTER_LINEAR,
            "Alta (Bicúbica)": cv2.INTER_CUBIC
        }
        self.interp_actual = cv2.INTER_LINEAR

        # --- UI LAYOUT ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # PANEL IZQUIERDO
        self.panel = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.panel.grid(row=0, column=0, sticky="nswe")

        # Título
        ctk.CTkLabel(self.panel, text="MESH STUDIO PRO", font=("Arial", 22, "bold")).pack(pady=20)

        # 1. Abrir archivos
        frame_files = ctk.CTkFrame(self.panel, fg_color="transparent")
        frame_files.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(frame_files, text="Abrir Imagen...", command=self.abrir_archivo).pack(side="left", padx=5, expand=True)
        ctk.CTkButton(frame_files, text="Guardar", fg_color="#27ae60", hover_color="#2ecc71", 
                      command=self.guardar_archivo).pack(side="right", padx=5, expand=True)

        # Espacio como en css pero en python
        ctk.CTkFrame(self.panel, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=15)

        # 2. CONTROLES MALLA
        ctk.CTkLabel(self.panel, text="Densidad de Malla").pack()
        self.lbl_N = ctk.CTkLabel(self.panel, text="4x4")
        self.lbl_N.pack()
        self.slider_N = ctk.CTkSlider(self.panel, from_=2, to=10, number_of_steps=8, command=self.cambio_N)
        self.slider_N.set(4)
        self.slider_N.pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(self.panel, text="Resetear Deformación", fg_color="#c0392b", hover_color="#e74c3c", 
                      command=self.reset).pack(pady=10)

        # Espacio como en css pero en python
        ctk.CTkFrame(self.panel, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=15)

        # 3. RENDIMIENTO Y VISUAL
        ctk.CTkLabel(self.panel, text="Calidad de Render").pack()
        self.menu_calidad = ctk.CTkOptionMenu(self.panel, values=list(self.modos_interp.keys()), 
                                            command=self.cambio_calidad)
        self.menu_calidad.set("Estándar (Bilineal)")
        self.menu_calidad.pack(pady=5)

        ctk.CTkLabel(self.panel, text="Transparencia").pack(pady=(15,0))
        self.slider_alpha = ctk.CTkSlider(self.panel, from_=0, to=1, command=self.update_render)
        self.slider_alpha.set(1.0) # 1.0 = Totalmente visible
        self.slider_alpha.pack(pady=5, padx=20, fill="x")

        self.check_malla = ctk.CTkCheckBox(self.panel, text="Mostrar Malla / Puntos", command=self.update_render)
        self.check_malla.select()
        self.check_malla.pack(pady=20)

        # AREA DE TRABAJO
        self.area = ctk.CTkFrame(self)
        self.area.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        
        self.canvas = ctk.CTkCanvas(self.area, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Eventos Mouse
        self.canvas.bind("<Button-1>", self.clic)
        self.canvas.bind("<B1-Motion>", self.mover)
        self.canvas.bind("<ButtonRelease-1>", self.soltar)

        # Carga inicial (por si no existe la imagen default)
        try:
            self.cargar_img()
            self.init_malla()
            self.render()
        except:
            pass # Inicia vacío esperando que el usuario abra algo

    def abrir_archivo(self):
        filename = filedialog.askopenfilename(filetypes=[("Imagenes", "*.jpg *.png *.jpeg *.bmp")])
        if filename:
            self.ruta = filename
            self.cargar_img()
            self.init_malla()
            self.render()

    def guardar_archivo(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")])
        if save_path:
            # Renderizamos una versión limpia a full resolución o la actual
            res = self.procesar()
            # Quitamos el borde negro para guardar solo la foto
            h, w = res.shape[:2]
            m = self.margen
            crop = res[m:h-m, m:w-m]
            cv2.imwrite(save_path, crop)
            print("Guardado en:", save_path)

    def cargar_img(self):
        raw = cv2.imread(self.ruta)
        if raw is None: return

        # Redimencionamos para fluidez (max 900px ancho)
        h_raw, w_raw = raw.shape[:2]
        factor = 900 / w_raw
        h_new, w_new = int(h_raw * factor), int(w_raw * factor)
        img_re = cv2.resize(raw, (w_new, h_new))
        
        # Crear padding negro
        self.base = cv2.copyMakeBorder(img_re, self.margen, self.margen, self.margen, self.margen, 
                                      cv2.BORDER_CONSTANT, value=(0,0,0))
        self.h, self.w = self.base.shape[:2]

    def init_malla(self):
        if not hasattr(self, 'base'): return
        
        pts = []
        # Area útil
        x0, y0 = self.margen, self.margen
        wu = self.w - (2 * self.margen)
        hu = self.h - (2 * self.margen)
        dx, dy = wu / self.N, hu / self.N
        
        for i in range(self.N + 1):
            for j in range(self.N + 1):
                pts.append([int(x0 + j*dx), int(y0 + i*dy)])
        
        self.src = np.array(pts, dtype=np.float32)
        self.dst = np.array(pts, dtype=np.float32)

    def cambio_calidad(self, opcion):
        self.interp_actual = self.modos_interp[opcion]
        self.render()

    def cambio_N(self, val):
        self.N = int(val)
        self.lbl_N.configure(text=f"{self.N}x{self.N}")
        self.init_malla()
        self.render()

    def reset(self):
        self.init_malla()
        self.render()
        
    def update_render(self, val=None):
        self.render()

    def procesar(self):
        # Algoritmo de deformación
        salida = np.zeros_like(self.base) #Inicializa la imagen en negro
        
        for i in range(self.N):
            for j in range(self.N):
                k1 = i * (self.N + 1) + j
                k2, k3, k4 = k1 + 1, (i + 1) * (self.N + 1) + j, (i + 1) * (self.N + 1) + j + 1
                
                # Indices en los arrays para los vértices de la celda antes y después de la transformación
                s_blk = np.float32([self.src[k1], self.src[k2], self.src[k3], self.src[k4]])
                d_blk = np.float32([self.dst[k1], self.dst[k2], self.dst[k3], self.dst[k4]])
                
                # Calcular transformación de perspectiva a partir del cuadrado original
                M = cv2.getPerspectiveTransform(s_blk, d_blk)
                
                # Aplicar la interpolación seleccionada salu2
                warp = cv2.warpPerspective(self.base, M, (self.w, self.h), flags=self.interp_actual)
                
                # Se crea la máscara de la celda de destino
                mask = np.zeros((self.h, self.w), dtype=np.uint8)
                # Se rellena el polígono
                poly = d_blk.astype(np.int32)
                cv2.fillConvexPoly(mask, np.array([poly[0], poly[1], poly[3], poly[2]]), 255)
                
                salida = cv2.bitwise_and(salida, salida, mask=cv2.bitwise_not(mask))
                patch = cv2.bitwise_and(warp, warp, mask=mask)
                salida = cv2.add(salida, patch)
        return salida

    def render(self):
        if not hasattr(self, 'base'): return
        
        # 1. Obtener imagen deformada
        img_warp = self.procesar()
        
        # 2. Efecto Fantasma
        alpha = self.slider_alpha.get()
        if alpha < 1.0:
            # addWeighted mezcla: img1 * alpha + img2 * (1-alpha)
            combinada = cv2.addWeighted(img_warp, alpha, self.base, 1 - alpha, 0)
        else:
            combinada = img_warp

        # 3. Conversión para pantalla
        rgb = cv2.cvtColor(combinada, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        tk_img = ImageTk.PhotoImage(image=pil_img)
        
        self.canvas.delete("all")
        
        # Centrado en canvas
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        ox = (cw - self.w) // 2 if cw > 1 else 0
        oy = (ch - self.h) // 2 if ch > 1 else 0
        self.ox, self.oy = ox, oy

        self.canvas.create_image(ox, oy, image=tk_img, anchor="nw")
        
        # 4. Dibujar Malla (Solo si el checkbox está activo)
        if self.check_malla.get() == 1:
            self.dibujar_vectores(ox, oy)
            
        self.canvas.img_ref = tk_img 

    def dibujar_vectores(self, ox, oy):
        # Lineas azules
        c_lin = "#3498db"
        for i in range(self.N + 1):
            for j in range(self.N):
                p1, p2 = self.dst[i*(self.N+1)+j], self.dst[i*(self.N+1)+j+1]
                self.canvas.create_line(p1[0]+ox, p1[1]+oy, p2[0]+ox, p2[1]+oy, fill=c_lin)
        for i in range(self.N):
            for j in range(self.N + 1):
                p1, p2 = self.dst[i*(self.N+1)+j], self.dst[(i+1)*(self.N+1)+j]
                self.canvas.create_line(p1[0]+ox, p1[1]+oy, p2[0]+ox, p2[1]+oy, fill=c_lin)
        
        # Puntos
        for k, pt in enumerate(self.dst):
            x, y = pt[0]+ox, pt[1]+oy
            col = "#f1c40f" if k == self.sel else c_lin
            self.canvas.create_oval(x-5, y-5, x+5, y+5, fill=col, outline="white")

    # --- INPUT ---
    def clic(self, e):
        if self.check_malla.get() == 0: return # No mover si está oculta
        mx, my = e.x - self.ox, e.y - self.oy
        for k, pt in enumerate(self.dst):
            if np.linalg.norm(pt - [mx, my]) < 15:
                self.sel = k; self.drag = True; self.render(); break

    def mover(self, e):
        if self.drag and self.sel is not None:
            self.dst[self.sel] = [max(0, min(e.x - self.ox, self.w)), max(0, min(e.y - self.oy, self.h))]
            self.render()

    def soltar(self, e):
        self.drag = False; self.sel = None; self.render()

if __name__ == "__main__":
    app = AppMalla()
    app.mainloop()