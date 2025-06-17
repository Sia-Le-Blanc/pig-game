# utils/timer.py
from datetime import datetime, timedelta

class GameTimer:
    def __init__(self, timezone='Asia/Seoul'):
        """게임 타이머 초기화"""
        # 간단히 로컬 시간 사용
        pass
    
    def get_current_time(self):
        """현재 시간 반환 (로컬 시간 기준)"""
        return datetime.now()
    
    def get_server_time_string(self):
        """서버 시간을 문자열로 반환 (MM:SS 형식)"""
        now = self.get_current_time()
        return now.strftime("%M:%S")
    
    def get_full_time_string(self):
        """전체 시간 문자열 반환 (HH:MM:SS 형식)"""
        now = self.get_current_time()
        return now.strftime("%H:%M:%S")
    
    def calculate_remaining_time(self, start_time, duration_seconds):
        """남은 시간 계산"""
        if not start_time:
            return 0
        
        now = self.get_current_time()
        
        # start_time이 naive datetime인 경우 그대로 사용
        elapsed = (now - start_time).total_seconds()
        remaining = duration_seconds - elapsed
        
        return max(0, int(remaining))
    
    def format_time(self, seconds):
        """초를 MM:SS 형식으로 변환"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def is_time_expired(self, start_time, duration_seconds):
        """시간이 만료되었는지 확인"""
        remaining = self.calculate_remaining_time(start_time, duration_seconds)
        return remaining <= 0
    
    def get_next_round_time(self, seconds_delay=5):
        """다음 라운드 시작 시간 계산"""
        now = self.get_current_time()
        return now + timedelta(seconds=seconds_delay)
    
    def get_countdown_display(self, start_time, duration_seconds):
        """카운트다운 표시용 데이터 반환"""
        remaining = self.calculate_remaining_time(start_time, duration_seconds)
        
        return {
            'remaining_seconds': remaining,
            'formatted_time': self.format_time(remaining),
            'percentage': (remaining / duration_seconds * 100) if duration_seconds > 0 else 0,
            'is_expired': remaining <= 0,
            'is_warning': remaining <= 10  # 10초 이하일 때 경고
        }
    
    def get_game_session_info(self, session):
        """게임 세션의 시간 정보 반환"""
        if not session:
            return None
        
        return {
            'current_time': self.get_server_time_string(),
            'state': session.state,
            'countdown': self.get_countdown_display(
                session.state_started_at, 
                session.state_duration
            )
        }