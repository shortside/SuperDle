/*
  Superdle - Dutch Supermarket Price Guessing Game
  Guess the price of products from Dutch supermarkets!
*/

// Product info variables
let productName;
let productPrice;
let productImage;
let allProducts = [];

// Timeout IDs
let shakeTimeout;
let toastTimeout;
let warningTimeout;

// Game configuration
const GAME_NAME = "Superdle";
const WIN_THRESHOLD = 5;
const NEAR_THRESHOLD = 25;
const MAX_GUESSES = 6;

// DOM Elements
const infoButton = document.getElementById("info-button");
infoButton.addEventListener("click", switchState);

const statButton = document.getElementById("stat-button");
statButton.addEventListener("click", switchState);

const newGameButton = document.getElementById("new-game-button");
newGameButton.addEventListener("click", startNewGame);

// User stats object
const userStats = JSON.parse(localStorage.getItem("superdle-stats")) || {
  numGames: 0,
  numWins: 0,
  winsInNum: [0, 0, 0, 0, 0, 0],
  currentStreak: 0,
  maxStreak: 0,
};

// Game state
let gameState = { guesses: [], hasWon: false };

// Start the game
loadProducts();

function loadProducts() {
  fetch("./games.json")
    .then((response) => response.json())
    .then((json) => {
      if (Array.isArray(json)) {
        json.forEach(cat => {
          if (Array.isArray(cat.products)) allProducts = allProducts.concat(cat.products);
        });
      } else if (typeof json === 'object') {
        Object.values(json).forEach(item => {
          if (item.name && item.price && item.image) allProducts.push(item);
        });
      }
      if (allProducts.length === 0) allProducts = Object.values(json);
      selectRandomProduct();
      initializeGame();
    })
    .catch((error) => console.error("Error loading products:", error));
}

function selectRandomProduct() {
  const idx = Math.floor(Math.random() * allProducts.length);
  const p = allProducts[idx];
  productName = p.name;
  productPrice = Number(p.price.replace(/[^\d.,]/g, '').replace(',', '.'));
  productImage = p.image;
}

function startNewGame() {
  if (gameState.guesses.length > 0 && !gameState.hasWon) {
    userStats.currentStreak = 0;
    localStorage.setItem("superdle-stats", JSON.stringify(userStats));
  }
  gameState = { guesses: [], hasWon: false };
  selectRandomProduct();
  clearGameUI();
  initializeGame();
}

function clearGameUI() {
  const imageContainer = document.getElementById("image-container");
  imageContainer.innerHTML = '<div class="image-badge">🛒 Today\'s Product</div>';
  
  for (let i = 1; i <= 6; i++) {
    const c = document.getElementById(i.toString());
    c.innerHTML = '';
    c.classList.remove('transparent-background', 'animate__flipOutX');
  }
  
  document.getElementById("input-container").innerHTML = `
    <div id="text-input-container">
      <div id="input-label">€</div>
      <input id="guess-input" type="text" data-type="currency" placeholder="Guess the price..."/>
    </div>
    <div id="button-container">
      <button id="guess-button" class="active">GO</button>
    </div>
  `;
  document.getElementById("game-stats").innerHTML = '';
}

function initializeGame() {
  if (gameState.guesses.length === 0) {
    userStats.numGames++;
    localStorage.setItem("superdle-stats", JSON.stringify(userStats));
  }
  displayProductCard();
  updateGameBoard();
  if (gameState.guesses.length < MAX_GUESSES && !gameState.hasWon) {
    addEventListeners();
  } else {
    convertToShareButton();
  }
}

function convertToShareButton() {
  const c = document.getElementById("input-container");
  c.innerHTML = `<button id="share-button">Share Results
    <svg class="share-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
      <polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/>
    </svg></button>`;
  document.getElementById("share-button").addEventListener("click", copyStats);
}

function displayProductCard() {
  const imageContainer = document.getElementById("image-container");
  if (!imageContainer.querySelector('.image-badge')) {
    imageContainer.innerHTML = '<div class="image-badge">🛒 Today\'s Product</div>' + imageContainer.innerHTML;
  }
  
  const img = document.createElement("img");
  img.src = productImage;
  img.id = "product-image";
  img.alt = productName;
  img.onerror = function() {
    this.style.display = 'none';
    const ph = document.createElement('div');
    ph.style.cssText = 'font-size:4rem;display:flex;align-items:center;justify-content:center;';
    ph.textContent = '🛒';
    imageContainer.appendChild(ph);
  };
  imageContainer.appendChild(img);
  document.getElementById("product-info").innerHTML = productName;
}

function updateGameBoard() {
  updateGuessStat();
  gameState.guesses.forEach((g, i) => displayGuess(g, i + 1));
}

function updateGuessStat() {
  const s = document.getElementById("game-stats");
  if (gameState.hasWon) {
    s.innerHTML = `<center><span style="font-size:1.25rem;">🎉 Gefeliciteerd!</span>
      <span>The price was <strong style="color:var(--dutch-orange);">€${productPrice.toFixed(2)}</strong></span></center>`;
  } else if (gameState.guesses.length === MAX_GUESSES) {
    s.innerHTML = `<center><span style="font-size:1.1rem;">Better luck next time!</span>
      <span>The price was <strong style="color:var(--dutch-red);">€${productPrice.toFixed(2)}</strong></span></center>`;
  } else {
    s.innerHTML = `<span>Guess ${gameState.guesses.length + 1} of ${MAX_GUESSES}</span>`;
  }
}

function inputEventListener(e) { if (e.key === "Enter") handleInput(); }
function buttonEventListener() { handleInput(); }

function handleInput() {
  const input = document.getElementById("guess-input");
  const val = input.value.replaceAll(",", "").replaceAll(" ", "");
  const guess = Number(val).toFixed(2);
  if (isNaN(guess) || !val || Number(val) <= 0) {
    showWarning();
    return;
  }
  checkGuess(guess);
  input.value = "";
}

function showWarning() {
  clearTimeout(warningTimeout);
  const w = document.getElementById("warning-toast");
  w.classList.remove("hide");
  w.classList.add("animate__flipInX");
  warningTimeout = setTimeout(() => {
    w.classList.remove("animate__flipInX");
    w.classList.add("animate__flipOutX");
    setTimeout(() => { w.classList.remove("animate__flipOutX"); w.classList.add("hide"); }, 500);
  }, 2000);
}

function copyStats() {
  let out = `🛒 ${GAME_NAME} ${gameState.hasWon ? gameState.guesses.length : 'X'}/${MAX_GUESSES}\n\n`;
  gameState.guesses.forEach((g) => {
    out += g.direction === "↑" ? "⬆️" : g.direction === "↓" ? "⬇️" : "✅";
    out += g.closeness === "guess-far" ? "🟥" : g.closeness === "guess-near" ? "🟨" : "🟩";
    out += "\n";
  });
  out += "\n🇳🇱 Dutch supermarket price game!";
  
  if (navigator.share && /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
    navigator.share({ title: GAME_NAME, text: out }).catch(() => {});
  } else {
    navigator.clipboard.writeText(out);
    showToast();
  }
}

function showToast() {
  clearTimeout(toastTimeout);
  const t = document.getElementById("share-toast");
  t.classList.remove("hide");
  t.classList.add("animate__flipInX");
  toastTimeout = setTimeout(() => {
    t.classList.remove("animate__flipInX");
    t.classList.add("animate__flipOutX");
    setTimeout(() => { t.classList.remove("animate__flipOutX"); t.classList.add("hide"); }, 500);
  }, 3000);
}

function addEventListeners() {
  const input = document.getElementById("guess-input");
  const btn = document.getElementById("guess-button");
  input.addEventListener("keydown", inputEventListener);
  btn.addEventListener("click", buttonEventListener);
  input.addEventListener("focus", () => input.placeholder = "0.00");
  input.addEventListener("blur", () => input.placeholder = "Guess the price...");
}

function removeEventListeners() {
  const input = document.getElementById("guess-input");
  const btn = document.getElementById("guess-button");
  if (btn) { btn.disabled = true; btn.classList.remove("active"); }
  if (input) { input.disabled = true; input.placeholder = "Game Over!"; }
}

function checkGuess(guess) {
  const obj = { guess, closeness: "", direction: "" };
  const pct = ((guess * 100) / (productPrice * 100)) * 100 - 100;
  
  if (Math.abs(pct) <= WIN_THRESHOLD) {
    obj.closeness = "guess-win";
    gameState.hasWon = true;
  } else {
    shakeBox();
    obj.closeness = Math.abs(pct) <= NEAR_THRESHOLD ? "guess-near" : "guess-far";
  }
  obj.direction = gameState.hasWon ? "✓" : pct < 0 ? "↑" : "↓";
  
  gameState.guesses.push(obj);
  displayGuess(obj);
  
  if (gameState.hasWon) gameWon();
  else if (gameState.guesses.length === MAX_GUESSES) gameLost();
}

function displayGuess(guess, index = gameState.guesses.length) {
  const c = document.getElementById(index.toString());
  const v = document.createElement("div");
  const d = document.createElement("div");
  v.className = "guess-value-container animate__flipInX";
  d.className = "guess-direction-container animate__flipInX " + guess.closeness;
  v.innerHTML = `€${guess.guess}`;
  d.innerHTML = guess.direction;
  c.classList.add("animate__flipOutX");
  setTimeout(() => { c.classList.add("transparent-background"); c.appendChild(v); c.appendChild(d); }, 300);
  updateGuessStat();
}

function gameWon() {
  userStats.numWins++;
  userStats.currentStreak++;
  userStats.winsInNum[gameState.guesses.length - 1]++;
  if (userStats.currentStreak > userStats.maxStreak) userStats.maxStreak = userStats.currentStreak;
  localStorage.setItem("superdle-stats", JSON.stringify(userStats));
  removeEventListeners();
  convertToShareButton();
}

function gameLost() {
  userStats.currentStreak = 0;
  localStorage.setItem("superdle-stats", JSON.stringify(userStats));
  removeEventListeners();
  convertToShareButton();
}

function switchState(event) {
  const overlayId = event.currentTarget.dataset.overlay;
  const overlay = document.getElementById(overlayId);
  const title = document.getElementById("title");
  
  title.classList.remove("info-title");
  
  if (overlay.style.display === "flex") {
    title.innerHTML = `<span class="dutch-orange">Super</span><span class="dutch-blue">dle</span>`;
    overlay.style.display = "none";
    return;
  }
  
  document.getElementById("info-overlay").style.display = "none";
  document.getElementById("stats-overlay").style.display = "none";
  
  if (overlayId === "info-overlay") {
    title.innerHTML = `<span class="dutch-orange">How to</span> <span class="dutch-blue">Play</span>`;
    title.classList.add("info-title");
  } else {
    title.innerHTML = `<span class="dutch-orange">Your</span> <span class="dutch-blue">Stats</span>`;
    document.getElementById("number-wins").innerHTML = userStats.numGames;
    document.getElementById("win-percent").innerHTML = userStats.numGames ? Math.round((userStats.numWins / userStats.numGames) * 100) : 0;
    document.getElementById("current-streak").innerHTML = userStats.currentStreak;
    document.getElementById("max-streak").innerHTML = userStats.maxStreak;
    const max = Math.max(...userStats.winsInNum, 1);
    userStats.winsInNum.forEach((v, i) => {
      const el = document.getElementById(`graph-${i + 1}`);
      el.style.width = `${(v / max) * 95 + 5}%`;
      el.innerHTML = v;
      el.parentElement.classList.toggle('highlight', gameState.hasWon && gameState.guesses.length === i + 1);
    });
  }
  overlay.style.display = "flex";
}

function shakeBox() {
  clearTimeout(shakeTimeout);
  const card = document.getElementById("info-card");
  card.classList.remove("animate__headShake");
  shakeTimeout = setTimeout(() => card.classList.add("animate__headShake"), 50);
}
