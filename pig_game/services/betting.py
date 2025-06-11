def evaluate_bet(bet_target: str, winner: str, amount: int):
    #배팅 대상과 실제 승자를 비교하여 결과 및 배당금 계산

    bet_win = (bet_target == winner)
    payout_rate = {
        "player" : 1.0,
        "banker": 0.95,
        "tie": 8.0
    }

    if bet_win:
        gain = int(amount * payout_rate[bet_target])
        return True, gain
    else:
        return False, amount