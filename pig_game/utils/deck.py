import random

# 덱 생성
def create_deck():
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    suits = ['S', 'H', 'D', 'C']
    return [r + s for r in ranks for s in suits]


# 덱 셔플
def shuffle_deck(deck):
    random.shuffle(deck)
    return deck

# 개별 카드 점수 계산
def get_card_score(card_code):
    rank = card_code[0] # 카드 코드의 첫 글자가 랭크
    if rank == 'A':
        return 1
    elif rank in ['0', 'J', 'Q', 'K']:
        return 0
    else:
        return int(rank)
    
# 덱에서 카드 점수 계산
def calc_score(card1, card2):
    return (get_card_score(card1) + get_card_score(card2)) % 10