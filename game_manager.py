import asyncio
import uuid
from datetime import datetime
from game import PokerGame, Deck
from database import db
from config import STARTING_CHIPS, MIN_BET

class GameManager:
    """Manages individual poker game sessions"""
    
    def __init__(self, session_id, group_id, players):
        self.session_id = session_id
        self.group_id = group_id
        self.players = players  # List of {id, name, username, chips}
        self.game = None
        self.current_turn_index = 0
        self.status = 'pre-game'  # pre-game, playing, showdown, ended
        self.pot = 0
        self.current_bet = 0
        self.community_cards = []
        self.player_actions = {}  # Track who has acted
        self.player_bets = {}  # Track individual bets this round
        self.all_in_players = set()
        self.folded_players = set()
        self.last_bet_player = None
        self.betting_complete = False
        
        self.initialize_players()
    
    def initialize_players(self):
        """Initialize player data for game"""
        for player in self.players:
            player_id = player['id']
            self.player_actions[player_id] = False
            self.player_bets[player_id] = 0
    
    def start_game(self):
        """Start the poker game"""
        if len(self.players) < 2:
            return False, "Minimal 2 pemain untuk memulai permainan"
        
        # Create deck and deal cards
        self.game = PokerGame(self.players)
        self.status = 'playing'
        self.current_turn_index = 0
        self.betting_complete = False
        
        # Reset betting info
        for player in self.players:
            self.player_actions[player['id']] = False
            self.player_bets[player['id']] = 0
        
        return True, "Permainan dimulai!"
    
    def get_current_player(self):
        """Get current player whose turn it is"""
        if self.status != 'playing':
            return None
        
        # Skip folded and all-in players
        for i in range(len(self.players)):
            idx = (self.current_turn_index + i) % len(self.players)
            player_id = self.players[idx]['id']
            
            if player_id not in self.folded_players and player_id not in self.all_in_players:
                return self.players[idx]
        
        return None
    
    def next_player(self):
        """Move to next player"""
        self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
    
    def get_active_players(self):
        """Get players still in game (not folded)"""
        active = []
        for player in self.players:
            if player['id'] not in self.folded_players:
                active.append(player)
        return active
    
    def get_player_hole_cards(self, player_id):
        """Get player's hole cards"""
        if not self.game:
            return []
        return self.game.get_hole_cards(player_id)
    
    def get_game_state(self):
        """Get current game state for display"""
        active = self.get_active_players()
        current = self.get_current_player()
        
        return {
            'pot': self.pot,
            'current_bet': self.current_bet,
            'community_cards': self.community_cards,
            'active_players': len(active),
            'current_player': current['name'] if current else None,
            'phase': self.game.game_stage if self.game else 'pre-flop',
            'folded_count': len(self.folded_players),
            'all_in_count': len(self.all_in_players)
        }
    
    def place_bet(self, player_id, bet_amount):
        """Place a bet"""
        # Find player
        player = None
        for p in self.players:
            if p['id'] == player_id:
                player = p
                break
        
        if not player:
            return False, "Pemain tidak ditemukan"
        
        if player_id in self.folded_players:
            return False, "Anda sudah fold"
        
        if player_id in self.all_in_players:
            return False, "Anda sudah all-in"
        
        if bet_amount < MIN_BET:
            return False, f"Taruhan minimal {MIN_BET} chips"
        
        if bet_amount > player['chips']:
            return False, f"Chip tidak cukup (punya: {player['chips']})"
        
        # Deduct from player chips
        player['chips'] -= bet_amount
        self.player_bets[player_id] += bet_amount
        self.pot += bet_amount
        self.current_bet = max(self.current_bet, bet_amount)
        self.last_bet_player = player_id
        self.player_actions[player_id] = True
        
        # Next player
        self.next_player()
        
        return True, f"Bet {bet_amount} chips ditempatkan"
    
    def call_bet(self, player_id):
        """Call current bet"""
        player = None
        for p in self.players:
            if p['id'] == player_id:
                player = p
                break
        
        if not player:
            return False, "Pemain tidak ditemukan"
        
        if player_id in self.folded_players:
            return False, "Anda sudah fold"
        
        if player_id in self.all_in_players:
            return False, "Anda sudah all-in"
        
        call_amount = self.current_bet - self.player_bets[player_id]
        
        if call_amount > player['chips']:
            # Force all-in
            call_amount = player['chips']
            self.all_in_players.add(player_id)
        
        player['chips'] -= call_amount
        self.player_bets[player_id] += call_amount
        self.pot += call_amount
        self.player_actions[player_id] = True
        
        # Next player
        self.next_player()
        
        return True, f"Call {call_amount} chips"
    
    def raise_bet(self, player_id, raise_amount):
        """Raise the bet"""
        player = None
        for p in self.players:
            if p['id'] == player_id:
                player = p
                break
        
        if not player:
            return False, "Pemain tidak ditemukan"
        
        if player_id in self.folded_players:
            return False, "Anda sudah fold"
        
        if player_id in self.all_in_players:
            return False, "Anda sudah all-in"
        
        total_bet = self.player_bets[player_id] + raise_amount
        
        if raise_amount < MIN_BET:
            return False, f"Raise minimal {MIN_BET} chips"
        
        if raise_amount > player['chips']:
            return False, f"Chip tidak cukup (punya: {player['chips']})"
        
        if total_bet <= self.current_bet:
            return False, f"Raise harus lebih tinggi dari {self.current_bet}"
        
        player['chips'] -= raise_amount
        self.player_bets[player_id] += raise_amount
        self.pot += raise_amount
        self.current_bet = total_bet
        self.last_bet_player = player_id
        self.player_actions[player_id] = True
        self.betting_complete = False  # Reset betting round
        
        # Reset other players' actions
        for p_id in self.player_actions:
            if p_id != player_id:
                self.player_actions[p_id] = False
        
        # Next player
        self.next_player()
        
        return True, f"Raise {raise_amount} chips (total: {total_bet})"
    
    def check(self, player_id):
        """Check (pass without betting)"""
        if self.current_bet > 0:
            return False, "Tidak bisa check jika ada bet"
        
        if player_id in self.folded_players:
            return False, "Anda sudah fold"
        
        self.player_actions[player_id] = True
        self.next_player()
        
        return True, "Check"
    
    def fold(self, player_id):
        """Fold hand"""
        if player_id in self.folded_players:
            return False, "Anda sudah fold"
        
        self.folded_players.add(player_id)
        self.player_actions[player_id] = True
        self.next_player()
        
        return True, "Anda fold"
    
    def all_in(self, player_id):
        """Go all-in"""
        player = None
        for p in self.players:
            if p['id'] == player_id:
                player = p
                break
        
        if not player:
            return False, "Pemain tidak ditemukan"
        
        if player_id in self.folded_players:
            return False, "Anda sudah fold"
        
        if player_id in self.all_in_players:
            return False, "Anda sudah all-in"
        
        if player['chips'] == 0:
            return False, "Anda tidak punya chip"
        
        # All remaining chips go in
        all_in_amount = player['chips']
        player['chips'] = 0
        self.player_bets[player_id] += all_in_amount
        self.pot += all_in_amount
        self.all_in_players.add(player_id)
        self.player_actions[player_id] = True
        
        if all_in_amount > 0:
            self.current_bet = max(self.current_bet, self.player_bets[player_id])
            self.last_bet_player = player_id
        
        self.next_player()
        
        return True, f"All-in {all_in_amount} chips!"
    
    def check_betting_complete(self):
        """Check if betting round is complete"""
        active = self.get_active_players()
        not_all_in = [p for p in active if p['id'] not in self.all_in_players]
        
        if len(not_all_in) <= 1:
            return True  # Only 1 or 0 players who can bet
        
        # All players have acted and current bets are equal
        for player in not_all_in:
            if not self.player_actions[player['id']]:
                return False
            if self.player_bets[player['id']] != self.current_bet:
                return False
        
        return True
    
    def next_phase(self):
        """Move to next game phase"""
        if not self.game:
            return
        
        if self.game.game_stage == 'pre-flop':
            self.game.flop()
            self.community_cards = [str(c) for c in self.game.community_cards]
        elif self.game.game_stage == 'flop':
            self.game.turn()
            self.community_cards = [str(c) for c in self.game.community_cards]
        elif self.game.game_stage == 'turn':
            self.game.river()
            self.community_cards = [str(c) for c in self.game.community_cards]
        elif self.game.game_stage == 'river':
            self.status = 'showdown'
        
        # Reset betting for new round
        if self.status == 'playing':
            for player_id in self.player_actions:
                self.player_actions[player_id] = False
            self.current_bet = 0
            self.betting_complete = False
            self.last_bet_player = None
    
    def determine_winner(self):
        """Determine game winner"""
        active = self.get_active_players()
        
        if len(active) == 1:
            return active[0]
        
        # Multiple players - evaluate hands
        best_player = None
        best_rank = -1
        
        for player in active:
            _, hand_rank = self.game.evaluate_hand(player['id'])
            if hand_rank > best_rank:
                best_rank = hand_rank
                best_player = player
        
        return best_player
    
    def end_game(self):
        """End game and update database"""
        winner = self.determine_winner()
        
        if winner:
            winner['chips'] += self.pot
            db.update_player_chips(winner['id'], winner['chips'], won_game=True)
            
            # Update losers
            for player in self.players:
                if player['id'] != winner['id']:
                    db.update_player_chips(player['id'], player['chips'], won_game=False)
                    # Save game result
                    rank = 2 if len(self.players) == 2 else 3
                    db.save_game_result(self.session_id, player['id'], player['chips'], rank)
            
            # Save winner
            db.save_game_result(self.session_id, winner['id'], winner['chips'], 1)
        
        self.status = 'ended'
        return winner
