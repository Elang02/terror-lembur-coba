# Terror Lembur — Godot Base (Level 1)

Co-op horror top-down 2 pemain di kantor gelap. Satu pemain mengalihkan
sosok yang mengejar, satu lagi menyelesaikan tugas — lalu kabur berdua
lewat Lobby.

> Dibuat dengan Godot 4.4 (GL Compatibility). Bisa dibuka di Godot 4.4–4.7.
> Peta Level 1 memakai **TileMap** (3 layer: Floor / Walls / Props) dengan
> collision dari TileSet, sesuai gambar referensi "Desain Map – Level 1".

![Preview peta Level 1](docs/map_preview.png)

## Cara main (cepat)

1. Install **Godot 4.4+** dari https://godotengine.org/download (pilih
   Standard, bukan .NET).
2. Buka Godot → **Import** → pilih folder project ini (`project.godot`) →
   **Import & Edit**. Tunggu import selesai.
3. Tekan **F5** (atau ▶) untuk main. Di Main Menu:
   - **Tes Sendiri (Solo)** — 1 pemain, untuk tes map & tugas.
   - **Buat Game (Host — PC 1)** lalu **Gabung (Join — PC 2)** dari PC kedua.
     Detail 2 PC ada di [docs/MULTIPLAYER.md](docs/MULTIPLAYER.md).

### Kontrol (keyboard)

| Aksi | Tombol |
|---|---|
| Gerak | WASD / Panah |
| Lari (lebih cepat, tapi berisik — enemy bisa dengar) | Shift |
| Interaksi: buka tugas / ambil item / sembunyi | E (atau F) |
| Tahan untuk menyelamatkan teman di kurungan | E (atau F) |
| Batalkan minigame tugas | Esc |

## Yang sudah jadi di base ini

- **Map Level 1 (TileMap 64×40, tile 32px)** — 15 ruangan sesuai referensi:
  Gudang, Pantry, R. Istirahat, R. Rapat, R. Manager, R. Keuangan, Toilet,
  R. Arsip, Area Kerja, R. IT, R. Fotokopi, R. HR, R. Serbaguna, R. Server,
  Lobby (pintu keluar), Resepsionis. Banyak rute & koneksi antar-ruangan,
  tidak ada jalan buntu, dan ruangan dipenuhi furnitur (meja, kursi, rak,
  boks, kertas, tanaman, dll) supaya terasa berantakan seperti kantor
  sungguhan. Lihat [docs/MAP_LEVEL_1.md](docs/MAP_LEVEL_1.md).
- **Gelap & POV per pemain** — CanvasModulate gelap, lampu langit-langit
  berkedip, tiap pemain bawa cahaya sendiri, pojok tanpa lampu tetap gelap.
  Di multiplayer 2 PC, tiap PC menampilkan kameranya sendiri.
- **7 tugas = 7 minigame kantor** — tekan E di stasiun tugas: Laporan
  Excel (hitung cepat), Susun Slide (urutkan 1-4), Balas Email (ketik
  kata), Fotokopi (timing Spasi), Sortir Arsip (folder 1/2/3), Panel
  Listrik (hafalkan urutan lampu), dan Server yang **wajib dikerjakan
  2 pemain** (tiap pemain menyelesaikan sinkronisasinya sendiri).
  Musuh tetap bergerak selagi kamu kerja; Esc membatalkan. Selesaikan
  semua untuk membuka pintu keluar.
- **Enemy stalker** — patrol loop, mengejar dengan line-of-sight + waktu
  reaksi (tidak instan), mencari di posisi terakhir, lalu **blink**: hilang
  tiba-tiba (lampu padam + getar kamera), teleport ke spawn acak, lalu **buta
  2,5 detik** supaya pemain masih bisa kabur.
- **Tertangkap → terkurung → diselamatkan** — pemain yang tertangkap masuk
  kurungan; partner harus mencari **Item Bangkit** (spawn acak) lalu menahan E
  di kurungan. Kalau berdua tertangkap = gagal. Mode solo: kurungan terbuka
  sendiri setelah 12 detik (untuk tes).
- **2 pintu terkunci** (pintas) — Pintu A dibuka tugas Arsip, Pintu B dibuka
  tugas Panel Listrik. Map tetap bisa dilalui penuh saat keduanya tertutup.
- **Pintu keluar butuh 2 pemain** — berdiri berdua di zona Lobby sampai bar
  penuh. Hasil akhir: **Happy Ending** (0 tertangkap) / **Bad Ending**
  (pernah tertangkap tapi kabur) + **bintang 1–3** dari waktu & jumlah
  tertangkap. Bintang & waktu terbaik tersimpan per PC.
- **Multiplayer 2 PC (ENet, UDP 7777)** — host otoritatif untuk AI/tugas/
  pintu/ending; posisi disinkronkan 20 Hz. Lihat
  [docs/MULTIPLAYER.md](docs/MULTIPLAYER.md).

## Merapikan map di TileMap (editor)

1. Buka `scenes/level_1.tscn`.
2. Pilih layer **Floor**, **Walls**, atau **Props** di panel Scene, lalu
   gambar tile dari TileSet di panel bawah (tab **TileSet**).
   - **Floor**: lantai saja, tidak ada collision.
   - **Walls**: dinding, ada collision penuh 1 tile.
   - **Props**: meja/rak/tanaman/dll, ada collision penuh 1 tile.
3. Aturannya supaya gameplay tetap jalan:
   - Jangan menutup satu-satunya jalan ke ruangan/tugas. Pintu (cell kosong
     di layer Walls) jangan ditutup semua.
   - Cell pintu terkunci (oranye di preview) harus tetap **kosong di layer
     Walls** — soliditasnya dari node `LockedDoor`, bukan tile.
   - Node gameplay (Tasks, HidingSpots, Doors, ExitDoor, Spawns) bisa
     digeser bebas dengan mouse; posisinya tidak terikat tile.
   - Setelah mengubah dinding/prop, jalankan smoke test (di bawah) untuk
     memastikan semua tugas masih terjangkau.
4. Layout awal dibuat dari `levels/level_1_grid.txt` oleh generator
   `tools/build_level_1.gd`. Kalau mengedit langsung di editor, tidak perlu
   generator lagi. Kalau mau regenerate dari file grid:
   `godot --headless --import` lalu `godot --headless res://tools/build_level_1.tscn`
   (ini akan menimpa `scenes/level_1.tscn`).

## Level 2 — Lobi Kantor "Gelap Gulita" (dalam pengerjaan)

- Scene: `scenes/level_2.tscn` (TileMap 72×46), script: `scripts/level_2.gd`.
- Coba dengan membuka scene-nya lalu tekan **F6** (belum ada tombol di menu).
- Penjelasan node, aturan edit, dan status mekanik: `docs/MAP_LEVEL_2.md`.
- Cek otomatis: `tests/smoke_test_level2.tscn` (F6, cari `SMOKE L2: ALL PASS`).

## Aset itch.io (sudah terpasang)

Art di game ini berasal dari tiga paket itch.io yang sudah dipasang
(atlas TileMap, sprite karakter, dekorasi) — lihat daftar & kredit di
[CREDITS.md](CREDITS.md) dan cara mengubah/menambahnya di
[assets/tiles/README_ASSETS.md](assets/tiles/README_ASSETS.md).
Paket aslinya tidak disertakan di project; unduh dari halaman
itch.io masing-masing kalau mau mengambil potongan lain.

## Struktur project

```
project.godot            Konfigurasi, InputMap, Autoload
scenes/                  Main menu, Level 1 (TileMap), player, enemy,
                         task/hiding/exit/door/revive/cage, HUD
scripts/                 GDScript gameplay + multiplayer
scripts/autoloads/       NetworkManager (ENet), GameProgress (bintang)
scripts/minigames/       Minigame tugas (Excel, Slide, Email, dll)
assets/tiles/            Atlas + TileSet (office_tileset.tres)
assets/characters/       Sprite karakter (Imersa office_worker)
assets/decor/            Dekorasi overlay (nacl1234)
assets/sprites/          Sprite placeholder lama + tekstur cahaya
levels/level_1_grid.txt  Sumber grid layout Level 1 (64x40)
tools/build_level_1.*    Generator TileSet + scene Level 1 dari grid
tests/                   Smoke test headless + net test
docs/                    Panduan map, multiplayer, instalasi GDAS/MCP
```

## Tes (headless, Godot 4.4+)

```bash
# Smoke test: 77 cek (tile, collision, A*, minigame, kurungan, blink, exit)
godot --headless --path . res://tests/smoke_test.tscn
# Uji host headless (client butuh UDP loopback; di sandbox tertentu diblokir)
godot --headless --path . res://tests/net_test.tscn -- --net-role=host
```

Hasil verifikasi terakhir (Godot 4.4.1 headless, 2026-11-13): smoke test
**77/77 lolos** (termasuk 7 minigame end-to-end), soak solo 300 frame
bersih, host headless jalan & enemy patrol. Koneksi client→host **belum**
terverifikasi live di VM ini karena sandbox memblokir socket UDP — uji
2 PC sungguhan di LAN sebelum rilis.

## Instalasi skill & MCP (opsional, untuk pengembangan)

- **Game-Dev-Agentic-Skills** (pustaka skill Godot/Bevy) dan **Godot MCP**
  (jembatan AI ↔ editor Godot): panduan lengkap di
  [docs/GDAS_MCP_INSTALL.md](docs/GDAS_MCP_INSTALL.md). Project ini sudah
  berisi `.cursor/mcp.json` siap pakai untuk Cursor.
- **Superpowers** (metodologi dev untuk coding agent): terpasang untuk Muse
  di workspace ini, bukan bagian dari project Godot.

## Lisensi

Kode project ini bebas dipakai untuk pengembangan *Terror Lembur*.
Aset itch.io mengikuti lisensi masing-masing pembuatnya —
lihat [CREDITS.md](CREDITS.md).
