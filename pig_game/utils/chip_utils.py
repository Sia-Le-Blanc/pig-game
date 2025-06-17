# utils/chip_utils.py
from config import Config

class ChipCalculator:
    def __init__(self):
        self.denominations = Config.CHIP_DENOMINATIONS
    
    def break_down_chips(self, total_amount):
        """칩 총액을 단위별로 분해"""
        breakdown = {}
        remaining = total_amount
        
        for denomination in self.denominations:
            count, remaining = divmod(remaining, denomination)
            breakdown[denomination] = count
        
        return breakdown
    
    def calculate_total(self, chip_breakdown):
        """칩 구성에서 총액 계산"""
        total = 0
        for denomination, count in chip_breakdown.items():
            total += denomination * count
        return total
    
    def get_chip_display_data(self, total_chips):
        """UI 표시용 칩 데이터 생성"""
        breakdown = self.break_down_chips(total_chips)
        
        display_data = []
        for denomination in self.denominations:
            count = breakdown.get(denomination, 0)
            
            display_data.append({
                'value': denomination,
                'count': count,
                'total_value': denomination * count,
                'formatted_value': self.format_chip_value(denomination),
                'color': self.get_chip_color(denomination),
                'image_path': self.get_chip_image_path(denomination)
            })
        
        return display_data
    
    def format_chip_value(self, value):
        """칩 값을 표시용으로 포맷팅"""
        if value >= 10000:
            return f"{value // 1000}K"
        elif value >= 1000:
            return f"{value // 1000}K"
        else:
            return str(value)
    
    def get_chip_color(self, denomination):
        """칩 단위별 색상 반환"""
        colors = {
            100: '#FF6B6B',      # 빨간색
            500: '#4ECDC4',      # 청록색
            1000: '#45B7D1',     # 파란색
            5000: '#96CEB4',     # 녹색
            10000: '#FFEAA7'     # 노란색
        }
        return colors.get(denomination, '#CCCCCC')
    
    def get_chip_image_path(self, denomination):
        """칩 이미지 경로 반환"""
        return f"/static/images/chips/chip_{denomination}.png"
    
    def suggest_bet_amounts(self, available_chips, target_amount=None):
        """추천 베팅 금액 목록 생성"""
        min_bet = Config.GAME_CONFIG['MIN_BET']
        max_bet = min(Config.GAME_CONFIG['MAX_BET'], available_chips)
        
        suggestions = []
        
        # 기본 추천 금액들
        base_amounts = [min_bet, 500, 1000, 5000, 10000, 25000, 50000]
        
        for amount in base_amounts:
            if min_bet <= amount <= max_bet:
                suggestions.append({
                    'amount': amount,
                    'formatted': f"{amount:,}",
                    'chips_needed': self.break_down_chips(amount)
                })
        
        # 타겟 금액이 있으면 추가
        if target_amount and min_bet <= target_amount <= max_bet:
            suggestions.append({
                'amount': target_amount,
                'formatted': f"{target_amount:,}",
                'chips_needed': self.break_down_chips(target_amount),
                'is_target': True
            })
        
        # 중복 제거 및 정렬
        unique_suggestions = {}
        for suggestion in suggestions:
            unique_suggestions[suggestion['amount']] = suggestion
        
        return sorted(unique_suggestions.values(), key=lambda x: x['amount'])
    
    def can_make_bet(self, available_chips, bet_amount):
        """해당 금액으로 베팅 가능한지 확인"""
        min_bet = Config.GAME_CONFIG['MIN_BET']
        max_bet = Config.GAME_CONFIG['MAX_BET']
        
        return (
            available_chips >= bet_amount and
            bet_amount >= min_bet and
            bet_amount <= max_bet
        )
    
    def get_optimal_chip_combination(self, target_amount, available_chips_breakdown):
        """목표 금액에 대한 최적 칩 조합 계산"""
        result = {}
        remaining = target_amount
        
        for denomination in self.denominations:
            available = available_chips_breakdown.get(denomination, 0)
            needed = min(remaining // denomination, available)
            
            if needed > 0:
                result[denomination] = needed
                remaining -= denomination * needed
        
        # 정확히 만들 수 있는지 확인
        can_make_exact = (remaining == 0)
        
        return {
            'chips_to_use': result,
            'can_make_exact': can_make_exact,
            'shortfall': remaining if remaining > 0 else 0
        }
    
    def format_amount(self, amount):
        """금액을 사용자 친화적으로 포맷팅"""
        if amount >= 1000000:
            return f"{amount / 1000000:.1f}M"
        elif amount >= 1000:
            return f"{amount / 1000:.0f}K"
        else:
            return f"{amount:,}"