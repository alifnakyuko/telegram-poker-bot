"""
Command and button handlers for poker bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from game_manager import GameManager
from leaderboard import get_leaderboard_text, get_player_stats_text, get_top_3_text
from database import db
from config import STARTING_CHIPS, MIN_BET
import uuid

# Global storage for games
active_games = {}  # group_id -> GameManager
game_players = {}  # group_id -> list of players
pending_game_start = {}  # group_id -> session_id

async def send_hole_cards(context: CallbackContext, player_id: str, player_name: str, group_id: int):
    """Send hole cards to player via private message"""
    game = active_games.get(group_id)
    if not game:
        return
    
    cards = game.get_player_hole_cards(int(player_id))
    cards_str = " ".join([str(c) for c in cards])
    
    try:
        await context.bot.send_message(
            chat_id=player_id,
            text=f"🎴 Kartu Anda di grup:\n\n{cards_str}",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error sending hole cards: {e}")

async def send_game_status(context: CallbackContext, group_id: int, game: GameManager):
    """Send game status to group"""
    state = game.get_game_state()
    
    status_text = f"""
🎮 **POKER GAME STATUS**

💰 **POT:** {state['pot']} chips
📊 **Current Bet:** {state['current_bet']} chips
🎯 **Phase:** {state['phase']}
👥 **Active Players:** {state['active_players']}
😔 **Folded:** {state['folded_count']} | 💥 **All-in:** {state['all_in_count']}

🃏 **Community Cards:**
{' '.join(state['community_cards']) if state['community_cards'] else 'Not yet'}

{'⏳ Waiting for: ' + state['current_player'] if state['current_player'] else 'Showdown!'}
"""
    
    try:
        await context.bot.send_message(
            chat_id=group_id,
            text=status_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error sending game status: {e}")

async def send_player_action_menu(context: CallbackContext, player_id: str, group_id: int, game: GameManager):
    """Send action menu buttons to player"""
    player = game.get_current_player()
    
    if not player or player['id'] != int(player_id):
        return
    
    keyboard = [
        [
            InlineKeyboardButton("Check ✓", callback_data=f"check_{group_id}"),
            InlineKeyboardButton("Fold 🛑", callback_data=f"fold_{group_id}")
        ],
        [
            InlineKeyboardButton("Call 📞", callback_data=f"call_{group_id}"),
            InlineKeyboardButton("Raise 📈", callback_data=f"raise_{group_id}")
        ],
        [
            InlineKeyboardButton("All-in 💥", callback_data=f"allin_{group_id}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    action_text = f"""
🎯 **Giliran Anda!**

💰 Your Chips: {player['chips']}
📊 Current Bet: {game.current_bet}
💵 Need to Call: {game.current_bet - game.player_bets[int(player_id)]}
"""
    
    try:
        await context.bot.send_message(
            chat_id=player_id,
            text=action_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error sending action menu: {e}")

async def handle_check(context: CallbackContext, player_id: int, group_id: int):
    """Handle check action"""
    game = active_games.get(group_id)
    if not game:
        return
    
    success, message = game.check(player_id)
    
    if success:
        await context.bot.send_message(
            chat_id=group_id,
            text=f"✓ {game.get_player_hole_cards(player_id) and 'Someone' or 'Player'} checked"
        )
    else:
        await context.bot.send_message(chat_id=player_id, text=f"❌ {message}")

async def handle_fold(context: CallbackContext, player_id: int, group_id: int):
    """Handle fold action"""
    game = active_games.get(group_id)
    if not game:
        return
    
    success, message = game.fold(player_id)
    
    if success:
        # Find player name
        player_name = "Player"
        for p in game.players:
            if p['id'] == player_id:
                player_name = p['name']
                break
        
        await context.bot.send_message(
            chat_id=group_id,
            text=f"🛑 {player_name} folded!"
        )
        
        # Check if only 1 player left
        active = game.get_active_players()
        if len(active) == 1:
            winner = active[0]
            await context.bot.send_message(
                chat_id=group_id,
                text=f"🏆 **{winner['name']} wins!**\n\n💰 Pot: {game.pot} chips"
            )
            game.status = 'ended'
    else:
        await context.bot.send_message(chat_id=player_id, text=f"❌ {message}")

async def handle_call(context: CallbackContext, player_id: int, group_id: int):
    """Handle call action"""
    game = active_games.get(group_id)
    if not game:
        return
    
    success, message = game.call_bet(player_id)
    
    if success:
        # Find player name
        player_name = "Player"
        for p in game.players:
            if p['id'] == player_id:
                player_name = p['name']
                break
        
        await context.bot.send_message(
            chat_id=group_id,
            text=f"📞 {player_name} called!"
        )
    else:
        await context.bot.send_message(chat_id=player_id, text=f"❌ {message}")

async def handle_raise(context: CallbackContext, player_id: int, group_id: int, amount: int):
    """Handle raise action"""
    game = active_games.get(group_id)
    if not game:
        return
    
    success, message = game.raise_bet(player_id, amount)
    
    if success:
        # Find player name
        player_name = "Player"
        for p in game.players:
            if p['id'] == player_id:
                player_name = p['name']
                break
        
        await context.bot.send_message(
            chat_id=group_id,
            text=f"📈 {player_name} raised {amount} chips!"
        )
    else:
        await context.bot.send_message(chat_id=player_id, text=f"❌ {message}")

async def handle_allin(context: CallbackContext, player_id: int, group_id: int):
    """Handle all-in action"""
    game = active_games.get(group_id)
    if not game:
        return
    
    success, message = game.all_in(player_id)
    
    if success:
        # Find player name
        player_name = "Player"
        for p in game.players:
            if p['id'] == player_id:
                player_name = p['name']
                break
        
        await context.bot.send_message(
            chat_id=group_id,
            text=f"💥 {player_name} is ALL-IN!"
        )
    else:
        await context.bot.send_message(chat_id=player_id, text=f"❌ {message}")

async def progress_game(context: CallbackContext, group_id: int):
    """Progress game to next phase or continue betting"""
    game = active_games.get(group_id)
    if not game or game.status != 'playing':
        return
    
    # Check if betting round is complete
    if game.check_betting_complete():
        # Move to next phase
        game.next_phase()
        
        if game.status == 'showdown':
            # Evaluate hands and determine winner
            winner = game.determine_winner()
            
            # Send showdown results
            if winner:
                await context.bot.send_message(
                    chat_id=group_id,
                    text=f"🏆 **SHOWDOWN!**\n\n🥇 **{winner['name']} wins!**\n💰 **{game.pot} chips**"
                )
                game.end_game()
                del active_games[group_id]
                if group_id in game_players:
                    del game_players[group_id]
        else:
            # Continue to next phase
            await send_game_status(context, group_id, game)
            
            # Send action menu to current player
            current = game.get_current_player()
            if current:
                await send_player_action_menu(context, str(current['id']), group_id, game)
    else:
        # Continue to next player
        current = game.get_current_player()
        if current:
            await send_player_action_menu(context, str(current['id']), group_id, game)
