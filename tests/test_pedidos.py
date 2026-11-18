import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pedidos import DOMICILIO, Carrito, RegistroPedidos, aviso_para_dueno, pesos  # noqa: E402


def test_carrito_suma_y_cobra_domicilio():
    c = Carrito()
    c.agregar("emp_carne"); c.agregar("emp_carne"); c.agregar("gaseosa")
    assert c.subtotal == 3_500 * 2 + 3_000
    assert c.total == c.subtotal + DOMICILIO
    assert "2 x Empanada de carne" in c.resumen()


def test_carrito_vacio_no_cobra_domicilio():
    assert Carrito().total == 0
    assert "vacío" in Carrito().resumen()


def test_no_agrega_productos_inexistentes_ni_sin_limite():
    c = Carrito()
    assert not c.agregar("pizza")
    for _ in range(50):
        assert c.agregar("emp_queso")
    assert not c.agregar("emp_queso")


def test_quitar():
    c = Carrito(); c.agregar("combo"); c.agregar("combo")
    c.quitar("combo"); assert c.items == {"combo": 1}
    c.quitar("combo"); assert c.vacio


def test_crear_pedido_numera_guarda_y_arma_aviso(tmp_path):
    reg = RegistroPedidos(tmp_path / "p.json")
    c = Carrito(); c.agregar("combo")
    p = reg.crear(10, "Ana Ruiz", "  Cra 45 # 10-20,   Laureles  ", c, ahora=datetime(2026, 11, 18, 12, 30))
    assert p.numero == 1 and p.direccion == "Cra 45 # 10-20, Laureles"
    assert p.total == 22_000 + DOMICILIO
    assert "Pedido #1" in aviso_para_dueno(p) and "Combo x6" in aviso_para_dueno(p)
    assert RegistroPedidos(tmp_path / "p.json").del_dia("2026-11-18")[0].cliente == "Ana Ruiz"


def test_rechaza_carrito_vacio_y_direccion_corta():
    reg = RegistroPedidos()
    with pytest.raises(ValueError):
        reg.crear(1, "x", "Calle 10 # 20-30", Carrito())
    c = Carrito(); c.agregar("gaseosa")
    with pytest.raises(ValueError):
        reg.crear(1, "x", "aquí", c)


def test_formato_pesos():
    assert pesos(22000) == "$22.000"
