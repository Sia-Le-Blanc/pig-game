# utils/deck.py
import random

def create_deck():
    """표준 52장 카드 덱 생성"""
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    suits = ['S', 'H', 'D', 'C']  # Spades, Hearts, Diamonds, Clubs
    return [rank + suit for rank in ranks for suit in suits]

def shuffle_deck(deck):
    """덱 셔플"""
    deck_copy = deck.copy()
    random.shuffle(deck_copy)
    return deck_copy

def get_card_rank(card_code):
    """카드 코드에서 랭크 추출"""
    if card_code.startswith('10'):
        return '10'
    return card_code[0]

def get_card_suit(card_code):
    """카드 코드에서 슈트 추출"""
    if card_code.startswith('10'):
        return card_code[2]
    return card_code[1]

def get_card_value(card_code):
    """바카라 규칙에 따른 카드 값 계산"""
    rank = get_card_rank(card_code)
    
    if rank == 'A':
        return 1
    elif rank in ['J', 'Q', 'K']:
        return 0
    elif rank == '10':
        return 0
    else:
        return int(rank)

def get_card_display_name(card_code):
    """카드의 표시용 이름 반환"""
    rank = get_card_rank(card_code)
    suit = get_card_suit(card_code)
    
    rank_names = {
        'A': 'Ace',
        'J': 'Jack',
        'Q': 'Queen',
        'K': 'King'
    }
    
    suit_names = {
        'S': 'Spades',
        'H': 'Hearts',
        'D': 'Diamonds',
        'C': 'Clubs'
    }
    
    rank_display = rank_names.get(rank, rank)
    suit_display = suit_names.get(suit, suit)
    
    return f"{rank_display} of {suit_display}"

def get_card_image_url(card_code):
    """카드 이미지 URL 생성 (Deck of Cards API 형식)"""
    # 10을 0으로 변환 (API 형식에 맞춤)
    if card_code.startswith('10'):
        api_code = '0' + card_code[2]
    else:
        api_code = card_code
    
    return f"https://deckofcardsapi.com/static/img/{api_code}.png"

def get_card_back_url():
    """카드 뒷면 이미지 URL"""
    return "https://deckofcardsapi.com/static/img/back.png"

def is_red_card(card_code):
    """빨간색 카드인지 확인"""
    suit = get_card_suit(card_code)
    return suit in ['H', 'D']

def is_black_card(card_code):
    """검은색 카드인지 확인"""
    suit = get_card_suit(card_code)
    return suit in ['S', 'C']

def format_cards_for_display(cards):
    """카드 리스트를 표시용으로 포맷팅"""
    return [
        {
            'code': card,
            'rank': get_card_rank(card),
            'suit': get_card_suit(card),
            'value': get_card_value(card),
            'name': get_card_display_name(card),
            'image_url': get_card_image_url(card),
            'is_red': is_red_card(card)
        }
        for card in cards
    ]