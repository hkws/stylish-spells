let state = null;
let waitGauge = 0;
const WAIT_GAUGE_MAX = 100;
const WAIT_GAUGE_INCREMENT = 1;

class GameState {
    constructor() {
        this.enemy = null;
        this.player = null;
        this.field = null;
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
        this.field = data.field;
        this.id = data.id;
        this.in_battle = data.in_battle;
    }
    victory() {
        return this.enemy.hp <= 0;
    }
}

function startGame() {
    let username = document.getElementById('username').value;
    let elements = document.getElementsByName('enemy');
    let enemy = '';

    for (let i = 0; i < elements.length; i++){
        if (elements.item(i).checked){
            enemy = elements.item(i).value;
        }
    }
    fetch('/start_game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ "username": username, "enemy": enemy})
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
        document.getElementById('battle-field').style.background = `url(/static/images/fields/${state.field.image}) center/cover`;
        document.getElementById('enemy-image').src = `/static/images/enemies/${state.enemy.image}`;
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
            showSpellEffect(deal.spell.attribute, deal.spell.cost);
            if (deal.result_msg) {
                displayMessage(deal.result_msg);
            }
            displayMessage(deal.enemy_msg);
            displayMessage(deal.field_msg);
            updateUI();
            if (!state.in_battle) {
                endGame(state.victory());
            }
        });
    document.getElementById('spell-input').value = '';
}

function showSpellEffect(attribute, cost) {
    imgsrc = `/static/images/effects/${attribute}_${cost}.png`;
    const effect = document.getElementById('spell-effect');
    effect.style.backgroundImage = `url(${imgsrc})`;
    effect.style.opacity = '1';
    setTimeout(() => {
        effect.style.opacity = '0';
    }, 1000);
}

function updateUI() {
    const playerHPBar = document.getElementById('player-hp-bar');
    playerHPBar.style.width = `${(state.player.hp / 100) * 100}%`;
    const playerHPText = document.getElementById('player-hp-text');
    playerHPText.textContent = `${state.player.hp}/${state.player.max_hp}`;

    const playerMPBar = document.getElementById('player-mp-bar');
    playerMPBar.style.width = `${(state.player.mp / 100) * 100}%`;
    const playerMPText = document.getElementById('player-mp-text');
    playerMPText.textContent = `${state.player.mp}/${state.player.max_mp}`;

    const enemyHPBar = document.getElementById('enemy-hp-bar');
    enemyHPBar.style.width = `${(state.enemy.hp / state.enemy.max_hp) * 100}%`;
    const enemyHPText = document.getElementById('enemy-hp-text');
    enemyHPText.textContent = `${state.enemy.hp} / ${state.enemy.max_hp}`;

    const waitBar = document.getElementById('enemy-wait-bar');
    waitBar.style.width = `${(waitGauge / WAIT_GAUGE_MAX) * 100}%`;
}

function displayMessage(message) {
    if (message.length == 0) {
        return;
    }
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
        displayMessage("あなたは倒れた...");
    }
    setTimeout(() => {
        window.location.href = `/result/${state.id}`;
    }, 1000);
}

function goBack() {
    window.location.href = '/';
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', async () => {
    if (window.location.pathname === '/battle') {
        await initBattleScreen();
        document.getElementById('cast-button').addEventListener('click', castSpell);
    }
});