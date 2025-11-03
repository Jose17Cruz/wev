import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime

class InventarioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventario de Pantallas y Accesorios - v2.0")
        self.root.geometry("1400x800")
        self.root.configure(bg="#2c2c2c")

        # Conexión a BD
        self.conn = sqlite3.connect('base_datos.db')
        self.cursor = self.conn.cursor()
        self.crear_tablas()
        

        # Variables
        self.ticket = []  # Lista de dicts: {'id': int, 'tipo': str, 'modelo': str, 'cantidad': int, 'precio': float, 'subtotal': float}
        self.ticket_devolucion = []  # Lista de dicts para devoluciones
        self.contador_ventas = 0
        self.contador_devoluciones = 0

        # Estilos
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", font=("Arial", 10, "bold"), padding=5)
        self.style.configure("TLabel", font=("Arial", 10), background="#2c2c2c", foreground="white")
        self.style.configure("TEntry", font=("Arial", 10))
        self.style.configure("TCombobox", font=("Arial", 10))
        self.style.configure("Treeview", background="#3c3c3c", foreground="white", fieldbackground="#3c3c3c")
        self.style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#555555", foreground="white")

        # Barra de menú superior
        self.menubar = tk.Menu(root)
        root.config(menu=self.menubar)
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Salir", command=self.salir)

        # Contador en la parte superior
        self.contador_label = ttk.Label(root, text=f"Ventas: {self.contador_ventas} | Devoluciones: {self.contador_devoluciones}", font=("Arial", 12, "bold"))
        self.contador_label.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.cargar_contadores()

        # Frame principal
        main_frame = tk.Frame(root, bg="#2c2c2c")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Sección Izquierda: Menú y Filtros
        self.left_frame = tk.Frame(main_frame, width=300, bg="#2c2c2c", relief="ridge", bd=2)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(self.left_frame, text="Menú de Navegación", font=("Arial", 12, "bold")).pack(pady=10)
        ttk.Button(self.left_frame, text="Registrar Productos", command=self.mostrar_registro).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_frame, text="Ver Inventario", command=self.mostrar_inventario).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_frame, text="Ventas", command=self.mostrar_ventas).pack(fill=tk.X, pady=2)
        ttk.Button(self.left_frame, text="Devoluciones", command=self.mostrar_devoluciones).pack(fill=tk.X, pady=2)

        ttk.Label(self.left_frame, text="Filtros", font=("Arial", 12, "bold")).pack(pady=10)
        ttk.Label(self.left_frame, text="Tipo:").pack(anchor="w", padx=10)
        self.tipo_filter = ttk.Combobox(self.left_frame, values=["Todos", "Pantalla", "Accesorio"], state="readonly")
        self.tipo_filter.pack(fill=tk.X, padx=10, pady=2)
        self.tipo_filter.set("Todos")
        self.tipo_filter.bind("<<ComboboxSelected>>", self.aplicar_filtros)

        ttk.Label(self.left_frame, text="Marca:").pack(anchor="w", padx=10)
        self.marca_filter = ttk.Entry(self.left_frame)
        self.marca_filter.pack(fill=tk.X, padx=10, pady=2)
        self.marca_filter.bind("<KeyRelease>", self.aplicar_filtros)

        ttk.Button(self.left_frame, text="Agregar Producto", command=self.agregar_producto).pack(fill=tk.X, pady=5)
        ttk.Button(self.left_frame, text="Actualizar Inventario", command=self.actualizar_inventario).pack(fill=tk.X, pady=5)

        # Sección Centro: Búsqueda y Lista
        self.center_frame = tk.Frame(main_frame, bg="#2c2c2c")
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(self.center_frame, text="Búsqueda y Selección", font=("Arial", 14, "bold")).pack(pady=10)

        search_frame = tk.Frame(self.center_frame, bg="#2c2c2c")
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Combobox(search_frame, state="normal")
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.buscar_productos)
        self.search_entry.bind("<<ComboboxSelected>>", self.buscar_productos)

        # Treeview para productos
        columns = ("ID", "Tipo", "Modelo", "Marca", "Cantidad", "Precio Venta", "Estado")
        self.tree = ttk.Treeview(self.center_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.mostrar_detalles)

        scrollbar = ttk.Scrollbar(self.center_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Detalles del producto seleccionado
        self.detalles_frame = tk.Frame(self.center_frame, bg="#2c2c2c")
        self.detalles_frame.pack(fill=tk.X, pady=5)
        self.detalles_label = ttk.Label(self.detalles_frame, text="Selecciona un producto para ver detalles.")
        self.detalles_label.pack()

        btn_frame = tk.Frame(self.center_frame, bg="#2c2c2c")
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Añadir a Venta", command=self.anadir_a_venta).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Marcar para Devolución", command=self.marcar_devolucion).pack(side=tk.LEFT, padx=5)

        # Sección Derecha: Ticket
        self.right_frame = tk.Frame(main_frame, width=350, bg="#2c2c2c", relief="ridge", bd=2)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(self.right_frame, text="Ticket Actual", font=("Arial", 14, "bold")).pack(pady=10)

        # Treeview para ticket
        ticket_columns = ("Modelo", "Cantidad", "Precio", "Subtotal")
        self.ticket_tree = ttk.Treeview(self.right_frame, columns=ticket_columns, show="headings", height=10)
        for col in ticket_columns:
            self.ticket_tree.heading(col, text=col)
            self.ticket_tree.column(col, width=80, anchor="center")
        self.ticket_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        self.total_label = ttk.Label(self.right_frame, text="Total: $0.00", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=5)

        btn_ticket_frame = tk.Frame(self.right_frame, bg="#2c2c2c")
        btn_ticket_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_ticket_frame, text="Cobrar", command=self.cobrar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_ticket_frame, text="Devolver", command=self.devolver).pack(side=tk.RIGHT, padx=5)

        # Cargar inventario inicial
        self.mostrar_inventario()

    def crear_tablas(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                modelo TEXT NOT NULL,
                marca TEXT NOT NULL,
                descripcion TEXT,
                cantidad INTEGER NOT NULL,
                precio_compra REAL NOT NULL,
                precio_venta REAL NOT NULL,
                fecha_ingreso TEXT NOT NULL,
                ubicacion TEXT,
                estado TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                productos TEXT,
                total REAL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS devoluciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                productos TEXT,
                total REAL
            )
        ''')
        self.conn.commit()

    def cargar_contadores(self):
        self.cursor.execute("SELECT COUNT(*) FROM ventas")
        self.contador_ventas = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM devoluciones")
        self.contador_devoluciones = self.cursor.fetchone()[0]
        self.actualizar_contador()

    def actualizar_contador(self):
        self.contador_label.config(text=f"Ventas: {self.contador_ventas} | Devoluciones: {self.contador_devoluciones}")

    def mostrar_registro(self):
        # Cambiar a vista de registro (simplemente mostrar el formulario en centro o algo, pero por simplicidad, usar el izquierdo)
        pass  # Ya está en el izquierdo

    def mostrar_inventario(self):
        self.buscar_productos()

    def mostrar_ventas(self):
        # Mostrar historial de ventas
        win = tk.Toplevel(self.root)
        win.title("Historial de Ventas")
        win.geometry("600x400")
        tree = ttk.Treeview(win, columns=("ID", "Fecha", "Productos", "Total"), show="headings")
        tree.pack(fill=tk.BOTH, expand=True)
        self.cursor.execute("SELECT * FROM ventas")
        for row in self.cursor.fetchall():
            tree.insert("", tk.END, values=row)

    def mostrar_devoluciones(self):
        # Mostrar historial de devoluciones
        win = tk.Toplevel(self.root)
        win.title("Historial de Devoluciones")
        win.geometry("600x400")
        tree = ttk.Treeview(win, columns=("ID", "Fecha", "Productos", "Total"), show="headings")
        tree.pack(fill=tk.BOTH, expand=True)
        self.cursor.execute("SELECT * FROM devoluciones")
        for row in self.cursor.fetchall():
            tree.insert("", tk.END, values=row)

    def aplicar_filtros(self, event=None):
        tipo = self.tipo_filter.get()
        marca = self.marca_filter.get().strip()
        query = "SELECT id, tipo, modelo, marca, cantidad, precio_venta, estado FROM productos WHERE 1=1"
        params = []
        if tipo != "Todos":
            query += " AND tipo = ?"
            params.append(tipo)
        if marca:
            query += " AND LOWER(marca) LIKE ?"
            params.append(f"%{marca.lower()}%")
        self.cursor.execute(query, params)
        self.actualizar_tree(self.cursor.fetchall())

    def buscar_productos(self, event=None):
        search = self.search_entry.get().strip().lower()
        if search:
            self.cursor.execute('''
                SELECT id, tipo, modelo, marca, cantidad, precio_venta, estado FROM productos
                WHERE LOWER(modelo) LIKE ? OR LOWER(marca) LIKE ? OR LOWER(tipo) LIKE ?
            ''', (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            self.cursor.execute("SELECT id, tipo, modelo, marca, cantidad, precio_venta, estado FROM productos")
        self.actualizar_tree(self.cursor.fetchall())

    def actualizar_tree(self, rows):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def mostrar_detalles(self, event=None):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            prod_id = item['values'][0]
            self.cursor.execute("SELECT * FROM productos WHERE id = ?", (prod_id,))
            prod = self.cursor.fetchone()
            if prod:
                detalles = f"ID: {prod[0]}\nTipo: {prod[1]}\nModelo: {prod[2]}\nMarca: {prod[3]}\nDescripción: {prod[4]}\nCantidad: {prod[5]}\nPrecio Compra: ${prod[6]}\nPrecio Venta: ${prod[7]}\nFecha: {prod[8]}\nUbicación: {prod[9]}\nEstado: {prod[10]}"
                self.detalles_label.config(text=detalles)

    def anadir_a_venta(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona un producto.")
            return
        item = self.tree.item(selected[0])
        prod_id, tipo, modelo, marca, cantidad, precio, estado = item['values']
        if cantidad <= 0:
            messagebox.showerror("Error", "Producto sin stock.")
            return
        qty = simpledialog.askinteger("Cantidad", f"Cantidad para {modelo}:", minvalue=1, maxvalue=cantidad)
        if qty:
            precio = float(precio)
            subtotal = qty * precio
            self.ticket.append({'id': prod_id, 'tipo': tipo, 'modelo': modelo, 'cantidad': qty, 'precio': precio, 'subtotal': subtotal})
            self.actualizar_ticket()

    def marcar_devolucion(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona un producto.")
            return
        item = self.tree.item(selected[0])
        prod_id, tipo, modelo, marca, cantidad, precio, estado = item['values']
        qty = simpledialog.askinteger("Cantidad", f"Cantidad para devolver {modelo}:", minvalue=1)
        if qty:
            precio = float(precio)
            subtotal = qty * precio
            self.ticket_devolucion.append({'id': prod_id, 'tipo': tipo, 'modelo': modelo, 'cantidad': qty, 'precio': precio, 'subtotal': subtotal})
            self.actualizar_ticket_devolucion()

    def actualizar_ticket(self):
        for row in self.ticket_tree.get_children():
            self.ticket_tree.delete(row)
        total = 0.0
        for item in self.ticket:
            self.ticket_tree.insert("", tk.END, values=(item['modelo'], item['cantidad'], f"${float(item['precio']):.2f}", f"${float(item['subtotal']):.2f}"))
            total += item['subtotal']
        self.total_label.config(text=f"Total: ${total:.2f}")

    def actualizar_ticket_devolucion(self):
        for row in self.ticket_tree.get_children():
            self.ticket_tree.delete(row)
        total = 0.0
        for item in self.ticket_devolucion:
            self.ticket_tree.insert("", tk.END, values=(item['modelo'], item['cantidad'], f"${float(item['precio']):.2f}", f"${float(item['subtotal']):.2f}"))
            total += item['subtotal']
        self.total_label.config(text=f"Total Devolución: ${total:.2f}")

    def cobrar(self):
        if not self.ticket:
            messagebox.showwarning("Advertencia", "Ticket vacío.")
            return
        productos_str = "; ".join([f"{item['modelo']} x{item['cantidad']}" for item in self.ticket])
        total = sum(item['subtotal'] for item in self.ticket)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cursor.execute("INSERT INTO ventas (fecha, productos, total) VALUES (?, ?, ?)", (fecha, productos_str, total))
        for item in self.ticket:
            self.cursor.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id = ?", (item['cantidad'], item['id']))
        self.conn.commit()
        self.ticket = []
        self.actualizar_ticket()
        self.contador_ventas += 1
        self.actualizar_contador()
        self.mostrar_inventario()
        messagebox.showinfo("Éxito", "Venta cobrada.")

    def devolver(self):
        if not self.ticket_devolucion:
            messagebox.showwarning("Advertencia", "Ticket de devolución vacío.")
            return
        productos_str = "; ".join([f"{item['modelo']} x{item['cantidad']}" for item in self.ticket_devolucion])
        total = sum(item['subtotal'] for item in self.ticket_devolucion)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cursor.execute("INSERT INTO devoluciones (fecha, productos, total) VALUES (?, ?, ?)", (fecha, productos_str, total))
        for item in self.ticket_devolucion:
            self.cursor.execute("UPDATE productos SET cantidad = cantidad + ? WHERE id = ?", (item['cantidad'], item['id']))
        self.conn.commit()
        self.ticket_devolucion = []
        self.actualizar_ticket_devolucion()
        self.contador_devoluciones += 1
        self.actualizar_contador()
        self.mostrar_inventario()
        messagebox.showinfo("Éxito", "Devolución procesada.")

    def agregar_producto(self):
        # Abrir ventana de registro
        add_win = tk.Toplevel(self.root)
        add_win.title("Agregar Producto")
        add_win.geometry("500x500")

        fields = ["Tipo", "Modelo", "Marca", "Descripción", "Cantidad", "Precio Compra", "Precio Venta", "Ubicación", "Estado"]
        entries = {}
        for field in fields:
            ttk.Label(add_win, text=f"{field}:").pack(pady=2)
            if field == "Tipo":
                combo = ttk.Combobox(add_win, values=["Pantalla", "Accesorio"], state="readonly")
                combo.pack(fill=tk.X, padx=10)
                entries[field] = combo
            elif field == "Estado":
                combo = ttk.Combobox(add_win, values=["Nuevo", "Usado", "Dañado"], state="readonly")
                combo.pack(fill=tk.X, padx=10)
                entries[field] = combo
            else:
                entry = ttk.Entry(add_win)
                entry.pack(fill=tk.X, padx=10)
                entries[field] = entry

        def save():
            try:
                tipo = entries["Tipo"].get()
                modelo = entries["Modelo"].get().strip()
                marca = entries["Marca"].get().strip()
                desc = entries["Descripción"].get().strip()
                qty = int(entries["Cantidad"].get())
                pc = float(entries["Precio Compra"].get())
                pv = float(entries["Precio Venta"].get())
                ubi = entries["Ubicación"].get().strip()
                est = entries["Estado"].get()
                fecha = datetime.now().strftime("%d/%m/%Y")
                self.cursor.execute('''
                    INSERT INTO productos (tipo, modelo, marca, descripcion, cantidad, precio_compra, precio_venta, fecha_ingreso, ubicacion, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (tipo, modelo, marca, desc, qty, pc, pv, fecha, ubi, est))
                self.conn.commit()
                messagebox.showinfo("Éxito", "Producto agregado.")
                add_win.destroy()
                self.mostrar_inventario()
            except ValueError:
                messagebox.showerror("Error", "Datos inválidos.")

        ttk.Button(add_win, text="Guardar", command=save).pack(pady=10)

    def salir(self):
        self.conn.close()
        self.root.quit()

    def actualizar_inventario(self):
        self.mostrar_inventario()


if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioApp(root)
    root.mainloop()
