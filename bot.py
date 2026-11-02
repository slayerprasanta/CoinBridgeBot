import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# States define karte hain
CHOOSING, BUY_NET, BUY_TXN, BUY_WALLET, SELL_NET, SELL_TXN, SELL_PAY_METHOD, SELL_PAY_DETAILS = range(8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("BUY", callback_data="BUY")],
        [InlineKeyboardButton("SELL", callback_data="SELL")],
        [InlineKeyboardButton("SUPPORT", callback_data="SUPPORT")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("Welcome to CoinBridge! Please select an option:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Welcome to CoinBridge! Please select an option:", reply_markup=reply_markup)
        
    return CHOOSING

async def main_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "SUPPORT":
        await query.edit_message_text("We will reach you immediately.")
        return ConversationHandler.END

    elif choice == "BUY":
        keyboard = [
            [InlineKeyboardButton("BEP20", callback_data="BEP20")],
            [InlineKeyboardButton("TRC20", callback_data="TRC20")],
            [InlineKeyboardButton("ERC20", callback_data="ERC20")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Please select Network for BUY:", reply_markup=reply_markup)
        return BUY_NET

    elif choice == "SELL":
        keyboard = [
            [InlineKeyboardButton("BTC", callback_data="BTC")],
            [InlineKeyboardButton("BEP20", callback_data="BEP20")],
            [InlineKeyboardButton("TRC20", callback_data="TRC20")],
            [InlineKeyboardButton("ERC20", callback_data="ERC20")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Please select Crypto/Network for SELL:", reply_markup=reply_markup)
        return SELL_NET

# --- BUY FLOW ---
async def buy_network_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['buy_network'] = query.data
    
    await query.edit_message_text(f"Selected Network: {query.data}\n\nPlease Provide Transaction ID:")
    return BUY_TXN

async def buy_txn_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txn_id = update.message.text
    context.user_data['buy_txn'] = txn_id
    
    msg = await update.message.reply_text("Wait 20-25 sec.\nOur team are verifying your order.")
    await asyncio.sleep(5)
    
    await msg.edit_text("Successful.\nPlease provide your wallet address:")
    return BUY_WALLET

async def buy_wallet_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = update.message.text
    msg = await update.message.reply_text("Processing...")
    await asyncio.sleep(5)
    
    await msg.edit_text("Transfer Successfully.\nCheck your wallet.")
    return ConversationHandler.END

# --- SELL FLOW ---
async def sell_network_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['sell_network'] = query.data
    
    await query.edit_message_text(f"Selected: {query.data}\n\nPlease Provide Transaction ID from Wallet:")
    return SELL_TXN

async def sell_txn_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txn_id = update.message.text
    msg = await update.message.reply_text("Wait 20-25 sec.\nOur team are verifying.")
    
    await asyncio.sleep(5)
    
    keyboard = [
        [InlineKeyboardButton("UPI", callback_data="UPI")],
        [InlineKeyboardButton("IMPS", callback_data="IMPS")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await msg.edit_text("Successful.\nPlease select how you can receive INR:", reply_markup=reply_markup)
    return SELL_PAY_METHOD

async def sell_pay_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data
    context.user_data['pay_method'] = method

    if method == "UPI":
        await query.edit_message_text("Please provide your UPI ID:")
    else:
        await query.edit_message_text("Please provide your Acc No and IFSC:")
    
    return SELL_PAY_DETAILS

async def sell_pay_details_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    details = update.message.text
    msg = await update.message.reply_text("Processing Over.\nTeam are doing process.")
    
    await asyncio.sleep(3)
    await msg.edit_text("Transfer Successfully completed.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Process cancelled.")
    return ConversationHandler.END

import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- Render port timeout fix ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"CoinBridge Bot is alive and running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Background thread me HTTP server start kar rahe hain taaki Render khush rahe
threading.Thread(target=run_dummy_server, daemon=True).start()
# ---------------------------------

if __name__ == '__main__':
    TOKEN = "9033084725:AAGuYW5s9A4ZXrXYn35NWlrFNIMrMaRegm8"
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [CallbackQueryHandler(main_menu_choice)],
            BUY_NET: [CallbackQueryHandler(buy_network_selected)],
            BUY_TXN: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_txn_received)],
            BUY_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_wallet_received)],
            SELL_NET: [CallbackQueryHandler(sell_network_selected)],
            SELL_TXN: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_txn_received)],
            SELL_PAY_METHOD: [CallbackQueryHandler(sell_pay_method_selected)],
            SELL_PAY_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_pay_details_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    app.add_handler(conv_handler)
    
    print("CoinBridge Bot successfully start ho gaya hai...")
    app.run_polling()
