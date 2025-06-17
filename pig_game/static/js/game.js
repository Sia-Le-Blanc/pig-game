// game.js - 바카라 게임 실시간 업데이트
class BaccaratGame {
    constructor() {
        this.gameData = null;
        this.updateInterval = null;
        this.myBets = {};
        this.isFirstLoad = true;
        
        this.init();
    }
    
    init() {
        console.log('🎮 바카라 게임 초기화');
        
        // 이벤트 리스너 등록
        this.setupEventListeners();
        
        // 실시간 업데이트 시작
        this.startRealTimeUpdates();
        
        // 초기 데이터 로드
        this.updateGameState();
    }
    
    setupEventListeners() {
        // 베팅 버튼 클릭
        document.querySelectorAll('.bet-buttons .btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleBetClick(e));
        });
        
        // 빠른 금액 선택
        document.querySelectorAll('.quick-bet').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const amount = e.target.dataset.amount;
                document.getElementById('bet-amount').value = amount;
            });
        });
        
        // 베팅 금액 입력 검증
        const betAmountInput = document.getElementById('bet-amount');
        betAmountInput.addEventListener('input', () => this.validateBetAmount());
        betAmountInput.addEventListener('change', () => this.validateBetAmount());
    }
    
    startRealTimeUpdates() {
        // 1초마다 게임 상태 업데이트
        this.updateInterval = setInterval(() => {
            this.updateGameState();
        }, 1000);
        
        console.log('⏰ 실시간 업데이트 시작');
    }
    
    async updateGameState() {
        try {
            const response = await fetch('/api/game/state');
            const data = await response.json();
            
            if (data.success) {
                this.gameData = data;
                this.updateUI(data);
                
                if (this.isFirstLoad) {
                    this.showNotification('🎮 게임에 연결되었습니다!', 'success');
                    this.isFirstLoad = false;
                }
            } else {
                console.error('게임 상태 조회 실패:', data.error);
            }
        } catch (error) {
            console.error('API 호출 오류:', error);
            this.showNotification('⚠️ 서버 연결 오류', 'error');
        }
    }
    
    updateUI(data) {
        this.updateUserChips(data.user_chips);
        this.updateGameInfo(data.game_state, data.timer_info);
        this.updateCards(data.game_state);
        this.updateScores(data.game_state);
        this.updateBettingTotals(data.game_state);
        this.updateActiveUsers(data.active_users);
        this.updateBettingButtons(data.game_state);
    }
    
    updateUserChips(chips) {
        const chipsElement = document.getElementById('user-chips');
        if (chipsElement) {
            chipsElement.textContent = this.formatNumber(chips || 0);
        }
    }
    
    updateGameInfo(gameState, timerInfo) {
        // 타이머 업데이트
        if (timerInfo && timerInfo.countdown) {
            const timerDisplay = document.getElementById('timer-display');
            const timerProgress = document.getElementById('timer-progress');
            
            if (timerDisplay) {
                timerDisplay.textContent = timerInfo.countdown.formatted_time;
            }
            
            if (timerProgress) {
                const percentage = timerInfo.countdown.percentage || 0;
                timerProgress.style.width = percentage + '%';
                
                // 시간이 얼마 안 남으면 빨간색으로
                if (timerInfo.countdown.is_warning) {
                    timerProgress.style.backgroundColor = '#e74c3c';
                } else {
                    timerProgress.style.backgroundColor = '#3498db';
                }
            }
        }
        
        // 게임 상태 텍스트
        const stateText = document.getElementById('game-state-text');
        const roundNumber = document.getElementById('round-number');
        
        if (gameState && stateText) {
            const stateMessages = {
                'waiting': '🔄 다음 라운드 대기중',
                'first_deal': '🃏 첫 번째 카드 분배',
                'betting': '💰 베팅 타임!',
                'second_deal': '🃏 두 번째 카드 분배',
                'result': '🎯 결과 발표',
                'finished': '✅ 라운드 종료'
            };
            
            stateText.textContent = stateMessages[gameState.state] || '게임 진행중';
        }
        
        if (gameState && roundNumber) {
            roundNumber.textContent = `라운드 #${gameState.round_number || 1}`;
        }
    }
    
    updateCards(gameState) {
        if (!gameState) return;
        
        // 플레이어 카드
        const playerCardsContainer = document.getElementById('player-cards');
        if (playerCardsContainer && gameState.player_cards_display) {
            this.renderCards(playerCardsContainer, gameState.player_cards_display);
        }
        
        // 뱅커 카드
        const bankerCardsContainer = document.getElementById('banker-cards');
        if (bankerCardsContainer && gameState.banker_cards_display) {
            this.renderCards(bankerCardsContainer, gameState.banker_cards_display);
        }
    }
    
    renderCards(container, cards) {
        container.innerHTML = '';
        
        if (cards.length === 0) {
            // 카드가 없으면 플레이스홀더 표시
            container.innerHTML = '<div class="card-placeholder">?</div><div class="card-placeholder">?</div>';
            return;
        }
        
        cards.forEach(card => {
            const cardElement = document.createElement('img');
            cardElement.src = card.image_url;
            cardElement.alt = card.name;
            cardElement.className = 'card';
            cardElement.style.width = '80px';
            cardElement.style.margin = '5px';
            
            container.appendChild(cardElement);
        });
        
        // 카드가 1장만 있으면 두 번째 카드용 플레이스홀더 추가
        if (cards.length === 1) {
            const placeholder = document.createElement('div');
            placeholder.className = 'card-placeholder';
            placeholder.textContent = '?';
            container.appendChild(placeholder);
        }
    }
    
    updateScores(gameState) {
        if (!gameState) return;
        
        const playerScoreElement = document.getElementById('player-score');
        const bankerScoreElement = document.getElementById('banker-score');
        const gameResultElement = document.getElementById('game-result');
        
        if (playerScoreElement) {
            playerScoreElement.textContent = gameState.player_score !== null ? gameState.player_score : '-';
        }
        
        if (bankerScoreElement) {
            bankerScoreElement.textContent = gameState.banker_score !== null ? gameState.banker_score : '-';
        }
        
        if (gameResultElement && gameState.winner) {
            const resultMessages = {
                'player': '🏆 Player 승!',
                'banker': '🏆 Banker 승!',
                'tie': '🤝 무승부!'
            };
            
            gameResultElement.textContent = resultMessages[gameState.winner] || '🎯 게임 진행중';
            gameResultElement.className = `result-text ${gameState.winner}`;
        } else if (gameResultElement) {
            gameResultElement.textContent = '🎯 게임 진행중';
            gameResultElement.className = 'result-text';
        }
    }
    
    updateBettingTotals(gameState) {
        if (!gameState || !gameState.total_bets) return;
        
        const elements = {
            'banker-total': gameState.total_bets.banker,
            'player-total': gameState.total_bets.player,
            'tie-total': gameState.total_bets.tie
        };
        
        Object.entries(elements).forEach(([id, amount]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = this.formatNumber(amount || 0);
            }
        });
    }
    
    updateActiveUsers(users) {
        if (!users) return;
        
        // 모든 유저 슬롯 초기화
        for (let i = 0; i < 4; i++) {
            const slot = document.getElementById(`user-slot-${i}`);
            if (slot) {
                if (i < users.length) {
                    const user = users[i];
                    slot.innerHTML = `
                        <div class="username">${user.username}</div>
                        <div class="chips">💰 ${this.formatNumber(user.chips)}</div>
                        <div class="status">${user.is_current_user ? '(나)' : '게임중'}</div>
                    `;
                    slot.className = 'user-box active';
                } else {
                    slot.innerHTML = `
                        <div class="username">-</div>
                        <div class="chips">💰 0</div>
                        <div class="status">대기중</div>
                    `;
                    slot.className = 'user-box';
                }
            }
        }
    }
    
    updateBettingButtons(gameState) {
        const buttons = document.querySelectorAll('.bet-buttons .btn');
        const isBettingTime = gameState && gameState.state === 'betting';
        
        buttons.forEach(btn => {
            btn.disabled = !isBettingTime;
            
            if (isBettingTime) {
                btn.classList.add('enabled');
            } else {
                btn.classList.remove('enabled');
            }
        });
    }
    
    async handleBetClick(event) {
        const button = event.currentTarget;
        const betTarget = button.dataset.target;
        const betAmountInput = document.getElementById('bet-amount');
        const betAmount = parseInt(betAmountInput.value);
        
        // 베팅 검증
        if (!this.validateBet(betTarget, betAmount)) {
            return;
        }
        
        // 중복 베팅 확인
        if (this.myBets[betTarget]) {
            this.showNotification('⚠️ 이미 해당 항목에 베팅하셨습니다.', 'warning');
            return;
        }
        
        try {
            button.disabled = true;
            button.textContent = '처리중...';
            
            const response = await fetch('/api/bet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    bet_target: betTarget,
                    bet_amount: betAmount
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.myBets[betTarget] = betAmount;
                this.updateMyBets();
                this.showNotification(`✅ ${betAmount.toLocaleString()} 칩 베팅 완료!`, 'success');
                
                // 사용자 칩 업데이트
                this.updateUserChips(data.remaining_chips);
            } else {
                this.showNotification(`❌ ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('베팅 오류:', error);
            this.showNotification('❌ 베팅 처리 중 오류가 발생했습니다.', 'error');
        } finally {
            // 버튼 상태 복원은 다음 게임 상태 업데이트에서 처리
            setTimeout(() => {
                this.updateBettingButtons(this.gameData?.game_state);
            }, 1000);
        }
    }
    
    validateBet(betTarget, betAmount) {
        const userChips = this.gameData?.user_chips || 0;
        
        if (betAmount < 100) {
            this.showNotification('❌ 최소 베팅 금액은 100칩입니다.', 'error');
            return false;
        }
        
        if (betAmount > 50000) {
            this.showNotification('❌ 최대 베팅 금액은 50,000칩입니다.', 'error');
            return false;
        }
        
        if (betAmount > userChips) {
            this.showNotification('❌ 보유 칩이 부족합니다.', 'error');
            return false;
        }
        
        return true;
    }
    
    validateBetAmount() {
        const input = document.getElementById('bet-amount');
        const value = parseInt(input.value);
        const userChips = this.gameData?.user_chips || 0;
        
        if (value < 100) {
            input.value = 100;
        } else if (value > Math.min(50000, userChips)) {
            input.value = Math.min(50000, userChips);
        }
    }
    
    updateMyBets() {
        const myBetsContainer = document.getElementById('my-bets');
        const myBetsList = document.getElementById('my-bets-list');
        const myTotalBet = document.getElementById('my-total-bet');
        
        if (Object.keys(this.myBets).length === 0) {
            myBetsContainer.style.display = 'none';
            return;
        }
        
        myBetsContainer.style.display = 'block';
        
        const betLabels = {
            'banker': 'BANKER',
            'player': 'PLAYER',
            'tie': 'TIE',
            'banker_pair': 'B.PAIR',
            'player_pair': 'P.PAIR'
        };
        
        let html = '';
        let total = 0;
        
        Object.entries(this.myBets).forEach(([target, amount]) => {
            html += `<div class="my-bet-item">${betLabels[target]}: ${this.formatNumber(amount)}칩</div>`;
            total += amount;
        });
        
        myBetsList.innerHTML = html;
        myTotalBet.textContent = this.formatNumber(total);
    }
    
    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        if (!notification) return;
        
        notification.textContent = message;
        notification.className = `notification ${type} show`;
        
        // 3초 후 자동 숨김
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    
    formatNumber(num) {
        return new Intl.NumberFormat('ko-KR').format(num);
    }
}

// 페이지 로드 시 게임 시작
document.addEventListener('DOMContentLoaded', () => {
    window.baccaratGame = new BaccaratGame();
});