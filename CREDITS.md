# Credits — Terror Lembur

## Aset game (itch.io) — dipakai di project ini

Art di game ini dibuat dari tiga paket di bawah. Asetnya disertakan
HANYA dalam bentuk sudah terpasang di project (atlas
`assets/tiles/office_atlas.png`, sprite karakter, dan dekorasi) —
paket aslinya TIDAK disertakan. Untuk mengunduh atau mengubah paket
asli, buka halaman masing-masing dan ikuti lisensinya.

1. **Office Pixel Art by Imersa Studios**
   https://imersastudios.itch.io/office-pixel-art
   Lantai, dinding, meja rapat, tanaman, lemari arsip, dan karakter
   pemain/enemy (versi Free). Kredit wajib dicantumkan sesuai lisensi.
2. **Modern Office Tileset 16x16 (Free Sample)** — RubberStudio
   https://rubberstudio.itch.io/modern-office-tileset-16x16-free-sample
   Lantai ubin/karpet, meja+monitor, rak buku, sofa, boks, counter
   (di-upscale 2x ke 32px).
3. **Top-Down Modern Office 2D Asset Pack** — nacl1234
   https://nacl1234.itch.io/top-down-modern-office-2d-asset-pack
   Dekorasi overlay: kulkas, mesin fotokopi, UPS, tower, palem, partisi.

> Catatan: periksa lisensi di tiap halaman sebelum rilis komersial.
> "Free sample" belum tentu sama lisensinya dengan paket penuhnya.

## Placeholder lama (tidak dipakai lagi, file disimpan)

- Atlas `assets/tiles/placeholder_tiles.png` dan sprite
  `assets/sprites/player1.png`, `player2.png`, `enemy.png` sudah
  digantikan art itch.io (lihat atas). File-nya masih ada di project
  sebagai cadangan; aman dihapus kalau tidak dibutuhkan.
- Tekstur cahaya (`light_soft.png`, `white.png`) dan ikon masih dipakai.

## Tools & pustaka pengembangan

- **Godot Engine** (https://godotengine.org) — MIT License.
- **Game-Dev-Agentic-Skills** by Divergent AI
  (https://github.com/thedivergentai/Game-Dev-Agentic-Skills) — LGPL-3.0.
  Dipakai sebagai referensi pola (TileMap, multiplayer, horror, revival);
  tidak ada kode dari repo tersebut yang disalin ke project ini.
- **Godot MCP** by Coding-Solo (https://github.com/Coding-Solo/godot-mcp)
  — MIT License. Tooling editor, bukan bagian runtime game.
- **Superpowers** by Obra (https://github.com/obra/superpowers) —
  metodologi pengembangan untuk coding agent, bukan bagian game.

## Desain map

- "Desain Map – Level 1 (Revisi)" — gambar referensi dari Edward
  (Lantai Kantor, Sayap Utama). Layout TileMap di project ini adalah
  adaptasi langsung dari gambar tersebut.

## Update TileMap Level 1 (Nov 2026)

Level 1 sekarang memakai atlas baru di `assets/tiles/lembur/` yang
dirakit dari 3 paket yang sama (tanpa aset baru dari luar):

- **Imersa Studios (Office Pixel Art Free)**: semua tile dinding
  (disusun ulang jadi sambungan/ujung), 5 lantai, meja kantor, kursi,
  tanaman, lemari arsip, dispenser, meja rapat, flipchart, layar
  proyektor, jam dinding, komputer, tumpukan kertas, tong sampah, meja samping, meja rapat vertikal, kursi samping, laptop, mug, lampu meja.
- **RubberStudio (Modern Office Tileset 16x16 Free Sample)**: 3 lantai
  (upscale 2×), rak buku, tumpukan boks, meja+monitor, meja kecil, sofa,
  tanaman besar, lemari kecil, printer, meja kopi, kursi, tanaman kecil
  (upscale 2×), whiteboard & jendela (ukuran asli).
- **nacl1234 (Modern Office 2D Props Pack)**: mesin fotokopi, kulkas,
  rak server (computer tower), UPS, kursi kerja, kursi rapat, meja sudut L, meja berdiri, meja panel, laci dorong, kursi bar, tanaman lebar, tanaman lidah mertua, tempat payung, tong sampah besar, printer kecil, serta hiasan kecil (stapler, kalkulator, tempat pena, buku catatan, headphone, kaktus, bingkai foto, organizer, botol, papan klip, kunci, selotip, map, USB, laptop, monitor, lampu meja, boks arsip, keranjang sampah), panel listrik, palem, pohon indoor,
  partisi, meja resepsionis, lemari tinggi, kabinet rendah, meja proyek,
  penghancur kertas, boks arsip, tempat sampah daur ulang, lampu lantai,
  lukisan, kamera CCTV, kursi tamu (diperkecil dari resolusi asli).

## Level 2 — Lobi Kantor (Nov 2026)

Level 2 memakai atlas baru di `assets/tiles/lobi/` yang dirakit dari 2 paket
berikut (paket aslinya tidak disertakan di project):

4. **Modern Office & School Interiors v1.0 (32x32)** — bubbabba
   https://bubbabba.itch.io
   Semua lantai, dinding gelap (wall top + wall face), dan hampir semua
   furnitur/dekorasi lobi: meja resepsionis, akuarium, kursi tunggu, lift,
   rak server, kafe, panggung, kursi acara, ruang rapat, rak buku, gudang,
   poster, jam, TV dinding, barang kecil.
   Lisensi (LICENSE.txt di paket): boleh untuk game komersial maupun
   non-komersial dan boleh diedit; TIDAK boleh dijual ulang/disebar sebagai
   aset, dipakai untuk melatih AI, atau dijadikan NFT. Kredit tidak wajib,
   tapi menyebut "bubbabba" dihargai.
5. **Modern Interiors – Free version (Interiors_free_32x32)** — LimeZu
   https://limezu.itch.io/moderninteriors
   Tangga darurat dan karpet "kolam" di atrium.
   Versi gratis ini untuk proyek non-komersial; cek ulang halaman itch.io
   sebelum game dirilis/dijual.

Rincian aset per area ada di `docs/sumber_aset_level2.png`.
