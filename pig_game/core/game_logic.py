# core/game_logic.py
from utils.deck import create_deck, shuffle_deck, get_card_value, get_card_rank

class BaccaratGame:
    def __init__(self):
        self.deck = None
        self.reset_deck()
    
    def reset_deck(self):
        """새로운 덱 생성 및 셔플"""
        self.deck = shuffle_deck(create_deck())
    
    def deal_first_cards(self):
        """첫 번째 카드 분배"""
        if len(self.deck) < 10:  # 카드가 부족하면 새 덱 사용
            self.reset_deck()
        
        player_card = self.deck.pop()
        banker_card = self.deck.pop()
        
        return player_card, banker_card
    
    def deal_second_cards(self):
        """두 번째 카드 분배"""
        player_card = self.deck.pop()
        banker_card = self.deck.pop()
        
        return player_card, banker_card
    
    def calculate_score(self, cards):
        """카드 점수 계산 (바카라 규칙)"""
        total = sum(get_card_value(card) for card in cards)
        return total % 10
    
    def has_pair(self, cards):
        """페어 여부 확인"""
        if len(cards) < 2:
            return False
        
        rank1 = get_card_rank(cards[0])
        rank2 = get_card_rank(cards[1])
        
        return rank1 == rank2
    
    def calculate_result(self, player_cards, banker_cards):
        """게임 결과 계산"""
        player_score = self.calculate_score(player_cards)
        banker_score = self.calculate_score(banker_cards)
        
        # 승자 결정
        if player_score > banker_score:
            winner = 'player'
        elif banker_score > player_score:
            winner = 'banker'
        else:
            winner = 'tie'
        
        # 페어 확인
        has_player_pair = self.has_pair(player_cards)
        has_banker_pair = self.has_pair(banker_cards)
        
        return {
            'player_score': player_score,
            'banker_score': banker_score,
            'winner': winner,
            'player_cards': player_cards,
            'banker_cards': banker_cards,
            'has_player_pair': has_player_pair,
            'has_banker_pair': has_banker_pair
        }
    
    def get_card_image_url(self, card_code):
        """카드 이미지 URL 생성"""
        # Deck of Cards API 형식으로 변환
        # 예: "AS" -> "AS", "10H" -> "0H"
        if card_code.startswith('10'):
            card_code = '0' + card_code[2]
        
        return f"https://deckofcardsapi.com/static/img/{card_code}.png"