import random
from itertools import combinations
from config import CARD_RANKS, CARD_SUITS, HAND_RANKINGS, STARTING_CHIPS

# Unicode card emojis
CARD_EMOJIS = {
    ('A', '♠'): '🂡', ('K', '♠'): '🂮', ('Q', '♠'): '🂭', ('J', '♠'): '🂫',
    ('10', '♠'): '🂪', ('9', '♠'): '🂩', ('8', '♠'): '🂨', ('7', '♠'): '🂧',
    ('6', '♠'): '🂦', ('5', '♠'): '🂥', ('4', '♠'): '🂤', ('3', '♠'): '🂣',
    ('2', '♠'): '🂢',
    
    ('A', '♥'): '🂱', ('K', '♥'): '🂾', ('Q', '♥'): '🂽', ('J', '♥'): '🂻',
    ('10', '♥'): '🂺', ('9', '♥'): '🂹', ('8', '♥'): '🂸', ('7', '♥'): '🂷',
    ('6', '♥'): '🂶', ('5', '♥'): '🂵', ('4', '♥'): '🂴', ('3', '♥'): '🂳',
    ('2', '♥'): '🂲',
    
    ('A', '♦'): '🃁', ('K', '♦'): '🃎', ('Q', '♦'): '🃍', ('J', '♦'): '🃋',
    ('10', '♦'): '🃊', ('9', '♦'): '🃉', ('8', '♦'): '🃈', ('7', '♦'): '🃇',
    ('6', '♦'): '🃆', ('5', '♦'): '🃅', ('4', '♦'): '🃄', ('3', '♦'): '🃃',
    ('2', '♦'): '🃂',
    
    ('A', '♣'): '🃑', ('K', '♣'): '🃞', ('Q', '♣'): '🃝', ('J', '♣'): '🃛',
    ('10', '♣'): '🃚', ('9', '♣'): '🃙', ('8', '♣'): '🃘', ('7', '♣'): '🃗',
    ('6', '♣'): '🃖', ('5', '♣'): '🃕', ('4', '♣'): '🃔', ('3', '♣'): '🃓',
    ('2', '♣'): '🃒',
}

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
    
    def __str__(self):
        # Return emoji if available, otherwise text format
        return CARD_EMOJIS.get((self.rank, self.suit), f"{self.rank}{self.suit}")
    
    def __repr__(self):
        return self.__str__()
    
    def get_text_repr(self):
        """Get text representation (without emoji)"""
        return f"{self.rank}{self.suit}"
    
    def get_value(self):
        """Get numeric value for card"""
        if self.rank == 'A':
            return 14
        elif self.rank == 'K':
            return 13
        elif self.rank == 'Q':
            return 12
        elif self.rank == 'J':
            return 11
        else:
            return int(self.rank)

class Deck:
    def __init__(self):
        self.cards = []
        self.reset()
    
    def reset(self):
        """Create new deck"""
        self.cards = [Card(rank, suit) for rank in CARD_RANKS for suit in CARD_SUITS]
        random.shuffle(self.cards)
    
    def draw(self):
        """Draw a card from deck"""
        return self.cards.pop() if self.cards else None

class PokerGame:
    def __init__(self, players):
        self.players = players  # List of player objects {id, name, chips}
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.game_stage = 'pre-flop'  # pre-flop, flop, turn, river, showdown
        self.player_hands = {}
        self.player_bets = {}
        self.active_players = set()
        
        self.initialize_game()
    
    def initialize_game(self):
        """Initialize game state"""
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.game_stage = 'pre-flop'
        self.active_players = {p['id'] for p in self.players}
        
        # Deal hole cards
        for player in self.players:
            self.player_hands[player['id']] = [self.deck.draw(), self.deck.draw()]
            self.player_bets[player['id']] = 0
    
    def get_hole_cards(self, player_id):
        """Get player's hole cards"""
        return self.player_hands.get(player_id, [])
    
    def flop(self):
        """Deal the flop"""
        if len(self.community_cards) == 0:
            self.community_cards = [self.deck.draw() for _ in range(3)]
            self.game_stage = 'flop'
    
    def turn(self):
        """Deal the turn"""
        if len(self.community_cards) == 3:
            self.community_cards.append(self.deck.draw())
            self.game_stage = 'turn'
    
    def river(self):
        """Deal the river"""
        if len(self.community_cards) == 4:
            self.community_cards.append(self.deck.draw())
            self.game_stage = 'river'
    
    def place_bet(self, player_id, amount):
        """Place bet"""
        if player_id in self.active_players:
            self.player_bets[player_id] = amount
            self.pot += amount
            self.current_bet = amount
            return True
        return False
    
    def fold(self, player_id):
        """Player folds"""
        self.active_players.discard(player_id)
    
    def evaluate_hand(self, player_id):
        """Evaluate best 5-card hand"""
        hole_cards = self.player_hands[player_id]
        all_cards = hole_cards + self.community_cards
        
        best_hand = None
        best_rank = -1
        
        # Generate all 5-card combinations
        for combo in combinations(all_cards, 5):
            rank = self.classify_hand(list(combo))
            if rank > best_rank:
                best_rank = rank
                best_hand = combo
        
        return best_hand, best_rank
    
    def classify_hand(self, cards):
        """Classify hand strength (0-9)"""
        # Sort by value
        sorted_cards = sorted(cards, key=lambda c: c.get_value(), reverse=True)
        values = [c.get_value() for c in sorted_cards]
        suits = [c.suit for c in sorted_cards]
        
        # Check hand type
        is_flush = len(set(suits)) == 1
        is_straight = self.check_straight(values)
        
        value_counts = {}
        for v in values:
            value_counts[v] = value_counts.get(v, 0) + 1
        
        counts = sorted(value_counts.values(), reverse=True)
        
        # Determine hand rank
        if is_straight and is_flush:
            if values == [14, 13, 12, 11, 10]:
                return 9  # Royal flush
            return 8  # Straight flush
        elif counts == [4, 1]:
            return 7  # Four of a kind
        elif counts == [3, 2]:
            return 6  # Full house
        elif is_flush:
            return 5  # Flush
        elif is_straight:
            return 4  # Straight
        elif counts == [3, 1, 1]:
            return 3  # Three of a kind
        elif counts == [2, 2, 1]:
            return 2  # Two pair
        elif counts == [2, 1, 1, 1]:
            return 1  # Pair
        else:
            return 0  # High card
    
    def check_straight(self, values):
        """Check if cards form a straight"""
        sorted_vals = sorted(values, reverse=True)
        
        # Check regular straight
        if sorted_vals == list(range(sorted_vals[0], sorted_vals[0]-5, -1)):
            return True
        
        # Check A-2-3-4-5 (wheel)
        if sorted_vals == [14, 5, 4, 3, 2]:
            return True
        
        return False
    
    def determine_winner(self):
        """Determine game winner"""
        if len(self.active_players) == 1:
            # Everyone folded
            return list(self.active_players)[0]
        
        # Evaluate all active players
        best_hand_rank = -1
        winner = None
        
        for player_id in self.active_players:
            _, hand_rank = self.evaluate_hand(player_id)
            if hand_rank > best_hand_rank:
                best_hand_rank = hand_rank
                winner = player_id
        
        return winner
    
    def get_game_state(self):
        """Get current game state"""
        return {
            'pot': self.pot,
            'community_cards': self.community_cards,
            'stage': self.game_stage,
            'active_players': list(self.active_players),
            'current_bet': self.current_bet
        }
    
    def get_hand_name(self, player_id):
        """Get name of player's hand"""
        _, hand_rank = self.evaluate_hand(player_id)
        
        hand_names = [
            'High Card', 'Pair', 'Two Pair', 'Three of a Kind',
            'Straight', 'Flush', 'Full House', 'Four of a Kind',
            'Straight Flush', 'Royal Flush'
        ]
        
        return hand_names[hand_rank] if hand_rank >= 0 else 'Unknown'
