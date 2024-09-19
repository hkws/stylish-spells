let state = null;
let waitGauge = 0;
const WAIT_GAUGE_MAX = 100;
const WAIT_GAUGE_INCREMENT = 1;

class GameState {
    constructor() {
        this.enemy = null;
        this.player = null;
        this.id = null;
        this.in_battle = false;
    }
    save(battle_id) {
        localStorage.setItem('battle_id', battle_id);
    }
    async load() {
        const battle_id = localStorage.getItem('battle_id');
        const res = await fetch(`/battle/${battle_id}`, {
            method: 'GET'
        });
        const data = await res.json();
        this.store(data);
    }
    store(data) {
        this.enemy = data.enemy;
        this.player = data.player;
        this.id = data.id;
        this.in_battle = data.in_battle;
    }
    victory() {
        return this.enemy.hp <= 0;
    }
}

function startGame(level) {
    fetch('/start_game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "level": level })
    })
        .then(response => response.json())
        .then(data => {
            state = new GameState();
            state.save(data.id);
            window.location.href = '/battle';
        });
}

async function initBattleScreen() {
    state = new GameState();
    await state.load();
    console.log(state);
    if (state.in_battle) {
        document.getElementById('enemy-image').src = `/static/images/${state.enemy.image}`;
        document.getElementById('enemy-name').textContent = state.enemy.name;
        updateUI();
        startWaitGauge();
    } else {
        window.location.href = `/result/${state.id}`;
    }
}

function castSpell() {
    const spell = document.getElementById('spell-input').value;
    displayMessage(`${spell}を唱えた！`);
    fetch('/cast_spell', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "spell": spell, "battle_id": state.id })
    })
        .then(response => response.json())
        .then(data => {
            state.store(data.state);
            const deal = data.deal;
            displayMessage(`MP: ${deal.mp} を消費して、${deal.damage} ダメージを与えた！`);
            displayMessage(deal.enemy_msg);
            if (deal.result_msg) {
                displayMessage(deal.result_msg);
            }
            updateUI();
            if (!state.in_battle) {
                endGame(state.victory());
            }
        });
    document.getElementById('spell-input').value = '';
}

function updateUI() {
    const enemyHPBar = document.getElementById('enemy-hp-bar');
    enemyHPBar.style.width = `${(state.enemy.hp / state.enemy.max_hp) * 100}%`;
    enemyHPBar.textContent = `${state.enemy.hp} / ${state.enemy.max_hp}`;

    const playerHPBar = document.getElementById('player-hp-bar');
    playerHPBar.style.width = `${(state.player.hp / 100) * 100}%`;
    playerHPBar.textContent = `${state.player.hp} / 100`;

    const waitBar = document.getElementById('enemy-wait-bar');
    waitBar.style.width = `${(waitGauge / WAIT_GAUGE_MAX) * 100}%`;
}

function displayMessage(message) {
    const messageWindow = document.getElementById('message-window');
    messageWindow.innerText += `\n${message}`;
    messageWindow.scrollTop = messageWindow.scrollHeight - messageWindow.clientHeight;
}

function startWaitGauge() {
    setInterval(() => {
        waitGauge += WAIT_GAUGE_INCREMENT;
        if (waitGauge >= WAIT_GAUGE_MAX) {
            enemyAttack();
            waitGauge = 0;
        }
        updateUI();
    }, 100);
}

function enemyAttack() {
    displayMessage(`${state.enemy.name}の攻撃！`);
    fetch('/enemy_attack', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "battle_id": state.id })
    })
        .then(response => response.json())
        .then(data => {
            state.store(data.state);
            const deal = data.deal;
            displayMessage(`${deal.damage}のダメージを食らった！`);
            displayMessage(deal.enemy_msg);
            if (deal.result_msg) {
                displayMessage(deal.result_msg);
            }
            updateUI();
            if (!state.in_battle) {
                endGame(state.victory());
            }
        });
}

function endGame(playerWon) {
    if (playerWon) {
        displayMessage("敵を倒した！勝利だ！");
    } else {
        displayMessage("あなたは倒れた...ゲームオーバー");
    }
    setTimeout(() => {
        window.location.href = `/result/${state.id}`;
    }, 1000);
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', async () => {
    if (window.location.pathname === '/battle') {
        await initBattleScreen();
        document.getElementById('cast-button').addEventListener('click', castSpell);
    }
});