#!/usr/bin/env python3
"""
Telegram Poker Bot - Texas Hold'em Multiplayer Game
"""

import logging
import uuid
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN, STARTING_CHIPS, MIN_BET
from database import db
from game_manager import GameManager
from leaderboard import get_leaderboard_text, get_player_stats_text
from handlers import (
    send_hole_cards, send_game_status, send_player_action_menu,
    handle_check, handle_fold, handle_call, handle_raise, handle_allin,
    progress_game, active_games, game_players, pending_game_start
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: CallbackContext) -> None:
    """Start command"""
    user = update.effective_user
    
    # Register player
    db.add_player(user.id, user.username or f"user_{user.id}", user.first_name)
    
    welcome_text = f"""
👋 Selamat datang di **Telegram Poker Bot**!

Saya adalah bot untuk memainkan **Texas Hold'em Poker** di grup Telegram.

📋 **Perintah Tersedia:**
/help - Bantuan & cara bermain
/leaderboard - Lihat ranking pemain
/stats - Lihat statistik Anda
/startgame - Mulai permainan poker baru (di grup)
/joingame - Bergabung dengan permainan

🎮 **Cara Bermain:**
1. Tambahkan bot ke grup Anda
2. Gunakan /startgame untuk memulai permainan
3. Pemain lain bergabung dengan /joingame
4. Ikuti instruksi untuk bermain
5. Gunakan tombol atau perintah untuk aksi

💡 Bergabunglah sekarang dan tunjukkan skill poker Anda!
"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: CallbackContext) -> None:
    """Help command"""
    help_text = """
🎮 **TEXAS HOLD'EM POKER - PANDUAN CEPAT**

📌 **Aturan Dasar:**
- Setiap pemain mendapat 2 kartu hole (tertutup)
- 5 kartu komunitas dibagikan bertahap
- Buat tangan terbaik 5-kartu dari 7 kartu total
- Pemain dengan tangan terbaik memenangkan pot

🎯 **Ranking Tangan (tertinggi ke terendah):**
1. Royal Flush
2. Straight Flush
3. Four of a Kind
4. Full House
5. Flush
6. Straight
7. Three of a Kind
8. Two Pair
9. Pair
10. High Card

💰 **Sistem Chip:**
- Starting: 1000 chips per pemain
- Minimum bet: 10 chips
- Chip bisa digunakan di game berikutnya

🎲 **Aksi Permainan:**
- **Check** ✓ - Lanjut tanpa bet
- **Bet** 🎯 - Taruh chip pertama
- **Call** 📞 - Ikuti taruhan
- **Raise** 📈 - Naikkan taruhan
- **Fold** 🛑 - Serah, keluar ronde
- **All-in** 💥 - Taruh semua chip

📊 **Fase Permainan:**
1. Pre-flop - 2 kartu hole
2. Flop - 3 kartu komunitas
3. Turn - 1 kartu komunitas
4. River - 1 kartu komunitas terakhir
5. Showdown - Bandingkan tangan

📄 **Untuk aturan lengkap, lihat RULES.md di repository**

Gunakan /startgame untuk mulai bermain! 🚀
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def leaderboard(update: Update, context: CallbackContext) -> None:
    """Show leaderboard"""
    leaderboard_text = get_leaderboard_text()
    await update.message.reply_text(leaderboard_text, parse_mode='Markdown')

async def stats(update: Update, context: CallbackContext) -> None:
    """Show player statistics"""
    user_id = update.effective_user.id
    stats_text = get_player_stats_text(user_id)
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def start_game(update: Update, context: CallbackContext) -> None:
    """Start a new poker game"""
    group_id = update.effective_chat.id
    user = update.effective_user
    
    # Check if game already running
    if group_id in active_games:
        if active_games[group_id].status != 'ended':
            await update.message.reply_text(
                "❌ Permainan sudah berjalan. Tunggu sampai selesai atau gunakan /endgame"
            )
            return
    
    # Register player
    db.add_player(user.id, user.username or f"user_{user.id}", user.first_name)
    
    # Initialize game
    session_id = str(uuid.uuid4())
    db.create_game_session(session_id, group_id)
    
    game_players[group_id] = [{
        'id': user.id,
        'name': user.first_name,
        'username': user.username or f"user_{user.id}",
        'chips': STARTING_CHIPS
    }]
    
    pending_game_start[group_id] = session_id
    
    keyboard = [[InlineKeyboardButton("➕ Bergabung", callback_data=f"join_{group_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    start_text = f"""
🎮 **PERMAINAN POKER DIMULAI!**

👤 Pembuat: {user.first_name}
🪑 Pemain: 1/10
💰 Starting Chips: {STARTING_CHIPS}

**Pemain yang bergabung:**
1. {user.first_name} (@{user.username or 'user_' + str(user.id)})

Pemain lain bisa bergabung dengan tombol di bawah atau /joingame
⏱️ Ketik /startgame lagi untuk memulai permainan!
"""
    
    await update.message.reply_text(start_text, reply_markup=reply_markup, parse_mode='Markdown')

async def join_game(update: Update, context: CallbackContext) -> None:
    """Join existing game"""
    group_id = update.effective_chat.id
    user = update.effective_user
    
    if group_id not in pending_game_start:
        await update.message.reply_text(
            "❌ Tidak ada permainan yang sedang menunggu pemain. Mulai dengan /startgame"
        )
        return
    
    # Check if already joined
    for player in game_players[group_id]:
        if player['id'] == user.id:
            await update.message.reply_text("❌ Anda sudah bergabung dengan permainan ini")
            return
    
    # Check max players
    if len(game_players[group_id]) >= 10:
        await update.message.reply_text("❌ Permainan sudah penuh (max 10 pemain)")
        return
    
    # Register and add player
    db.add_player(user.id, user.username or f"user_{user.id}", user.first_name)
    
    game_players[group_id].append({
        'id': user.id,
        'name': user.first_name,
        'username': user.username or f"user_{user.id}",
        'chips': STARTING_CHIPS
    })
    
    player_count = len(game_players[group_id])
    
    join_text = f"""
✅ **{user.first_name} bergabung dengan permainan!**

👥 Total Pemain: {player_count}/10

**Pemain dalam permainan:**
"""
    
    for i, p in enumerate(game_players[group_id], 1):
        join_text += f"\n{i}. {p['name']} (@{p['username']}) - {p['chips']} 💰"
    
    join_text += "\n\n_Ketik /startgame lagi untuk memulai permainan!_"
    
    await update.message.reply_text(join_text, parse_mode='Markdown')

async def play_game_command(update: Update, context: CallbackContext) -> None:
    """Actually start the game (second /startgame call)"""
    group_id = update.effective_chat.id
    
    if group_id not in pending_game_start:
        await update.message.reply_text("❌ Tidak ada permainan yang menunggu")
        return
    
    if len(game_players.get(group_id, [])) < 2:
        await update.message.reply_text("❌ Minimal 2 pemain untuk memulai permainan")
        return
    
    # Create game manager
    session_id = pending_game_start[group_id]
    game_manager = GameManager(session_id, group_id, game_players[group_id])
    success, message = game_manager.start_game()
    
    if not success:
        await update.message.reply_text(f"❌ {message}")
        return
    
    active_games[group_id] = game_manager
    del pending_game_start[group_id]
    
    # Send game started message
    player_names = ", ".join([p['name'] for p in game_manager.players])
    await update.message.reply_text(
        f"🎮 **PERMAINAN DIMULAI!**\n\n👥 Pemain: {player_names}",
        parse_mode='Markdown'
    )
    
    await asyncio.sleep(1)
    
    # Send hole cards to each player
    for player in game_manager.players:
        await send_hole_cards(context, str(player['id']), player['name'], group_id)
    
    await asyncio.sleep(1)
    
    # Send game status
    await send_game_status(context, group_id, game_manager)
    
    await asyncio.sleep(1)
    
    # Ask first player to act
    current = game_manager.get_current_player()
    if current:
        await send_player_action_menu(context, str(current['id']), group_id, game_manager)

async def end_game(update: Update, context: CallbackContext) -> None:
    """End current game"""
    group_id = update.effective_chat.id
    
    if group_id not in active_games and group_id not in pending_game_start:
        await update.message.reply_text("❌ Tidak ada permainan aktif")
        return
    
    if group_id in active_games:
        del active_games[group_id]
    if group_id in pending_game_start:
        del pending_game_start[group_id]
    if group_id in game_players:
        del game_players[group_id]
    
    await update.message.reply_text("🛑 Permainan dihentikan. Terima kasih telah bermain!")

# ==================== BUTTON HANDLERS ====================

async def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Join game button
    if data.startswith("join_"):
        group_id = int(data.split("_")[1])
        user = query.from_user
        
        if group_id not in pending_game_start:
            await query.edit_message_text("❌ Permainan sudah dimulai atau tidak ada")
            return
        
        # Check if already joined
        for player in game_players.get(group_id, []):
            if player['id'] == user.id:
                await query.edit_message_text("❌ Anda sudah bergabung")
                return
        
        if len(game_players.get(group_id, [])) >= 10:
            await query.edit_message_text("❌ Permainan penuh")
            return
        
        # Add player
        db.add_player(user.id, user.username or f"user_{user.id}", user.first_name)
        game_players[group_id].append({
            'id': user.id,
            'name': user.first_name,
            'username': user.username or f"user_{user.id}",
            'chips': STARTING_CHIPS
        })
        
        # Update message
        player_count = len(game_players[group_id])
        text = f"""
🎮 **PERMAINAN POKER MENUNGGU**

🪑 Pemain: {player_count}/10

**Pemain yang bergabung:**
"""
        
        for i, p in enumerate(game_players[group_id], 1):
            text += f"\n{i}. {p['name']} - {p['chips']} 💰"
        
        text += "\n\n_Ketik /startgame untuk memulai!_"
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    # Game action buttons
    elif data.startswith("check_"):
        group_id = int(data.split("_")[1])
        player_id = query.from_user.id
        await handle_check(context, player_id, group_id)
        await progress_game(context, group_id)
    
    elif data.startswith("fold_"):
        group_id = int(data.split("_")[1])
        player_id = query.from_user.id
        await handle_fold(context, player_id, group_id)
        await progress_game(context, group_id)
    
    elif data.startswith("call_"):
        group_id = int(data.split("_")[1])
        player_id = query.from_user.id
        await handle_call(context, player_id, group_id)
        await progress_game(context, group_id)
    
    elif data.startswith("allin_"):
        group_id = int(data.split("_")[1])
        player_id = query.from_user.id
        await handle_allin(context, player_id, group_id)
        await progress_game(context, group_id)

async def unknown(update: Update, context: CallbackContext) -> None:
    """Handle unknown commands"""
    await update.message.reply_text(
        "❓ Perintah tidak dikenali. Gunakan /help untuk melihat perintah yang tersedia.",
        parse_mode='Markdown'
    )

def main() -> None:
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN tidak ditemukan. Set di file .env")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("startgame", start_game))
    application.add_handler(CommandHandler("startgame", play_game_command))  # Second call
    application.add_handler(CommandHandler("joingame", join_game))
    application.add_handler(CommandHandler("endgame", end_game))
    
    # Add button handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add unknown command handler
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    # Start bot
    logger.info("🚀 Bot dimulai...")
    print("✅ Bot poker siap! Tekan Ctrl+C untuk menghentikan.")
    application.run_polling()

if __name__ == '__main__':
    main()
