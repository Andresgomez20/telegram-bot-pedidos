# Bot de pedidos para Telegram

Bot para negocios de comida o tiendas pequeñas: el cliente ve el catálogo con botones, arma su pedido, escribe la dirección y el bot **le avisa al dueño con el pedido completo**. Hecho con [python-telegram-bot](https://python-telegram-bot.org/).

*English below.*

## Qué hace

- `/start` muestra el catálogo con botones para agregar productos; el mensaje se actualiza con el carrito y el total.
- Botones para vaciar el carrito o confirmar el pedido.
- Pide la dirección, valida que no esté vacía, numera el pedido y lo guarda.
- Envía el pedido al chat del dueño.
- `/cancelar` borra el pedido en curso y `/miid` muestra el chat id (para configurar al dueño).

## Estructura

| Archivo | Qué hace |
|---|---|
| `pedidos.py` | Catálogo, carrito, totales con domicilio, registro de pedidos en JSON y aviso al dueño. No depende de Telegram. |
| `bot.py` | Conexión con Telegram: comandos, botones y mensajes. |
| `tests/` | Pruebas de la lógica de pedidos. |

Para otro negocio, cambia `NEGOCIO`, `CATALOGO` y `DOMICILIO` en `pedidos.py`.

## Instalación y uso

```bash
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

1. En Telegram, habla con **@BotFather**, crea un bot con `/newbot` y pega el token en `TELEGRAM_TOKEN`.
2. Arranca el bot con `python bot.py`.
3. Desde la cuenta del dueño, escríbele `/miid` al bot y pega ese número en `TELEGRAM_CHAT_DUENO`. Reinicia el bot.
4. Haz un pedido de prueba con `/start`.

## Pruebas

```bash
python3 -m pytest
```

## Despliegue

El bot usa *long polling*, así que no necesita una dirección pública: basta con un servicio que mantenga el proceso encendido (Render, Railway, Fly.io o un VPS). Comando de inicio: `python bot.py`.

---

## English

Telegram ordering bot for small food businesses and shops. Customers browse an inline-keyboard catalog, build a cart with live totals (including delivery), send their address, and the owner receives the full order in Telegram. The business logic in `pedidos.py` is framework-independent and unit-tested; `bot.py` wires it to python-telegram-bot v21. Setup: create a bot with @BotFather, put the token in `.env`, run `python bot.py`. Tests: `python3 -m pytest`.

---

Hecho por **Jorge Andrés Gómez** · [Portafolio](https://andresgomez20.github.io/) · WhatsApp +57 322 789 1135
