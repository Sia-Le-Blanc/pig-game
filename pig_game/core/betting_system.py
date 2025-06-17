# core/betting_system.py
from config import Config

class BettingSystem:
    def __init__(self):
        self.payout_rates = Config.PAYOUT_RATES
    
    def evaluate_bet(self, bet_target, game_result, bet_amount):
        """베팅 결과 평가"""
        is_win = False
        payout = 0
        
        if bet_target == 'player':
            is_win = game_result['winner'] == 'player'
        elif bet_target == 'banker':
            is_win = game_result['winner'] == 'banker'
        elif bet_target == 'tie':
            is_win = game_result['winner'] == 'tie'
        elif bet_target == 'player_pair':
            is_win = game_result['has_player_pair']
        elif bet_target == 'banker_pair':
            is_win = game_result['has_banker_pair']
        
        if is_win:
            payout = int(bet_amount * self.payout_rates[bet_target])
        
        return is_win, payout
    
    def calculate_house_edge(self, bet_target):
        """하우스 엣지 계산"""
        house_edges = {
            'player': 1.24,
            'banker': 1.06,
            'tie': 14.44,
            'player_pair': 10.36,
            'banker_pair': 10.36
        }
        return house_edges.get(bet_target, 0)
    
    def get_bet_limits(self):
        """베팅 한도 반환"""
        return {
            'min_bet': Config.GAME_CONFIG['MIN_BET'],
            'max_bet': Config.GAME_CONFIG['MAX_BET']
        }
    
    def validate_bet(self, bet_target, amount, user_chips):
        """베팅 유효성 검사"""
        errors = []
        
        # 베팅 대상 확인
        valid_targets = ['player', 'banker', 'tie', 'player_pair', 'banker_pair']
        if bet_target not in valid_targets:
            errors.append("유효하지 않은 베팅 대상입니다.")
        
        # 최소/최대 베팅 금액 확인
        min_bet = Config.GAME_CONFIG['MIN_BET']
        max_bet = Config.GAME_CONFIG['MAX_BET']
        
        if amount < min_bet:
            errors.append(f"최소 베팅 금액은 {min_bet:,}칩입니다.")
        
        if amount > max_bet:
            errors.append(f"최대 베팅 금액은 {max_bet:,}칩입니다.")
        
        # 보유 칩 확인
        if amount > user_chips:
            errors.append("보유 칩이 부족합니다.")
        
        return len(errors) == 0, errors
    
    def get_payout_info(self):
        """배당률 정보 반환"""
        return {
            target: {
                'rate': rate,
                'description': self._get_bet_description(target)
            }
            for target, rate in self.payout_rates.items()
        }
    
    def _get_bet_description(self, bet_target):
        """베팅 대상 설명"""
        descriptions = {
            'player': 'Player가 이기면 배당',
            'banker': 'Banker가 이기면 배당 (수수료 5% 차감)',
            'tie': 'Player와 Banker가 동점이면 배당',
            'player_pair': 'Player의 첫 두 카드가 같은 숫자이면 배당',
            'banker_pair': 'Banker의 첫 두 카드가 같은 숫자이면 배당'
        }
        return descriptions.get(bet_target, '')
    
    def format_odds(self, bet_target):
        """배당률을 사용자 친화적 형식으로 변환"""
        rate = self.payout_rates[bet_target]
        
        if rate == 1.0:
            return "1:1"
        elif rate == 0.95:
            return "19:20 (수수료 5%)"
        elif rate == 8.0:
            return "8:1"
        elif rate == 11.0:
            return "11:1"
        else:
            return f"{rate}:1"