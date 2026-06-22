# 📋 ATURAN LENGKAP POKER BOT

## 💰 SISTEM CHIP

### Starting Chips (Chip Awal)
- Setiap pemain baru memulai dengan **1000 chips**
- Chip digunakan untuk betting dalam permainan
- Chip tersimpan di database dan bisa digunakan di permainan berikutnya

### Chip Management
```
Starting Chips: 1000
Minimum Bet: 10 chips
Maximum Players: 10 per game
```

### Leaderboard & Chip Total
- Total chip Anda adalah akumulasi dari semua permainan
- **Win**: Jika menang, chip bertambah sesuai pot yang dikumpulkan
- **Lose**: Jika kalah, chip berkurang sesuai bet yang dikeluarkan
- **Fold**: Chip yang sudah dibet tidak kembali (hilang)

### Contoh Permainan:
```
Pemain A: 1000 chips (mulai)
Pemain B: 1000 chips (mulai)

Pre-flop: Pemain A bet 50 chips, Pemain B call 50 chips
Flop: Pemain A bet 100 chips, Pemain B call 100 chips
Turn: Pemain A bet 200 chips, Pemain B fold

Hasil:
- Pot Total: 500 chips
- Pemain A WIN: 1000 + 500 = 1500 chips
- Pemain B LOSE: 1000 - 200 = 800 chips
```

---

## 🎮 FASE PERMAINAN

### 1. PRE-FLOP
- Setiap pemain dapat 2 kartu hole (private cards)
- Kartu tidak boleh dilihat pemain lain
- Pemain dapat: **Check**, **Bet**, **Fold**, **Call**, **Raise**

### 2. FLOP
- 3 kartu komunitas dibuka di meja
- Pemain dapat menggunakan kartu ini + kartu hole mereka
- Betting round kedua dimulai

### 3. TURN
- 1 kartu komunitas tambahan dibuka
- Total sekarang 4 kartu komunitas + 2 hole cards = 6 kartu untuk dievaluasi
- Betting round ketiga

### 4. RIVER
- Kartu komunitas terakhir dibuka (total 5 kartu komunitas)
- Setiap pemain punya 7 kartu total untuk membuat tangan terbaik 5 kartu
- Betting round final

### 5. SHOWDOWN
- Semua pemain aktif membuka kartu mereka
- Bot otomatis mengevaluasi tangan terbaik
- Pemain dengan ranking tangan tertinggi menang
- Pemenang mengambil seluruh pot

---

## 🎯 RANKING TANGAN POKER (dari tertinggi)

### 1. 🏆 ROYAL FLUSH (Tertinggi)
```
A♠ K♠ Q♠ J♠ 10♠
```
- Straight flush dengan kartu tertinggi (Ace)
- Ranking terbaik dalam poker
- Probabilitas: 1 dalam 649,740

### 2. 🌟 STRAIGHT FLUSH
```
9♥ 8♥ 7♥ 6♥ 5♥
K♣ Q♣ J♣ 10♣ 9♣
```
- 5 kartu berurutan dengan suit sama
- Contoh: 5-6-7-8-9 semua hearts
- Tangan kedua terkuat

### 3. 👑 FOUR OF A KIND (Four)
```
K♠ K♥ K♦ K♣ 2♠
```
- 4 kartu dengan nilai sama
- 1 kartu kicker (kartu pendamping)
- Contoh: 4 King + 1 kartu lain

### 4. 🏠 FULL HOUSE
```
Q♠ Q♥ Q♦ 7♠ 7♥
```
- 3 kartu satu nilai + 2 kartu nilai lain
- Contoh: 3 Queen + 2 Seven
- Tiga of a kind + Pair

### 5. 💧 FLUSH
```
2♦ 5♦ 7♦ 9♦ K♦
```
- 5 kartu dengan suit sama (tapi tidak berurutan)
- Contoh: 5 kartu hearts (warna sama, nilai berbeda)
- Tidak perlu berurutan

### 6. 📍 STRAIGHT
```
9♠ 8♥ 7♦ 6♣ 5♠
```
- 5 kartu berurutan tapi suit berbeda
- Contoh: 5-6-7-8-9 (warna beda, urutan sama)
- Tidak boleh berurutan mundur dari Ace (hanya A-2-3-4-5 "The Wheel" yang boleh)

### 7. 🔱 THREE OF A KIND (Three)
```
10♠ 10♥ 10♦ K♠ 2♥
```
- 3 kartu dengan nilai sama
- 2 kartu kicker berbeda
- Contoh: 3 sepuluh + 2 kartu berbeda

### 8. 🎭 TWO PAIR
```
J♠ J♥ 5♦ 5♣ K♠
```
- 2 kartu satu nilai + 2 kartu nilai lain
- 1 kartu kicker
- Contoh: 1 Pair Jack + 1 Pair Five + 1 King

### 9. 💑 PAIR
```
7♠ 7♥ K♦ Q♣ 2♠
```
- 2 kartu dengan nilai sama
- 3 kartu kicker berbeda
- Contoh: 2 Seven + 3 kartu berbeda

### 10. 🎴 HIGH CARD (Terendah)
```
A♠ K♥ Q♦ J♣ 9♠
```
- Tidak ada kombinasi apapun
- Kartu tertinggi yang memutuskan pemenang
- Contoh: Ace high (jika pemain lain juga high card)

---

## 🎲 AKSI BETTING

### CHECK ✓
- Lanjut permainan tanpa mengeluarkan chip
- Hanya bisa dilakukan jika **belum ada bet** di ronde ini
- Jika semua pemain check, lanjut ke fase berikutnya

### BET 🎯
- Menaruh chip pertama kali di ronde
- Minimum bet: **10 chips**
- Pemain lain harus call, raise, atau fold

### CALL 📞
- Menyamakan jumlah bet pemain sebelumnya
- Contoh: Pemain A bet 100, Pemain B call 100
- Pot bertambah sesuai jumlah yang dipanggil

### RAISE 📈
- Menaikkan bet lebih tinggi dari sebelumnya
- Harus naikkan minimal 2x lipat atau sesuai aturan
- Contoh: Pemain A bet 100, Pemain B raise menjadi 200

### FOLD 🛑
- Menyerah, keluar dari ronde ini
- Chip yang sudah dibet tidak bisa diambil kembali
- Tidak bisa kembali ke permainan ini

### ALL-IN 💥
- Memasukkan SEMUA chip yang dimiliki
- Tidak bisa mengeluarkan chip lagi di ronde ini
- Jika kalah, pemain eliminated (out of game)

---

## 💡 STRATEGI DASAR

### Pre-Flop Strategy
```
STRONG HANDS (Bet/Raise):
- Royal Flush unlikely (AA, KK, QQ, JJ)
- Ace + King same suit
- High pairs (10+)

MEDIUM HANDS (Call):
- Medium pairs (5-9)
- Suited connectors (9-10, 8-9)

WEAK HANDS (Fold):
- Low cards (2-5)
- Unsuited low cards
```

### Pot Odds
- Jika pot = 100 chips dan perlu call 20 chips
- Pot odds = 100:20 = 5:1
- Butuh 20% chance menang untuk profitable call

### Hand Selection
```
Early Position: Mainkan tangan kuat saja
Middle Position: Bisa mainkan tangan medium
Late Position: Bisa mainkan lebih banyak tangan
```

---

## 📊 STATISTIK & LEADERBOARD

### Stats Pemain
Setiap pemain dilacak dengan data:
- **Total Chips**: Chips current yang dimiliki
- **Games Played**: Total permainan yang diikuti
- **Games Won**: Berapa kali menang
- **Win Rate**: Persentase menang (Wins/Games)
- **Total Winnings**: Total keuntungan chip

### Leaderboard Ranking
```
🥇 Rank 1 (Gold): Player dengan chips terbanyak
🥈 Rank 2 (Silver): Player kedua
🥉 Rank 3 (Bronze): Player ketiga
4-10: Top 10 lainnya
```

Lihat dengan: `/leaderboard`

---

## ⚠️ ATURAN PENTING

### Timeout
- Setiap pemain punya **5 menit** untuk aksi
- Jika timeout, otomatis fold
- Hindari delay dan play responsibly

### Fair Play
- ❌ TIDAK boleh bekerja sama (kolusi)
- ❌ TIDAK boleh cheat atau multi-account
- ✅ Mainkan dengan jujur dan fair
- 🔨 Pemain yang melanggar bisa di-ban

### Chip Management
- Minimum bet bisa di-adjust by admin
- Chip tidak bisa di-transfer antar pemain
- Chip hanya dari winning games atau reset

### Game Rules
- Minimum 2 pemain untuk mulai
- Maximum 10 pemain per game
- Jika 1 pemain tersisa (all fold), dia menang otomatis
- Jika 2 pemain all-in, community cards dibuka otomatis

---

## 🎯 CONTOH PERMAINAN LENGKAP

### Setup
```
Pemain A: 1000 chips
Pemain B: 1000 chips
Pemain C: 1000 chips
```

### Pre-Flop
```
Pemain A: Kartu 7♠ 7♥
Pemain B: Kartu K♦ Q♦
Pemain C: Kartu 2♠ 3♥

Aksi:
- Pemain A bet 50 chips
- Pemain B call 50 chips
- Pemain C fold (-0, chips: 1000)

Pot: 100 chips
```

### Flop
```
Community: 7♦ 5♣ 2♦

Aksi:
- Pemain A bet 100 chips (punya 3 of a kind)
- Pemain B call 100 chips (flush draw)

Pot: 300 chips
```

### Turn
```
Community: 7♦ 5♣ 2♦ K♠

Aksi:
- Pemain A bet 200 chips
- Pemain B call 200 chips (dapat pair)

Pot: 700 chips
```

### River
```
Community: 7♦ 5♣ 2♦ K♠ 9♣

Aksi:
- Pemain A check
- Pemain B check

Pot: 700 chips (no more betting)
```

### Showdown
```
Pemain A: 7♠ 7♥ + 7♦ 5♣ 2♦ K♠ 9♣ = THREE OF A KIND
Pemain B: K♦ Q♦ + 7♦ 5♣ 2♦ K♠ 9♣ = PAIR OF KINGS

WINNER: Pemain A (Three of a Kind > Pair)

Final Chips:
- Pemain A: 1000 - 50 - 100 - 200 + 700 = 1350 ✅
- Pemain B: 1000 - 50 - 100 - 200 = 650 ❌
- Pemain C: 1000 (fold early)
```

---

## 📞 BANTUAN LEBIH LANJUT

Gunakan perintah:
- `/help` - Bantuan umum
- `/leaderboard` - Lihat ranking
- `/stats` - Lihat statistik Anda
- `/start` - Info bot

Happy playing! 🍀🎰
