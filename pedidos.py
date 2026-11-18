"""Lógica de pedidos: catálogo, carrito y registro. No depende de Telegram, así que se prueba sin token."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Producto:
    id: str
    nombre: str
    precio: int  # COP


# Adapta este catálogo a cada negocio
NEGOCIO = "Empanadas Doña Rosa"
CATALOGO: dict[str, Producto] = {p.id: p for p in [
    Producto("emp_carne", "Empanada de carne", 3_500),
    Producto("emp_pollo", "Empanada de pollo", 3_500),
    Producto("emp_queso", "Empanada de queso", 3_000),
    Producto("gaseosa", "Gaseosa 400 ml", 3_000),
    Producto("combo", "Combo x6 + gaseosa", 22_000),
]}
DOMICILIO = 4_000
MAX_UNIDADES = 50


def pesos(valor: int) -> str:
    return "$" + f"{valor:,}".replace(",", ".")


@dataclass
class Carrito:
    items: dict[str, int] = field(default_factory=dict)

    def agregar(self, producto_id: str) -> bool:
        if producto_id not in CATALOGO or self.items.get(producto_id, 0) >= MAX_UNIDADES:
            return False
        self.items[producto_id] = self.items.get(producto_id, 0) + 1
        return True

    def quitar(self, producto_id: str) -> None:
        if self.items.get(producto_id, 0) > 1:
            self.items[producto_id] -= 1
        else:
            self.items.pop(producto_id, None)

    def vaciar(self) -> None:
        self.items.clear()

    @property
    def vacio(self) -> bool:
        return not self.items

    @property
    def subtotal(self) -> int:
        return sum(CATALOGO[i].precio * n for i, n in self.items.items())

    @property
    def total(self) -> int:
        return self.subtotal + (DOMICILIO if self.items else 0)

    def resumen(self) -> str:
        if self.vacio:
            return "Tu carrito está vacío."
        lineas = [f"• {n} x {CATALOGO[i].nombre}: {pesos(CATALOGO[i].precio * n)}" for i, n in self.items.items()]
        lineas += [f"Domicilio: {pesos(DOMICILIO)}", f"*Total: {pesos(self.total)}*"]
        return "\n".join(lineas)


@dataclass(frozen=True)
class Pedido:
    numero: int
    chat_id: int
    cliente: str
    direccion: str
    items: dict[str, int]
    total: int
    fecha: str


class RegistroPedidos:
    def __init__(self, archivo: str | Path | None = None) -> None:
        self._archivo = Path(archivo) if archivo else None
        self._lock = threading.Lock()
        self._pedidos: list[Pedido] = []
        if self._archivo and self._archivo.exists():
            self._pedidos = [Pedido(**p) for p in json.loads(self._archivo.read_text(encoding="utf-8"))]

    def crear(self, chat_id: int, cliente: str, direccion: str, carrito: Carrito, ahora: datetime | None = None) -> Pedido:
        direccion = " ".join(direccion.split())
        if carrito.vacio:
            raise ValueError("El carrito está vacío")
        if len(direccion) < 8:
            raise ValueError("La dirección es muy corta")
        with self._lock:
            pedido = Pedido(
                numero=len(self._pedidos) + 1, chat_id=chat_id, cliente=cliente, direccion=direccion[:200],
                items=dict(carrito.items), total=carrito.total, fecha=(ahora or datetime.now()).isoformat(timespec="minutes"),
            )
            self._pedidos.append(pedido)
            self._guardar()
        return pedido

    def del_dia(self, dia: str) -> list[Pedido]:
        return [p for p in self._pedidos if p.fecha.startswith(dia)]

    def _guardar(self) -> None:
        if not self._archivo:
            return
        self._archivo.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._archivo.with_suffix(".tmp")
        tmp.write_text(json.dumps([asdict(p) for p in self._pedidos], ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._archivo)


def aviso_para_dueno(p: Pedido) -> str:
    """Texto plano (sin Markdown): el nombre o la dirección del cliente pueden traer símbolos."""
    lineas = [f"🛵 Pedido #{p.numero}", f"Cliente: {p.cliente}", f"Dirección: {p.direccion}"]
    lineas += [f"• {n} x {CATALOGO[i].nombre}" for i, n in p.items.items()]
    lineas.append(f"Total: {pesos(p.total)} (incluye domicilio)")
    return "\n".join(lineas)
