// ==========================================
// AUREX PUBG MOBILE - TELEGRAM WEB APP
// ==========================================

const tg = window.Telegram?.WebApp;
if (tg) {
  try {
    tg.ready();
    tg.expand();
  } catch (e) {
    console.warn("Telegram WebApp initialization error:", e);
  }
}

// Current User info
const tgUser = tg?.initDataUnsafe?.user || {};
const currentUser = {
  id: tgUser.id || 0,
  name: [tgUser.first_name, tgUser.last_name].filter(Boolean).join(' ') || "Jangchi",
  username: tgUser.username ? `@${tgUser.username}` : "@foydalanuvchi",
  raw_username: tgUser.username || null
};

let tournamentData = {};
let slotsData = [];
let allPlayersData = [];
let isAdminUser = false;

// TAB NAVIGATION
window.switchTab = function(targetId) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

  const tabBtn = document.querySelector(`.nav-tab[data-tab="${targetId}"]`);
  if (tabBtn) tabBtn.classList.add('active');

  const content = document.getElementById(targetId);
  if (content) content.classList.add('active');

  if (tg?.HapticFeedback) {
    tg.HapticFeedback.selectionChanged();
  }
};

document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const targetId = tab.getAttribute('data-tab');
    switchTab(targetId);
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

// TOAST NOTIFICATION
function showToast(message = "Nusxa olindi!") {
  const toast = document.getElementById('toast-notification');
  if (!toast) return;
  toast.innerText = message;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2000);
}

// COPY HELPER
window.copyText = function(textOrId, btn) {
  let val = textOrId;
  const el = document.getElementById(textOrId);
  if (el) {
    val = el.innerText.trim();
  }

  if (navigator.clipboard) {
    navigator.clipboard.writeText(val).then(() => {
      showToast("Nusxa olindi! 📋");
      if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
    }).catch(() => {
      fallbackCopy(val);
    });
  } else {
    fallbackCopy(val);
  }
};

function fallbackCopy(val) {
  const textArea = document.createElement("textarea");
  textArea.value = val;
  document.body.appendChild(textArea);
  textArea.select();
  try {
    document.execCommand('copy');
    showToast("Nusxa olindi! 📋");
    if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
  } catch (err) {
    console.error("Copy failed", err);
  }
  document.body.removeChild(textArea);
}

// ==========================================
// 1. CHECK ADMIN STATUS
// ==========================================
async function checkAdminStatus() {
  if (!currentUser.id) return;
  try {
    const res = await fetch(`/api/check_admin?user_id=${currentUser.id}`);
    if (!res.ok) return;
    const data = await res.json();
    isAdminUser = !!data.is_admin;

    const adminNav = document.getElementById('admin-nav-tab');
    const roleBadge = document.getElementById('user-role-badge');

    if (isAdminUser) {
      if (adminNav) adminNav.style.display = 'flex';
      if (roleBadge) {
        roleBadge.innerText = "🛡️ ADMIN";
        roleBadge.style.color = "#ff5500";
        roleBadge.style.borderColor = "#ff5500";
      }
    } else {
      if (adminNav) adminNav.style.display = 'none';
      if (roleBadge) {
        roleBadge.innerText = "O'YINCHI";
      }
    }
  } catch (err) {
    console.error("Admin check error:", err);
  }
}

// ==========================================
// 2. LOAD TOURNAMENT DATA
// ==========================================
async function loadTournament() {
  try {
    const res = await fetch('/api/tournament');
    if (!res.ok) return;
    tournamentData = await res.json();

    const titleEl = document.getElementById('tournament-title');
    if (titleEl) titleEl.innerText = tournamentData.title || 'Aurex PUBG Mobile Turniri';

    const stageEl = document.getElementById('stage-badge');
    if (stageEl) stageEl.innerText = tournamentData.stage_name || "Ro'yxatga olish";

    // Slot Price
    const price = tournamentData.slot_price || 0;
    const priceFormatted = price > 0 ? `${price.toLocaleString()} so'm` : "BEPUL / TEKIN";
    const priceDisp = document.getElementById('slot-price-display');
    if (priceDisp) priceDisp.innerText = priceFormatted;
    const modalPrice = document.getElementById('modal-slot-price');
    if (modalPrice) modalPrice.innerText = priceFormatted;

    // Card info
    const cardNum = document.getElementById('modal-card-num');
    if (cardNum && tournamentData.card_number) cardNum.innerText = tournamentData.card_number;

    // Room info
    const roomTitle = document.getElementById('room-status-title');
    const roomDesc = document.getElementById('room-status-desc');
    const roomCreds = document.getElementById('room-creds');
    const roomIdVal = document.getElementById('room-id-val');
    const roomPassVal = document.getElementById('room-pass-val');

    if (tournamentData.room_id && tournamentData.room_password) {
      if (roomTitle) roomTitle.innerText = "🔥 XONA OCHILGAN!";
      if (roomDesc) roomDesc.innerText = "PUBG Mobile ilovasida pastdagi ID va parol orqali xonaga kiring:";
      if (roomIdVal) roomIdVal.innerText = tournamentData.room_id;
      if (roomPassVal) roomPassVal.innerText = tournamentData.room_password;
      if (roomCreds) roomCreds.style.display = 'grid';
    } else {
      if (roomTitle) roomTitle.innerText = "Xona hali ochilmagan";
      if (roomDesc) roomDesc.innerText = "Turnir boshlanishidan 10 daqiqa oldin Room ID va Parol beriladi.";
      if (roomCreds) roomCreds.style.display = 'none';
    }

    // Grand Final fireworks
    if (tournamentData.status === 'final') {
      startFireworks();
      if (tournamentData.winner_nick) {
        const winnerBannerNick = document.getElementById('banner-winner-nick');
        if (winnerBannerNick) winnerBannerNick.innerText = tournamentData.winner_nick;
        const fireworksBanner = document.getElementById('fireworks-banner');
        if (fireworksBanner) fireworksBanner.style.display = 'flex';
      }
    }

  } catch (err) {
    console.error("Turnir yuklashda xato:", err);
  }
}

// ==========================================
// 3. LOAD SLOTS
// ==========================================
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
        const isPending = slot.status === 'pending';
        const statusHtml = isPending 
          ? `<span class="slot-status-pill" style="background: rgba(255, 171, 0, 0.2); color: #ffab00; border: 1px solid rgba(255, 171, 0, 0.4);">🟡 KUTILMOQDA</span>`
          : `<span class="slot-status-pill">🔴 BAND</span>`;

        card.innerHTML = `
          <div class="slot-card-header">
            <span class="slot-badge-num">SLOT #${numStr}</span>
            ${statusHtml}
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

    // Also update Admin slots list if admin tab exists
    renderAdminSlotsList(slotsData);

  } catch (err) {
    console.error("Slotlarni yuklashda xato:", err);
  }
}

// ==========================================
// 4. LOAD PLAYERS (MIJOZLAR)
// ==========================================
async function loadPlayers() {
  try {
    const res = await fetch('/api/players');
    if (!res.ok) return;
    allPlayersData = await res.json();

    renderPlayersList(allPlayersData);

    const count = allPlayersData.length;
    document.getElementById('players-summary-badge').innerText = `${count} / 16`;

    const remaining = 16 - count;
    const remainingEl = document.getElementById('remaining-count-text');
    if (remainingEl) {
      if (remaining > 0) {
        remainingEl.innerText = `Yana ${remaining} ta bo'sh o'rin mavjud!`;
        document.getElementById('remaining-slots-card').style.display = 'flex';
      } else {
        remainingEl.innerText = "Barcha 16 ta o'rin to'ldi! (16/16)";
        document.getElementById('remaining-slots-card').style.display = 'none';
      }
    }

  } catch (err) {
    console.error("Mijozlarni yuklashda xato:", err);
  }
}

function renderPlayersList(players) {
  const container = document.getElementById('players-list-container');
  if (!container) return;

  container.innerHTML = '';

  if (!players || players.length === 0) {
    container.innerHTML = `
      <div class="empty-slot-card">
        <div class="empty-slot-icon">👥</div>
        <h4>Hozircha hech kim ro'yxatdan o'tmadi</h4>
        <p>Birinchi bo'lib slot band qiling va g'oliblik uchun kurashing!</p>
        <button class="action-btn-sm" onclick="switchTab('slots-tab')">🎮 Slot Tanlash</button>
      </div>
    `;
    return;
  }

  players.forEach(p => {
    const card = document.createElement('div');
    card.className = 'player-card';

    const numStr = String(p.slot_number).padStart(2, '0');
    const uName = p.user_username ? `@${p.user_username}` : (p.user_name || "O'yinchi");

    card.innerHTML = `
      <div class="player-left">
        <div class="player-slot-badge">#${numStr}</div>
        <div class="player-meta">
          <h4>👤 ${escapeHtml(p.pubg_nick || "Noma'lum")}</h4>
          <p>
            <span>ID: <code>${escapeHtml(p.pubg_id || "---")}</code></span>
            <button class="copy-btn" onclick="copyText('${escapeHtml(p.pubg_id || "")}', this)">📋</button>
          </p>
          <p style="font-size: 10px; color: #6e7681;">${escapeHtml(uName)}</p>
        </div>
      </div>
      <div class="player-right">
        <span class="slot-status-pill" style="${p.status === 'pending' ? 'background: rgba(255, 171, 0, 0.2); color: #ffab00; border: 1px solid rgba(255, 171, 0, 0.4);' : 'background: rgba(0, 230, 118, 0.15); color: #00e676; border: 1px solid rgba(0, 230, 118, 0.4);'}">
          ${p.status === 'pending' ? '🟡 KUTILMOQDA' : '✅ FAOL'}
        </span>
        ${p.phone ? `<span style="font-size: 10px; color: #8b949e;">📱 ${escapeHtml(p.phone)}</span>` : ''}
      </div>
    `;

    container.appendChild(card);
  });
}

// Search players filter
const searchInput = document.getElementById('player-search-input');
if (searchInput) {
  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderPlayersList(allPlayersData);
      return;
    }
    const filtered = allPlayersData.filter(p => {
      const nick = (p.pubg_nick || '').toLowerCase();
      const pid = (p.pubg_id || '').toLowerCase();
      const uname = (p.user_name || '').toLowerCase();
      const uuser = (p.user_username || '').toLowerCase();
      return nick.includes(q) || pid.includes(q) || uname.includes(q) || uuser.includes(q);
    });
    renderPlayersList(filtered);
  });
}

// ==========================================
// 5. LOAD USER PROFILE & BOOKED SLOT
// ==========================================
async function loadProfile() {
  try {
    // Populate user telegram details
    const letter = (currentUser.name || "J").charAt(0).toUpperCase();
    document.getElementById('user-avatar-letter').innerText = letter;
    document.getElementById('user-profile-name').innerText = currentUser.name;
    document.getElementById('user-profile-username').innerText = currentUser.username;
    document.getElementById('user-profile-id').innerText = currentUser.id ? `ID: ${currentUser.id}` : 'ID: Telegram orqali ochilgan';

    const container = document.getElementById('my-slot-content');
    if (!container) return;

    if (!currentUser.id) {
      container.innerHTML = `
        <div class="empty-slot-card">
          <div class="empty-slot-icon">⚠️</div>
          <h4>Foydalanuvchi aniqlanmadi</h4>
          <p>Iltimos, ushbu Web App'ni Telegram boti orqali oching.</p>
        </div>
      `;
      return;
    }

    const res = await fetch(`/api/profile?user_id=${currentUser.id}`);
    if (!res.ok) return;
    const data = await res.json();

    const userSlot = data.slot;

    if (userSlot) {
      const numStr = String(userSlot.slot_number).padStart(2, '0');
      const hasRoom = tournamentData.room_id && tournamentData.room_password;
      const isPending = userSlot.status === 'pending';

      const statusPill = isPending 
        ? `<span class="slot-status-pill" style="background: rgba(255, 171, 0, 0.2); color: #ffab00; border: 1px solid #ffab00;">🟡 KUTILMOQDA</span>`
        : `<span class="slot-status-pill" style="background: rgba(0, 230, 118, 0.2); color: #00e676; border: 1px solid #00e676;">✅ TASDIQLANGAN</span>`;

      const noticeBanner = isPending
        ? `<div style="background: rgba(255, 171, 0, 0.12); border: 1px solid #ffab00; border-radius: 10px; padding: 10px 12px; margin-bottom: 12px; text-align: center;">
            <div style="font-size: 13px; font-weight: 700; color: #ffab00;">⏳ To'lov chekingiz tekshirilmoqda</div>
            <p style="font-size: 11px; color: #c9d1d9; margin-top: 4px;">
              Siz yuborgan to'lov cheki administratorga (Murodaliyev Abdulaziz) yuborilgan. Tez orada tasdiqlanadi!
            </p>
          </div>`
        : `<div style="background: rgba(0, 230, 118, 0.1); border: 1px solid #00e676; border-radius: 10px; padding: 8px 12px; margin-bottom: 12px; text-align: center;">
            <span style="font-size: 12px; font-weight: 700; color: #00e676;">✅ Turnirda faol ishtirokchi</span>
          </div>`;

      container.innerHTML = `
        <div class="my-slot-card">
          <div class="my-slot-card-header">
            <span class="my-slot-title">🏆 SIZNING SLOTINGIZ: #${numStr}</span>
            ${statusPill}
          </div>

          ${noticeBanner}

          <div class="details-grid">
            <div class="detail-item">
              <span class="detail-label">PUBG NICKNAME</span>
              <span class="detail-val">${escapeHtml(userSlot.pubg_nick || "---")}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">PUBG ID</span>
              <span class="detail-val">
                <code>${escapeHtml(userSlot.pubg_id || "---")}</code>
                <button class="copy-btn" onclick="copyText('${escapeHtml(userSlot.pubg_id || "")}', this)">📋</button>
              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">TELEFON</span>
              <span class="detail-val">${escapeHtml(userSlot.phone || "Kiritilmagan")}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">RO'YXAT VAQTI</span>
              <span class="detail-val" style="font-size: 11px;">${escapeHtml(userSlot.registered_at || "---")}</span>
            </div>
          </div>

          ${hasRoom ? `
            <div style="background: rgba(255, 136, 0, 0.15); border: 1px solid #ff8800; border-radius: 10px; padding: 12px; margin-bottom: 12px; text-align: center;">
              <div style="font-size: 12px; color: #ffaa00; font-weight: 700;">🔥 XONA OCHILGAN!</div>
              <div style="display: flex; justify-content: space-around; margin-top: 8px;">
                <div>
                  <div style="font-size: 10px; color: #8b949e;">ROOM ID</div>
                  <div style="font-family: monospace; font-size: 16px; font-weight: 700; color: #00e676;">${tournamentData.room_id}</div>
                  <button class="copy-btn" onclick="copyText('${tournamentData.room_id}', this)">📋</button>
                </div>
                <div>
                  <div style="font-size: 10px; color: #8b949e;">PAROL</div>
                  <div style="font-family: monospace; font-size: 16px; font-weight: 700; color: #00e676;">${tournamentData.room_password}</div>
                  <button class="copy-btn" onclick="copyText('${tournamentData.room_password}', this)">📋</button>
                </div>
              </div>
              <div style="font-size: 10px; color: #ffab00; margin-top: 6px;">⚠️ O'yinda aynan Slot #${numStr} ga o'tiring!</div>
            </div>
          ` : ''}

          <button class="cancel-slot-btn" onclick="cancelUserSlot(${userSlot.slot_number})">
            ❌ Slotni Bekor Qilish / Bo'shatish
          </button>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="empty-slot-card">
          <div class="empty-slot-icon">🎮</div>
          <h4>Siz hali slot band qilmadingiz</h4>
          <p>16 ta slotdan birini tanlab, turnirda o'z o'rningizni egallang!</p>
          <button class="submit-btn" style="max-width: 240px; margin: 0 auto; display: block;" onclick="switchTab('slots-tab')">
            🎮 HOZIR SLOT TANLASH
          </button>
        </div>
      `;
    }

  } catch (err) {
    console.error("Profil yuklashda xato:", err);
  }
}

// ==========================================
// 6. CANCEL USER SLOT
// ==========================================
window.cancelUserSlot = async function(slotNumber) {
  if (!confirm(`Haqiqatan ham Slot #${slotNumber} ni bekor qilmoqchimisiz?`)) {
    return;
  }

  try {
    const res = await fetch('/api/cancel_slot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        slot_number: slotNumber,
        user_id: currentUser.id
      })
    });
    const data = await res.json();
    if (data.success) {
      alert("✅ Slotingiz bekor qilindi.");
      if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
      await loadSlots();
      await loadPlayers();
      await loadProfile();
    } else {
      alert(data.error || "Bekor qilishda xatolik yuz berdi");
    }
  } catch (err) {
    alert("Server bilan aloqa xatosi.");
  }
};

// ==========================================
// 7. OPEN BOOK MODAL & SUBMIT
// ==========================================
window.openBookModal = function(slotNumber) {
  if (tournamentData.status !== 'registration' && tournamentData.status !== 'open') {
    alert("Turnirga ro'yxatga olish hozirda yopiq!");
    return;
  }

  document.getElementById('modal-slot-title').innerText = `SLOT #${String(slotNumber).padStart(2, '0')} BAND QILISH`;
  document.getElementById('modal-slot-num').value = slotNumber;
  document.getElementById('input-pubg-nick').value = '';
  document.getElementById('input-pubg-id').value = '';
  document.getElementById('input-phone').value = '';

  const receiptInput = document.getElementById('input-receipt');
  if (receiptInput) receiptInput.value = '';
  const previewWrap = document.getElementById('receipt-preview-wrap');
  if (previewWrap) previewWrap.style.display = 'none';

  modal.style.display = 'flex';
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('medium');
  }
};

// Image preview for receipt
const receiptInputEl = document.getElementById('input-receipt');
if (receiptInputEl) {
  receiptInputEl.addEventListener('change', (e) => {
    const file = e.target.files[0];
    const previewWrap = document.getElementById('receipt-preview-wrap');
    const previewImg = document.getElementById('receipt-preview-img');
    if (file && previewWrap && previewImg) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        previewImg.src = evt.target.result;
        previewWrap.style.display = 'block';
      };
      reader.readAsDataURL(file);
    }
  });
}

document.getElementById('book-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const slotNum = parseInt(document.getElementById('modal-slot-num').value);
  const nick = document.getElementById('input-pubg-nick').value.trim();
  const pubgId = document.getElementById('input-pubg-id').value.trim();
  const phone = document.getElementById('input-phone').value.trim();
  const receiptInput = document.getElementById('input-receipt');
  const receiptFile = receiptInput?.files?.[0];

  if (!nick || !pubgId) {
    alert("PUBG Nickname va PUBG ID to'ldirilishi shart!");
    return;
  }

  if (!phone) {
    alert("Iltimos, telefon raqamingizni kiriting!");
    return;
  }

  if (!receiptFile) {
    alert("Iltimos, to'lov cheki skrinshotini yuklang!");
    return;
  }

  const submitBtn = document.getElementById('book-submit-btn');
  submitBtn.disabled = true;
  submitBtn.innerText = "CHEK VA ARIZA YUBORILMOQDA...";

  try {
    const formData = new FormData();
    formData.append('slot_number', slotNum);
    formData.append('user_id', currentUser.id || (1000 + Math.floor(Math.random() * 900000)));
    formData.append('user_name', currentUser.name);
    formData.append('user_username', currentUser.raw_username || '');
    formData.append('pubg_nick', nick);
    formData.append('pubg_id', pubgId);
    formData.append('phone', phone);
    formData.append('receipt', receiptFile);

    const res = await fetch('/api/book_with_receipt', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (data.success) {
      if (tg?.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('success');
      }
      alert(`🎉 To'lov chekingiz adminga tekshirish uchun yuborildi!\n\nSlot #${slotNum} tez orada tasdiqlanadi.`);
      modal.style.display = 'none';
      await loadSlots();
      await loadPlayers();
      await loadProfile();
      await loadTournament();
      switchTab('profile-tab');
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
    submitBtn.innerText = "🚀 TO'LOV CHEKINI VA ARIZANI YUBORISH";
  }
});

// ==========================================
// 8. ADMIN ACTIONS
// ==========================================
function renderAdminSlotsList(slots) {
  const container = document.getElementById('admin-slots-manage-list');
  if (!container) return;

  container.innerHTML = '';
  slots.forEach(s => {
    const row = document.createElement('div');
    row.className = 'admin-slot-row';
    const numStr = String(s.slot_number).padStart(2, '0');
    const isBooked = !!s.user_id;

    row.innerHTML = `
      <div>
        <span style="font-family: monospace; color: #ff9900; font-weight: 700;">#${numStr}</span>
        <span class="nick" style="margin-left: 8px;">${isBooked ? escapeHtml(s.pubg_nick || "O'yinchi") : '<span style="color:#6e7681;">Bo\'sh</span>'}</span>
        ${isBooked ? `<span style="font-size: 10px; color: #8b949e; margin-left: 6px;">(ID: ${s.pubg_id})</span>` : ''}
      </div>
      <div>
        ${isBooked ? `
          <button class="admin-kick-btn" onclick="adminKickSlot(${s.slot_number})">Kick ❌</button>
        ` : `<span style="font-size: 10px; color: #00e676;">🟢 Bo'sh</span>`}
      </div>
    `;
    container.appendChild(row);
  });
}

window.adminSaveRoom = async function() {
  const roomId = document.getElementById('admin-room-id').value.trim();
  const roomPass = document.getElementById('admin-room-pass').value.trim();

  if (!roomId || !roomPass) {
    alert("Iltimos, Room ID va Parolni kiriting!");
    return;
  }

  try {
    const res = await fetch('/api/admin/room', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        admin_id: currentUser.id,
        room_id: roomId,
        room_password: roomPass
      })
    });
    const data = await res.json();
    if (data.success) {
      alert("✅ Xona ma'lumotlari e'lon qilindi!");
      await loadTournament();
      await loadProfile();
    } else {
      alert(data.error || "Xatolik yuz berdi");
    }
  } catch (err) {
    alert("Server xatosi.");
  }
};

window.adminSetStage = async function(status, stageName) {
  try {
    const res = await fetch('/api/admin/stage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        admin_id: currentUser.id,
        status: status,
        stage_name: stageName
      })
    });
    const data = await res.json();
    if (data.success) {
      alert(`✅ Turnir bosqichi: «${stageName}» qilib o'zgartirildi!`);
      await loadTournament();
    } else {
      alert(data.error || "Bosqichni o'zgartirishda xatolik");
    }
  } catch (err) {
    alert("Server xatosi.");
  }
};

window.adminTriggerFinalModal = async function() {
  const winner = prompt("Turnir g'olibining PUBG Nickname'ini kiriting:", "WINNER");
  if (!winner) return;

  try {
    const res = await fetch('/api/admin/stage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        admin_id: currentUser.id,
        status: 'final',
        stage_name: '🏆 Grand Final & Salyut',
        winner_nick: winner
      })
    });
    const data = await res.json();
    if (data.success) {
      startFireworks();
      document.getElementById('banner-winner-nick').innerText = winner;
      document.getElementById('fireworks-banner').style.display = 'flex';
      await loadTournament();
    }
  } catch (err) {
    alert("Server xatosi.");
  }
};

window.adminSavePrice = async function() {
  const priceVal = document.getElementById('admin-slot-price').value;
  const price = parseInt(priceVal || 0);

  try {
    const res = await fetch('/api/admin/price', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        admin_id: currentUser.id,
        price: price
      })
    });
    const data = await res.json();
    if (data.success) {
      alert(`✅ Slot narxi ${price.toLocaleString()} so'm qilib belgilandi!`);
      await loadTournament();
    } else {
      alert(data.error || "Narxni o'zgartirishda xatolik");
    }
  } catch (err) {
    alert("Server xatosi.");
  }
};

window.adminKickSlot = async function(slotNumber) {
  if (!confirm(`Haqiqatan ham Slot #${slotNumber} dagi o'yinchini chetlatmoqchimisiz?`)) {
    return;
  }

  try {
    const res = await fetch('/api/admin/kick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        admin_id: currentUser.id,
        slot_number: slotNumber
      })
    });
    const data = await res.json();
    if (data.success) {
      alert(`✅ Slot #${slotNumber} bo'shatildi!`);
      await loadSlots();
      await loadPlayers();
      await loadProfile();
    } else {
      alert(data.error || "Xatolik");
    }
  } catch (err) {
    alert("Server xatosi.");
  }
};

window.adminResetTournament = async function() {
  const code = prompt("Turnirni tozalash uchun 'RESET' so'zini yozing:");
  if (code !== 'RESET') return;

  try {
    const res = await fetch('/api/admin/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        admin_id: currentUser.id,
        title: "Aurex PUBG Mobile Turniri"
      })
    });
    const data = await res.json();
    if (data.success) {
      alert("✅ Turnir to'liq tozalandi! Barcha slotlar bo'shatildi.");
      await loadSlots();
      await loadPlayers();
      await loadProfile();
      await loadTournament();
    } else {
      alert(data.error || "Xatolik");
    }
  } catch (err) {
    alert("Server xatosi.");
  }
};

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement('div');
  div.innerText = String(text);
  return div.innerHTML;
}

// ==========================================
// 9. SALYUT (FIREWORKS) ENGINE
// ==========================================
let fireworksAnimationId = null;
function startFireworks() {
  if (fireworksAnimationId) return;

  const canvas = document.getElementById('fireworks-canvas');
  if (!canvas) return;
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
      p.vy += 0.04;
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

// ==========================================
// 10. INITIALIZATION & POLLING
// ==========================================
async function init() {
  try { await checkAdminStatus(); } catch (e) { console.error("checkAdminStatus error:", e); }
  try { await loadTournament(); } catch (e) { console.error("loadTournament error:", e); }
  try { await loadSlots(); } catch (e) { console.error("loadSlots error:", e); }
  try { await loadPlayers(); } catch (e) { console.error("loadPlayers error:", e); }
  try { await loadProfile(); } catch (e) { console.error("loadProfile error:", e); }

  // Periodic refresh every 6 seconds
  setInterval(async () => {
    try { await loadTournament(); } catch (e) {}
    try { await loadSlots(); } catch (e) {}
    try { await loadPlayers(); } catch (e) {}
  }, 6000);
}

init();
