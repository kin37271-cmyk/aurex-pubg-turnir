// Telegram Web App init
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

let tournamentData = {};
let slotsData = [];

// TAB NAVIGATION
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    tab.classList.add('active');
    const targetId = tab.getAttribute('data-tab');
    document.getElementById(targetId)?.classList.add('active');

    if (tg?.HapticFeedback) {
      tg.HapticFeedback.selectionChanged();
    }
  });
});

// MODAL CONTROLS
const modal = document.getElementById('book-modal');
const modalCloseBtn = document.getElementById('modal-close-btn');

modalCloseBtn.addEventListener('click', () => {
  modal.style.display = 'none';
});

window.addEventListener('click', (e) => {
  if (e.target === modal) {
    modal.style.display = 'none';
  }
});

// LOAD TOURNAMENT DATA
async function loadTournament() {
  try {
    const res = await fetch('/api/tournament');
    if (!res.ok) return;
    tournamentData = await res.json();

    document.getElementById('tournament-title').innerText = tournamentData.title || 'Aurex PUBG Mobile Turniri';
    document.getElementById('stage-badge').innerText = tournamentData.stage_name || "Ro'yxatga olish";

    // Slot Narxi
    const price = tournamentData.slot_price || 0;
    const priceFormatted = price > 0 ? `${price.toLocaleString()} so'm` : "BEPUL / TEKIN";
    document.getElementById('slot-price-display').innerText = priceFormatted;
    document.getElementById('modal-slot-price').innerText = priceFormatted;

    // Room info
    if (tournamentData.room_id && tournamentData.room_password) {
      document.getElementById('room-status-title').innerText = "🔥 XONA OCHILGAN!";
      document.getElementById('room-status-desc').innerText = "PUBG Mobile ilovasida pastdagi ID va parol orqali xonaga kiring:";
      document.getElementById('room-id-val').innerText = tournamentData.room_id;
      document.getElementById('room-pass-val').innerText = tournamentData.room_password;
      document.getElementById('room-creds').style.display = 'grid';
    } else {
      document.getElementById('room-creds').style.display = 'none';
    }

    // Final bosqichida salyut animatsiyasini yoqish
    if (tournamentData.status === 'final') {
      startFireworks();
      if (tournamentData.winner_nick) {
        document.getElementById('banner-winner-nick').innerText = tournamentData.winner_nick;
        document.getElementById('fireworks-banner').style.display = 'flex';
      }
    }

  } catch (err) {
    console.error("Turnir ma'lumotlarini yuklashda xato:", err);
  }
}

// LOAD SLOTS
async function loadSlots() {
  try {
    const res = await fetch('/api/slots');
    if (!res.ok) return;
    slotsData = await res.json();

    const container = document.getElementById('slots-grid-container');
    container.innerHTML = '';

    let bookedCount = 0;

    slotsData.forEach(slot => {
      const isBooked = !!slot.user_id;
      if (isBooked) bookedCount++;

      const card = document.createElement('div');
      card.className = `slot-card ${isBooked ? 'booked' : 'free'}`;

      const numStr = String(slot.slot_number).padStart(2, '0');

      if (isBooked) {
        card.innerHTML = `
          <div class="slot-card-header">
            <span class="slot-badge-num">SLOT #${numStr}</span>
            <span class="slot-status-pill">🔴 BAND</span>
          </div>
          <div class="slot-player-info">
            <div class="slot-player-nick">👤 ${escapeHtml(slot.pubg_nick || 'O\'yinchi')}</div>
            <div class="slot-player-id">ID: ${escapeHtml(slot.pubg_id || '---')}</div>
          </div>
        `;
      } else {
        card.innerHTML = `
          <div class="slot-card-header">
            <span class="slot-badge-num">SLOT #${numStr}</span>
            <span class="slot-status-pill">🟢 BO'SH</span>
          </div>
          <div class="slot-player-info">
            <div class="slot-player-nick" style="color: #8b949e;">O'rin bo'sh</div>
            <button class="slot-book-btn" onclick="openBookModal(${slot.slot_number})">BAND QILISH</button>
          </div>
        `;
      }

      container.appendChild(card);
    });

    // Update Counter & Progress
    document.getElementById('slots-count-display').innerText = `${bookedCount} / 16`;
    const percentage = Math.round((bookedCount / 16) * 100);
    document.getElementById('slots-progress').style.width = `${percentage}%`;

  } catch (err) {
    console.error("Slotlarni yuklashda xato:", err);
  }
}

// OPEN BOOK MODAL
window.openBookModal = function(slotNumber) {
  if (tournamentData.status !== 'registration' && tournamentData.status !== 'open') {
    alert("Turnirga ro'yxatga olish yopiq!");
    return;
  }

  document.getElementById('modal-slot-title').innerText = `SLOT #${String(slotNumber).padStart(2, '0')} BAND QILISH`;
  document.getElementById('modal-slot-num').value = slotNumber;
  document.getElementById('input-pubg-nick').value = '';
  document.getElementById('input-pubg-id').value = '';
  document.getElementById('input-phone').value = '';

  modal.style.display = 'flex';
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('medium');
  }
};

// FORM SUBMISSION
document.getElementById('book-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const slotNum = parseInt(document.getElementById('modal-slot-num').value);
  const nick = document.getElementById('input-pubg-nick').value.trim();
  const pubgId = document.getElementById('input-pubg-id').value.trim();
  const phone = document.getElementById('input-phone').value.trim();

  if (!nick || !pubgId) {
    alert("PUBG Nickname va PUBG ID to'ldirilishi shart!");
    return;
  }

  const tgUser = tg?.initDataUnsafe?.user || {};
  const userId = tgUser.id || 1000 + Math.floor(Math.random() * 900000);
  const userName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(' ') || nick;
  const username = tgUser.username || null;

  const submitBtn = document.getElementById('book-submit-btn');
  submitBtn.disabled = true;
  submitBtn.innerText = "BAND QILINMOQDA...";

  try {
    const res = await fetch('/api/book', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        slot_number: slotNum,
        user_id: userId,
        user_name: userName,
        user_username: username,
        pubg_nick: nick,
        pubg_id: pubgId,
        phone: phone || null
      })
    });

    const data = await res.json();
    if (data.success) {
      if (tg?.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('success');
      }
      alert(`🎉 Tabriklaymiz! Slot #${slotNum} muvaffaqiyatli band qilindi!`);
      modal.style.display = 'none';
      await loadSlots();
      await loadTournament();
    } else {
      if (tg?.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('error');
      }
      alert(data.error || "Slotni band qilishda xatolik yuz berdi!");
    }
  } catch (err) {
    alert("Server bilan aloqada xatolik yuz berdi.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = "TASDIQLASH VA BAND QILISH";
  }
});

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

// SALYUT (FIREWORKS) ENGINE
let fireworksAnimationId = null;
function startFireworks() {
  if (fireworksAnimationId) return;

  const canvas = document.getElementById('fireworks-canvas');
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const particles = [];
  const colors = ['#ff0055', '#ff9900', '#ffea00', '#00e676', '#00e5ff', '#d500f9', '#ffffff'];

  function createFirework(x, y) {
    const count = 45;
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 / count) * i;
      const speed = Math.random() * 4 + 2;
      particles.push({
        x: x,
        y: y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        alpha: 1,
        color: colors[Math.floor(Math.random() * colors.length)],
        radius: Math.random() * 2.5 + 1.5,
        decay: Math.random() * 0.015 + 0.01
      });
    }
  }

  // Periodic launch
  let timer = 0;
  function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    timer++;
    if (timer % 40 === 0) {
      const rx = Math.random() * canvas.width * 0.8 + canvas.width * 0.1;
      const ry = Math.random() * canvas.height * 0.5 + canvas.height * 0.1;
      createFirework(rx, ry);
    }

    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.04; // gravity
      p.alpha -= p.decay;

      if (p.alpha <= 0) {
        particles.splice(i, 1);
        continue;
      }

      ctx.save();
      ctx.globalAlpha = p.alpha;
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    fireworksAnimationId = requestAnimationFrame(loop);
  }

  loop();
}

// Initial load & Polling every 8 seconds
loadTournament();
loadSlots();
setInterval(() => {
  loadSlots();
  loadTournament();
}, 8000);
