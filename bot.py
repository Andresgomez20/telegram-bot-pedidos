"""Bot de pedidos para Telegram. Ejecuta:  python bot.py"""

import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from pedidos import CATALOGO, NEGOCIO, Carrito, RegistroPedidos, aviso_para_dueno, pesos

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_DUENO = int(os.getenv("TELEGRAM_CHAT_DUENO", "0") or 0)
registro = RegistroPedidos(os.getenv("ARCHIVO_PEDIDOS", "datos/pedidos.json"))


def carrito_de(context: ContextTypes.DEFAULT_TYPE) -> Carrito:
    return context.user_data.setdefault("carrito", Carrito())


def teclado_catalogo(carrito: Carrito) -> InlineKeyboardMarkup:
    filas = [[InlineKeyboardButton(f"➕ {p.nombre} · {pesos(p.precio)}", callback_data=f"add:{p.id}")] for p in CATALOGO.values()]
    if not carrito.vacio:
        filas.append([InlineKeyboardButton("🗑 Vaciar", callback_data="vaciar"), InlineKeyboardButton(f"✅ Pedir · {pesos(carrito.total)}", callback_data="pedir")])
    return InlineKeyboardMarkup(filas)


async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["esperando_direccion"] = False
    carrito = carrito_de(context)
    await update.message.reply_text(
        f"¡Hola! 👋 Bienvenido a *{NEGOCIO}*.\nToca los productos para agregarlos a tu pedido.",
        parse_mode=ParseMode.MARKDOWN, reply_markup=teclado_catalogo(carrito),
    )


async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    consulta = update.callback_query
    carrito = carrito_de(context)
    dato = consulta.data or ""

    if dato.startswith("add:"):
        if carrito.agregar(dato.removeprefix("add:")):
            await consulta.answer("Agregado ✅")
        else:
            await consulta.answer("No se pudo agregar", show_alert=True)
        await consulta.edit_message_text(f"Tu pedido:\n{carrito.resumen()}", parse_mode=ParseMode.MARKDOWN, reply_markup=teclado_catalogo(carrito))
    elif dato == "vaciar":
        carrito.vaciar()
        await consulta.answer("Carrito vacío")
        await consulta.edit_message_text("Carrito vacío. Toca un producto para empezar.", reply_markup=teclado_catalogo(carrito))
    elif dato == "pedir":
        await consulta.answer()
        if carrito.vacio:
            await consulta.edit_message_text("Tu carrito está vacío.", reply_markup=teclado_catalogo(carrito))
            return
        context.user_data["esperando_direccion"] = True
        await consulta.edit_message_text(f"{carrito.resumen()}\n\n📍 Escríbeme la *dirección de entrega* (con barrio y referencias).", parse_mode=ParseMode.MARKDOWN)


async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("esperando_direccion"):
        await update.message.reply_text("Escribe /start para ver el menú y hacer tu pedido.")
        return
    carrito = carrito_de(context)
    usuario = update.effective_user
    try:
        pedido = registro.crear(update.effective_chat.id, usuario.full_name, update.message.text, carrito)
    except ValueError as error:
        await update.message.reply_text(f"⚠️ {error}. Inténtalo de nuevo, por favor.")
        return
    context.user_data["esperando_direccion"] = False
    carrito.vaciar()
    await update.message.reply_text(f"¡Pedido #{pedido.numero} recibido! 🙌 Total {pesos(pedido.total)}. Te avisamos cuando salga el domicilio.")
    if CHAT_DUENO:
        await context.bot.send_message(CHAT_DUENO, aviso_para_dueno(pedido))


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    carrito_de(context).vaciar()
    context.user_data["esperando_direccion"] = False
    await update.message.reply_text("Pedido cancelado. Escribe /start cuando quieras volver.")


async def mi_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sirve para que el dueño sepa qué número poner en TELEGRAM_CHAT_DUENO."""
    await update.message.reply_text(f"Tu chat id es: {update.effective_chat.id}")


def main() -> None:
    if not TOKEN:
        raise SystemExit("Falta TELEGRAM_TOKEN. Copia .env.example a .env y pega el token que te da @BotFather.")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", inicio))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("miid", mi_id))
    app.add_handler(CallbackQueryHandler(botones))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto))
    log.info("Bot en marcha. Ctrl+C para detenerlo.")
    app.run_polling()


if __name__ == "__main__":
    main()
