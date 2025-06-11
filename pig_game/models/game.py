from utils.deck import create_deck, shuffle_deck, calc_score

def play_game():
    deck = shuffle_deck(create_deck())

    # 카드를 2장씩 분배
    player_cards = [deck.pop(), deck.pop()]
    banker_cards = [deck.pop(), deck.pop()]

    # 점수 계산
    player_score = calc_score(*player_cards)
    banker_score = calc_score(*banker_cards)

    # 승자 판정
    if player_score > banker_score:
        winner = 'player'
    elif banker_score > player_score:
        winner = 'banker'
    else:
        winner = 'tie'


    return {
        "player": {
            "cards": player_cards,
            "score": player_score
        },
        "banker": {
            "cards": banker_cards,
            "score": banker_score
        },
        "winner": winner
    }