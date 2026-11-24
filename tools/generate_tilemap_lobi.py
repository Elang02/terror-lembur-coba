"""Generator Level 2 (Terror Lembur) - Lobi Kantor "Gelap Gulita" (72 x 46 tile).

CATATAN: file ini hanya arsip cara map Level 2 dibuat. TIDAK perlu dijalankan
untuk memainkan/mengedit Level 2 - semua tile sudah tersimpan di
scenes/level_2.tscn dan bisa diedit langsung di editor Godot.
Kalau dijalankan, file ini MENIMPA scenes/level_2.tscn dan assets/tiles/lobi/.

Cara pakai (butuh Python 3 + Pillow + numpy):
  python tools/generate_tilemap_lobi.py <folder project> <folder pack bubbabba> <png LimeZu Interiors_free_32x32>

Tileset utama: bubbabba - Modern Office & School Interiors (32x32).
Tambahan: LimeZu Modern Interiors Free (tangga + karpet kolam).
Sistem dinding bubbabba: wall top 32x32 (autotile 16 varian) + wall face 32x64 di 2 baris bawah dinding.
"""
import os, sys, json, base64, struct, random
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

T = 32
W, H = 72, 46
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
BB = (sys.argv[2] if len(sys.argv) > 2 else 'modern_office_school').rstrip('/') + '/'
J = json.load(open(BB + 'modern_office_school.json'))

def rgba(p): return Image.open(p).convert('RGBA')
def bbp(name, shadow=False):
    f = J['props'][name]['folder']
    return rgba(BB + ('props_with_shadow/' if shadow else 'props/') + f + '/' + name + '.png')
def single(name): return rgba(BB + 'tilesets/single/' + name + '.png')

# ------------------------------------------------------------------ helper gambar
def fit(im, w, h, xo=0, yo=0):
    """taruh gambar di kanvas w x h tile, rata bawah-tengah, tanpa resize (skala asli 32 px)."""
    im = im.crop(im.getbbox())
    assert im.width <= w*T and im.height <= h*T, (im.size, w, h)
    can = Image.new('RGBA', (w*T, h*T))
    can.alpha_composite(im, ((w*T - im.width)//2 + xo, h*T - im.height + yo))
    return can
def wm(im, w, y, xo=0):
    """barang tempel dinding: kanvas w x 2 tile (setinggi wall face), y = jarak dari atas face."""
    im = im.crop(im.getbbox())
    can = Image.new('RGBA', (w*T, 2*T))
    can.alpha_composite(im, ((w*T - im.width)//2 + xo, y))
    return can

PROPS, PACK, WALL_MOUNTED = {}, {}, set()
def P(name, im, pack='bubbabba', wall=False):
    PROPS[name] = (im, pack); PACK[name] = pack
    if wall: WALL_MOUNTED.add(name)
def B(name, w, h, xo=0, src=None): P(name, fit(bbp(src or name), w, h, xo))
def BW(name, w, y, xo=0, src=None): P(name, wm(bbp(src or name), w, y, xo), wall=True)

# --- bubbabba: lantai berdiri (ada collision)
for n, w, h in [
    ('reception_counter', 3, 2), ('brochure_rack', 1, 2), ('sign_in_stand', 1, 2), ('waiting_chairs_black', 2, 1),
    ('waiting_chairs_blue', 2, 1), ('lobby_sofa', 2, 1), ('lobby_chair', 1, 1), ('magazine_table', 1, 1),
    ('rope_barrier', 2, 1), ('rope_barrier_blue', 2, 1),
    ('executive_chair_black_front', 1, 2), ('task_chair_navy_back', 1, 2),
    ('vending_drinks', 2, 2), ('vending_snacks_blue', 2, 2), ('vending_snacks', 2, 2), ('kitchenette', 3, 2),
    ('office_fridge', 1, 2), ('office_fridge_steel', 1, 2), ('round_table_set', 2, 2), ('break_table_set', 2, 2),
    ('high_table_set', 2, 2), ('bar_stool', 1, 1), ('training_table_oak', 2, 1),
    ('janitor_cart', 2, 2), ('mop_bucket', 1, 2), ('wet_floor_sign', 1, 1), ('upright_vacuum', 1, 2),
    ('fire_extinguisher', 1, 1), ('sanitiser_stand', 1, 2), ('mail_cart', 2, 1), ('toner_boxes', 1, 1),
    ('paper_reams', 1, 1), ('fiddle_leaf_fig', 1, 2), ('monstera', 2, 2), ('snake_plant', 1, 2),
    ('planter_box', 2, 1), ('planter_box_oak', 2, 1), ('fish_tank', 2, 2),
    ('archive_shelf', 2, 2), ('supply_shelf', 2, 2), ('office_lockers', 2, 2), ('office_lockers_wide', 2, 2),
    ('tall_cupboard', 1, 2), ('tall_cupboard_grey', 1, 2), ('lateral_file', 2, 1), ('recycling_bins', 2, 1),
    ('umbrella_stand', 1, 1), ('waste_bin', 1, 1), ('coat_stand', 1, 2), ('low_bookshelf', 2, 1),
    ('desk_workstation_blue', 2, 2), ('av_rack', 1, 2), ('lounge_sofa_blue', 2, 1), ('lounge_chair_green', 1, 1),
    ('lounge_chair_orange', 1, 1), ('coffee_table_low', 2, 1), ('trophy_case', 2, 2)]:
    B(n, w, h)
# --- bubbabba: tempel dinding (tanpa collision). (nama, lebar tile, y dari atas face)
for n, w, y in [
    ('elevator', 2, 4), ('elevator_buttons', 1, 22), ('exit_sign', 1, 3), ('office_door_staff', 1, 14),
    ('office_door_office', 1, 14), ('window_blinds_night', 2, 8), ('poster_dream_big', 2, 12),
    ('poster_teamwork', 2, 12), ('poster_focus', 1, 12), ('employee_of_the_month', 1, 10),
    ('abstract_art_shapes', 2, 12), ('abstract_art_waves', 2, 12), ('wall_clock', 1, 8), ('wall_clock_white', 1, 8),
    ('wall_tv_report', 2, 10), ('wall_tv_call', 2, 10), ('wall_tv_slides', 2, 10), ('staff_notices', 2, 10),
    ('mug_rack', 1, 14), ('evacuation_map', 1, 14), ('fire_alarm', 1, 16), ('aed_cabinet', 1, 20),
    ('fire_extinguisher_wall', 1, 28), ('fire_hose_reel', 1, 18), ('first_aid_box', 1, 16),
    ('hanging_pothos', 1, 0), ('restroom_sign_men', 1, 18), ('restroom_sign_women', 1, 18)]:
    BW(n, w, y)
P('logo_resepsionis', wm(bbp('abstract_art_waves'), 2, 12, 16), wall=True)   # ditengahkan di atas meja
P('papan_karyawan', wm(bbp('employee_of_the_month'), 1, 12), wall=True)

# --- LimeZu (tangga & kolam)
LZ = rgba(sys.argv[3] if len(sys.argv) > 3 else 'Interiors_free_32x32.png')
P('lz_tangga', fit(LZ.crop((183, 31, 267, 161)), 3, 5, yo=-30), 'limezu')   # rata atas, menempel dinding
P('kolam', fit(LZ.crop((423, 355, 505, 477)).rotate(90, expand=True), 4, 3), 'limezu')

# --- benda kecil di atas meja / lantai (tanpa collision)
def onsurf(name, dx=0, dy=0):
    im = bbp(name, shadow=False); im = im.crop(im.getbbox())
    can = Image.new('RGBA', (T, T)); can.alpha_composite(im, ((T - im.width)//2 + dx, T - im.height + dy)); return can
SMALL = {}
for n, dx, dy in [('monitor_spreadsheet', 0, -6), ('monitor_inbox', 0, -6), ('monitor_asleep', 0, -6),
                  ('keyboard_slim_black', 0, -2), ('mug_teal', 7, -3), ('mug_navy', -6, -2), ('paper_cup_coffee', 5, -4),
                  ('coffee_machine', -4, -14), ('microwave', 2, -14), ('kettle', 4, -14), ('fruit_bowl', 0, -6),
                  ('folder_stack', 0, -6), ('clipboard', 0, -6), ('sticky_notes_yellow', 0, -8),
                  ('marking_pile', 0, -8), ('laptop_open', 0, -5), ('bankers_lamp', -6, -8)]:
    SMALL[n] = onsurf(n, dx, dy)

# ------------------------------------------------------------------ PROPS TAMBAHAN (ukuran otomatis dari JSON pack)
import math
def AUTO(name, xo=0):
    p = J['props'][name]; w, h = math.ceil(p['w']/T), math.ceil(p['h']/T)
    if p.get('kind') == 'wall': BW(name, w, max(0, (2*T - p['h'])//2 - 4), xo)
    else: B(name, w, h, xo)
for _n in ['partition_glass_64', 'phone_booth_blue', 'phone_booth_green', 'planter_divider', 'tripod_screen',
           'lectern_oak', 'chair_stack_blue', 'chair_stack_black', 'coffee_service', 'training_table', 'flip_chart_ideas',
           'mail_cubbies', 'copier_mfp', 'shredder', 'foosball_table', 'ping_pong_table', 'bean_bag_red', 'bean_bag_blue',
           'desk_l_white', 'lounge_sofa_green', 'low_bookshelf_long', 'certificate', 'dartboard', 'paper_towels',
           'stacking_chair_blue_back', 'stacking_chair_blue_left', 'stacking_chair_blue_right', 'stacking_chair_blue_front',
           'stacking_chair_orange_left', 'conference_set_walnut', 'conference_set_glass', 'glass_board', 'acoustic_panels',
           'room_panel_busy', 'mobile_whiteboard', 'flip_chart_graph', 'tv_cart',
           'cubicle_blue', 'cubicle_blue_mirrored', 'cubicle_green', 'cubicle_rust', 'desk_sit_stand', 'desk_l_oak',
           'desk_hot_white', 'partition_green_run', 'partition_blue_run', 'book_bins', 'cubbies_bins',
           'desk_workstation_green', 'task_chair_teal_back', 'floor_globe', 'upright_piano', 'pedestal_grey']:
    if _n not in PROPS: AUTO(_n)
P('bunting', wm(bbp('bunting'), 2, 2), wall=True)
P('exit_sign_tengah', wm(bbp('exit_sign'), 2, 3), wall=True)
P('logo_resepsionis', wm(bbp('abstract_art_waves'), 2, 12, 16), wall=True)
for n, dx, dy in [('speakerphone', 0, -14), ('notepad_and_pen', 4, -12), ('name_tents', 0, -12), ('laptop_slides', 0, -12),
                  ('mug_mustard', -6, -12), ('monitor_pair', 0, -8)]:
    SMALL[n] = onsurf(n, dx, dy)

# ------------------------------------------------------------------ DINDING
# 72 x 46 tile. Vestibul kaca menonjol 2 baris ke atas; atrium besar bertiang di tengah.
VOID = set((c, r) for r in (0, 1) for c in range(W) if not (30 <= c <= 41))
WALLS = set()
def hwall(r, c0, c1, skip=()):
    for c in range(c0, c1+1):
        if c not in skip: WALLS.add((c, r))
def vwall(c, r0, r1, skip=()):
    for r in range(r0, r1+1):
        if r not in skip: WALLS.add((c, r))
hwall(2, 0, 30); hwall(2, 41, 71); hwall(0, 30, 41); vwall(30, 0, 8); vwall(41, 0, 12)
vwall(0, 2, 45); vwall(71, 2, 45); hwall(45, 0, 71)
vwall(9, 2, 12); vwall(19, 2, 12)
hwall(12, 0, 21, skip=(1, 2, 16, 17))                     # bawah tangga / atas lobi lift / bawah ruang surat
vwall(11, 12, 21)                                         # sisi kanan lobi lift
hwall(12, 41, 71, skip=(45, 46, 57, 58, 69, 70))          # bawah security, ruang IT, lorong servis
vwall(52, 2, 12); vwall(62, 2, 12)
vwall(61, 12, 30, skip=(18, 19, 23, 24))                  # sisi kiri coworking
hwall(24, 0, 16, skip=(7, 8)); vwall(16, 24, 45, skip=(27, 28, 38, 39, 40))   # kafe
hwall(30, 35, 71, skip=(43, 44, 49, 50, 58, 59, 69, 70))  # atas r. rapat, pojok baca, gudang
vwall(35, 30, 45, skip=(38, 39, 40)); vwall(45, 30, 45); vwall(55, 30, 45)
PILLARS = [(22, 17), (22, 25), (30, 17), (30, 25), (42, 17), (42, 25), (50, 17), (50, 25)]
for p in PILLARS: WALLS.add(p)
EXTRA_FACE = [(30, 8)] + PILLARS

def isw(c, r): return (c, r) in WALLS or (c, r) in VOID or not (0 <= c < W and 0 <= r < H)
def face_style(c, r):
    if (c, r) in PILLARS: return 'wall_grey'
    if r == 0: return 'wall_glass'
    if r == 2:
        if c <= 8: return 'wall_grey'
        if c <= 18: return 'wall_block_cream'
        if c <= 29: return 'wall_slats_walnut'
        if c <= 51: return 'wall_charcoal'
        if c <= 61: return 'wall_grey'
        return 'wall_block_cream'
    if r == 8: return 'wall_grey'
    if r == 12:
        if c <= 10: return 'wall_wood_panel'
        if c <= 21: return 'wall_navy'
        if c <= 51: return 'wall_navy'
        if c <= 60: return 'wall_wood_panel'
        return 'wall_sage'
    if r == 24: return 'wall_brick_white'
    if r == 30:
        if c <= 44: return 'wall_felt_teal'
        if c <= 54: return 'wall_slats_oak'
        return 'wall_block_cream'
    return 'wall_greige'
FACES = {}
for (c, r) in sorted(WALLS):
    horiz = (c-1, r) in WALLS or (c+1, r) in WALLS
    if r+2 < H and not isw(c, r+1) and not isw(c, r+2) and (horiz or (c, r) in EXTRA_FACE):
        st = face_style(c, r); FACES[(c, r+1)] = (st, 0); FACES[(c, r+2)] = (st, 1)

def wall_top(c, r):
    n = 0
    if not isw(c, r-1): n |= 1
    if not isw(c+1, r): n |= 2
    if not isw(c, r+1): n |= 4
    if not isw(c-1, r): n |= 8
    return f'wall_top_dark_{n:02d}'

# ------------------------------------------------------------------ LANTAI
ROOMS = [
    ('Lobi Utama',      'floor_marble',           (12, 12, 60, 29)),
    ('Tangga Darurat',  'floor_tile_slate',       (1, 3, 8, 11)),
    ('Ruang Surat',     'floor_vct_grey',         (10, 3, 18, 11)),
    ('Resepsionis',     'floor_herringbone_oak',  (20, 3, 29, 11)),
    ('Vestibul Kaca',   'floor_marble',           (31, 1, 40, 11)),
    ('R. Security',     'floor_carpet_navy',      (42, 3, 51, 11)),
    ('Ruang IT',        'floor_access_panel',     (53, 3, 61, 11)),
    ('Lorong Servis',   'floor_concrete',         (63, 3, 70, 11)),
    ('Lobi Lift',       'floor_terrazzo_cream',   (1, 13, 10, 21)),
    ('Selasar',         'floor_vinyl_sheet_grey', (1, 22, 11, 23)),
    ('Coworking',       'floor_carpet_grey',      (62, 13, 70, 29)),
    ('Kafe & Game',     'floor_wood_oak',         (1, 25, 15, 44)),
    ('Area Acara',      'floor_marble',           (17, 30, 34, 44)),
    ('R. Rapat Tamu',   'floor_carpet_boardroom', (36, 31, 44, 44)),
    ('Pojok Baca',      'floor_parquet_oak',      (46, 31, 54, 44)),
    ('Gudang & Janitor','floor_concrete',         (56, 31, 70, 44)),
]
ZONES = [
    ('floor_carpet_charcoal', (23, 5, 28, 9)), ('floor_mat_entrance', (33, 3, 38, 4)),
    ('floor_terrazzo_grey', (31, 17, 40, 26)), ('floor_carpet_teal', (14, 18, 19, 22)),
    ('floor_carpet_fleck', (44, 19, 49, 23)), ('floor_terrazzo_brass', (24, 21, 28, 23)),
    ('floor_carpet_charcoal', (53, 15, 60, 18)),
    ('floor_carpet_boardroom_red', (18, 33, 33, 43)), ('floor_marble', (25, 34, 26, 43)),
    ('floor_checker_black_white', (1, 27, 6, 31)), ('floor_carpet_fleck_warm', (8, 40, 15, 44)),
    ('floor_vinyl_sheet_grey', (63, 40, 70, 44)), ('floor_carpet_green', (46, 42, 49, 44)),
]
OPENING_FLOOR = {(1, 12): 'floor_terrazzo_cream', (2, 12): 'floor_terrazzo_cream', (30, 11): 'floor_marble',
                 (69, 12): 'floor_carpet_grey', (70, 12): 'floor_carpet_grey', (7, 24): 'floor_wood_oak', (8, 24): 'floor_wood_oak',
                 (43, 30): 'floor_carpet_boardroom', (44, 30): 'floor_carpet_boardroom', (49, 30): 'floor_parquet_oak',
                 (50, 30): 'floor_parquet_oak', (58, 30): 'floor_concrete', (59, 30): 'floor_concrete',
                 (69, 30): 'floor_concrete', (70, 30): 'floor_concrete'}
for c in (16, 17, 45, 46, 57, 58): OPENING_FLOOR[(c, 12)] = 'floor_marble'
for r in (27, 28, 38, 39, 40): OPENING_FLOOR[(16, r)] = 'floor_marble'
for r in (38, 39, 40): OPENING_FLOOR[(35, r)] = 'floor_carpet_boardroom'
for r in (18, 19, 23, 24): OPENING_FLOOR[(61, r)] = 'floor_carpet_grey'
LABELS = {
    'Tangga Darurat': (4.5, 2.0), 'Ruang Surat': (14, 2.0), 'Resepsionis': (24.5, 2.0), 'Vestibul Kaca': (35.5, 7.6),
    'R. Security': (46.5, 2.0), 'Ruang IT': (57, 2.0), 'Lorong Servis': (66.5, 2.0), 'Lobi Lift': (5.5, 12.0),
    'Selasar': (6, 22.0), 'Galeri': (17, 12.0), 'Atrium Lobi Utama': (36, 27.6), 'Ruang Tunggu Tamu': (56.5, 12.0),
    'Coworking': (66, 12.0), 'Kafe & Game': (8, 24.0), 'Area Acara HUT': (25.5, 44.6), 'R. Rapat Tamu': (40, 30.0),
    'Pojok Baca': (50.5, 30.0), 'Gudang & Janitor': (63, 30.0),
}

# ------------------------------------------------------------------ PENEMPATAN
_kursi = []
for r in (35, 37, 39, 41):
    for c in list(range(19, 25)) + list(range(27, 33)):
        _kursi.append(('stacking_chair_blue_back', c, r))
_hilang = {(20, 35), (28, 37), (22, 39), (31, 39), (19, 41), (24, 41), (30, 35)}
_kursi = [k for k in _kursi if (k[1], k[2]) not in _hilang]
_kursi += [('stacking_chair_blue_left', 21, 36), ('stacking_chair_blue_front', 29, 38), ('stacking_chair_blue_right', 23, 40),
           ('stacking_chair_orange_left', 33, 36), ('stacking_chair_blue_front', 18, 38), ('stacking_chair_blue_left', 26, 42)]

PLACE = [
 # Tangga darurat
 ('lz_tangga', 1, 5), ('lz_tangga', 4, 5), ('fiddle_leaf_fig', 8, 4), ('waste_bin', 8, 9), ('planter_box_oak', 7, 11),
 # Ruang surat
 ('mail_cubbies', 10, 4), ('copier_mfp', 12, 4), ('shredder', 14, 5), ('paper_reams', 15, 5), ('tall_cupboard_grey', 18, 4),
 ('mail_cart', 11, 8), ('toner_boxes', 10, 10), ('recycling_bins', 13, 10), ('fiddle_leaf_fig', 18, 9),
 # Resepsionis
 ('fish_tank', 20, 4), ('brochure_rack', 22, 4), ('executive_chair_black_front', 25, 4), ('reception_counter', 24, 6),
 ('monstera', 28, 4), ('sign_in_stand', 28, 7), ('waiting_chairs_black', 20, 8), ('magazine_table', 22, 8),
 ('lobby_chair', 20, 10), ('coat_stand', 29, 9), ('umbrella_stand', 27, 10),
 # Vestibul kaca
 ('fiddle_leaf_fig', 31, 2), ('fiddle_leaf_fig', 40, 2), ('umbrella_stand', 32, 3), ('umbrella_stand', 39, 3),
 ('sanitiser_stand', 31, 4), ('partition_glass_64', 31, 6), ('partition_glass_64', 38, 6),
 ('rope_barrier', 31, 9), ('rope_barrier', 33, 9), ('rope_barrier', 37, 9), ('rope_barrier', 39, 9),
 # R. Security
 ('office_lockers', 42, 4), ('av_rack', 50, 4), ('av_rack', 51, 4), ('desk_workstation_blue', 45, 6),
 ('task_chair_navy_back', 46, 8), ('desk_l_white', 48, 7), ('lateral_file', 42, 10), ('snake_plant', 51, 9),
 # Ruang IT
 ('av_rack', 53, 4), ('av_rack', 54, 4), ('av_rack', 55, 4), ('av_rack', 53, 7), ('av_rack', 54, 7), ('av_rack', 55, 7),
 ('desk_workstation_green', 59, 5), ('task_chair_teal_back', 60, 7), ('toner_boxes', 61, 10), ('pedestal_grey', 58, 6),
 # Lorong servis
 ('tall_cupboard_grey', 63, 4), ('tall_cupboard', 64, 4), ('coat_stand', 70, 4), ('mail_cart', 66, 7),
 ('recycling_bins', 63, 10), ('upright_vacuum', 70, 8), ('sanitiser_stand', 68, 4),
 # Lobi lift + gerbang antrean karyawan
 ('fiddle_leaf_fig', 10, 15), ('waste_bin', 3, 15), ('sanitiser_stand', 1, 15), ('waiting_chairs_blue', 5, 18),
 ('rope_barrier_blue', 1, 21), ('rope_barrier_blue', 3, 21), ('rope_barrier_blue', 7, 21), ('rope_barrier_blue', 9, 21),
 # Selasar
 ('wet_floor_sign', 4, 23), ('waste_bin', 10, 22),
 # Galeri (kiri atas atrium)
 ('phone_booth_blue', 12, 13), ('phone_booth_green', 14, 13), ('trophy_case', 18, 14), ('trophy_case', 20, 14),
 # Atrium: plaza air mancur
 ('kolam', 34, 20), ('planter_box', 34, 19), ('planter_box', 36, 19), ('planter_box', 34, 23), ('planter_box', 36, 23),
 ('fiddle_leaf_fig', 33, 20), ('monstera', 38, 21), ('waiting_chairs_black', 35, 25), ('mop_bucket', 32, 23),
 ('wet_floor_sign', 31, 25), ('brochure_rack', 32, 13), ('sign_in_stand', 39, 13),
 # Atrium: lounge kiri, deret kursi tunggu, lounge kanan
 ('lounge_sofa_blue', 15, 18), ('coffee_table_low', 15, 20), ('lounge_chair_orange', 14, 20), ('lounge_chair_orange', 17, 20),
 ('lounge_chair_green', 16, 22), ('monstera', 19, 18), ('snake_plant', 13, 17),
 ('waiting_chairs_black', 24, 21), ('waiting_chairs_black', 26, 21), ('waiting_chairs_blue', 24, 23), ('waiting_chairs_blue', 26, 23),
 ('fiddle_leaf_fig', 28, 21), ('partition_green_run', 27, 15),
 ('lounge_sofa_green', 45, 19), ('coffee_table_low', 45, 21), ('lounge_chair_green', 44, 21), ('lounge_chair_green', 47, 21),
 ('planter_divider', 47, 18), ('snake_plant', 49, 22), ('planter_box', 47, 15), ('fiddle_leaf_fig', 44, 14),
 ('partition_blue_run', 40, 14),
 # Atrium bawah
 ('planter_divider', 26, 27), ('planter_divider', 46, 27), ('waste_bin', 33, 28), ('umbrella_stand', 40, 28),
 ('partition_green_run', 54, 26), ('recycling_bins', 56, 28),
 # Ruang tunggu tamu (kanan atrium)
 ('lobby_sofa', 53, 15), ('magazine_table', 54, 17), ('lobby_chair', 53, 17), ('lobby_chair', 55, 17), ('fish_tank', 59, 14),
 ('planter_box_oak', 53, 21), ('planter_box_oak', 55, 21), ('lobby_sofa', 53, 23), ('lobby_sofa', 56, 23),
 ('fiddle_leaf_fig', 60, 20), ('waiting_chairs_black', 57, 19),
 # Coworking: kubikel membentuk labirin
 ('cubicle_blue', 62, 15), ('cubicle_green', 65, 15), ('cubicle_blue_mirrored', 62, 20), ('cubicle_rust', 65, 20),
 ('cubicle_blue', 62, 25), ('cubicle_green', 65, 25), ('desk_sit_stand', 68, 16), ('desk_hot_white', 69, 21),
 ('desk_l_oak', 68, 26), ('snake_plant', 70, 13),
 # Kafe & game
 ('kitchenette', 1, 26), ('office_fridge', 4, 26), ('office_fridge_steel', 5, 26),
 ('vending_drinks', 9, 26), ('vending_snacks_blue', 11, 26), ('vending_snacks', 13, 26),
 ('training_table_oak', 2, 29), ('training_table_oak', 4, 29),
 ('bar_stool', 2, 30), ('bar_stool', 3, 30), ('bar_stool', 4, 30), ('bar_stool', 5, 30),
 ('round_table_set', 2, 33), ('break_table_set', 6, 33), ('high_table_set', 10, 30), ('round_table_set', 11, 33),
 ('break_table_set', 2, 37), ('round_table_set', 6, 37), ('high_table_set', 11, 37), ('fiddle_leaf_fig', 15, 30),
 ('snake_plant', 14, 34),
 ('lounge_sofa_blue', 2, 41), ('coffee_table_low', 2, 43), ('monstera', 5, 41),
 ('ping_pong_table', 9, 41), ('foosball_table', 13, 41), ('lounge_chair_orange', 9, 43), ('lounge_chair_orange', 11, 43),
 ('snake_plant', 15, 43),
 # Area acara HUT
 ('fiddle_leaf_fig', 18, 31), ('flip_chart_ideas', 20, 31), ('av_rack', 22, 31), ('tripod_screen', 25, 31),
 ('lectern_oak', 28, 31), ('av_rack', 30, 31), ('upright_piano', 32, 31),
 *_kursi,
 ('chair_stack_blue', 33, 42), ('chair_stack_blue', 34, 42), ('chair_stack_black', 17, 42),
 ('training_table', 19, 43), ('coffee_service', 21, 43), ('waste_bin', 34, 33),
 # R. rapat tamu
 ('flip_chart_graph', 36, 32), ('fiddle_leaf_fig', 36, 34), ('conference_set_walnut', 38, 35), ('conference_set_glass', 38, 40),
 ('tv_cart', 36, 42), ('mobile_whiteboard', 43, 41), ('snake_plant', 44, 35), ('stacking_chair_blue_right', 42, 38),
 # Pojok baca: rak rendah membentuk lorong
 ('low_bookshelf_long', 46, 35), ('low_bookshelf_long', 48, 35), ('low_bookshelf_long', 52, 35),
 ('low_bookshelf_long', 47, 38), ('low_bookshelf_long', 51, 38), ('low_bookshelf_long', 53, 38),
 ('low_bookshelf_long', 46, 41), ('low_bookshelf_long', 50, 41), ('book_bins', 52, 41),
 ('lounge_chair_green', 47, 33), ('lounge_chair_orange', 53, 33), ('bean_bag_blue', 46, 43), ('bean_bag_red', 48, 43),
 ('cubbies_bins', 53, 43), ('floor_globe', 51, 43),
 # Gudang & janitor
 ('supply_shelf', 64, 32), ('archive_shelf', 66, 32), ('archive_shelf', 56, 32),
 ('archive_shelf', 57, 36), ('archive_shelf', 59, 36), ('supply_shelf', 63, 36), ('supply_shelf', 65, 36),
 ('archive_shelf', 57, 40), ('office_lockers_wide', 60, 40), ('tall_cupboard_grey', 62, 40),
 ('janitor_cart', 66, 41), ('mop_bucket', 68, 41), ('wet_floor_sign', 65, 43), ('upright_vacuum', 70, 40),
 ('recycling_bins', 63, 43), ('toner_boxes', 56, 43), ('paper_reams', 59, 44), ('toner_boxes', 58, 43),
 ('paper_reams', 60, 44), ('toner_boxes', 61, 43), ('snake_plant', 70, 43),
]
WALL_PLACE = [
 ('fire_hose_reel', 1, 3), ('wall_clock', 4, 3), ('evacuation_map', 7, 3), ('fire_extinguisher_wall', 8, 3),
 ('wall_clock', 10, 3), ('staff_notices', 15, 3), ('office_door_staff', 17, 3),
 ('bunting', 20, 3), ('bunting', 22, 3), ('logo_resepsionis', 24, 3), ('bunting', 26, 3), ('wall_clock', 28, 3),
 ('hanging_pothos', 29, 3),
 ('exit_sign_tengah', 35, 1),
 ('wall_tv_report', 44, 3), ('wall_tv_call', 46, 3), ('wall_tv_slides', 48, 3), ('fire_alarm', 51, 3),
 ('wall_tv_report', 56, 3), ('evacuation_map', 58, 3), ('fire_alarm', 61, 3),
 ('fire_hose_reel', 65, 3), ('office_door_staff', 67, 3), ('aed_cabinet', 69, 3),
 ('elevator', 3, 13), ('elevator_buttons', 5, 13), ('elevator', 6, 13), ('elevator_buttons', 8, 13), ('elevator', 9, 13),
 ('poster_focus', 15, 13),
 ('employee_of_the_month', 18, 13), ('employee_of_the_month', 19, 13), ('employee_of_the_month', 20, 13), ('certificate', 21, 13),
 ('wall_tv_slides', 42, 13), ('hanging_pothos', 44, 13), ('abstract_art_shapes', 47, 13), ('poster_focus', 49, 13),
 ('wall_clock', 51, 13),
 ('staff_notices', 53, 13), ('evacuation_map', 55, 13), ('fire_alarm', 56, 13), ('certificate', 59, 13),
 ('wall_clock_white', 60, 13),
 ('window_blinds_night', 62, 13), ('poster_teamwork', 64, 13), ('wall_clock', 66, 13), ('glass_board', 67, 13),
 ('paper_towels', 6, 25), ('mug_rack', 2, 25), ('dartboard', 15, 25),
 ('room_panel_busy', 36, 31), ('glass_board', 37, 31), ('wall_tv_call', 39, 31), ('acoustic_panels', 41, 31),
 ('window_blinds_night', 46, 31), ('poster_focus', 48, 31), ('hanging_pothos', 51, 31), ('window_blinds_night', 52, 31),
 ('wall_clock', 54, 31),
 ('fire_hose_reel', 56, 31), ('office_door_staff', 61, 31), ('first_aid_box', 63, 31), ('fire_extinguisher_wall', 68, 31),
]
SMALL_PLACE_FIXED = [
 ('monitor_spreadsheet', 45, 7), ('monitor_inbox', 46, 7), ('monitor_asleep', 48, 8), ('mug_teal', 49, 8),
 ('monitor_pair', 59, 6), ('monitor_spreadsheet', 68, 17), ('laptop_open', 69, 22), ('monitor_inbox', 68, 27),
 ('coffee_machine', 1, 27), ('microwave', 2, 27), ('kettle', 3, 27),
 ('paper_cup_coffee', 3, 29), ('mug_navy', 5, 29), ('fruit_bowl', 10, 31),
 ('laptop_slides', 39, 36), ('speakerphone', 40, 36), ('name_tents', 41, 36), ('mug_mustard', 39, 41),
 ('paper_cup_coffee', 21, 43), ('folder_stack', 11, 8), ('laptop_open', 26, 6),
]
FLOOR_POOL = ['folder_stack', 'clipboard', 'sticky_notes_yellow', 'marking_pile', 'paper_cup_coffee', 'marking_pile']
N_CLUTTER = 75
SPAWNS = {'PlayerSpawn1': (3*T+16, 10*T+16), 'PlayerSpawn2': (5*T+16, 10*T+16)}
EXIT_POS = (36*T, 3*T+16)
LIGHTS = [
 (4.5, 7.5, 4.5, (255, 214, 150), 0.8), (14, 7, 4.5, (255, 210, 150), 0.55), (25, 7, 5.5, (255, 200, 130), 1.1),
 (21, 5, 2.2, (110, 200, 255), 0.7), (35.5, 5, 6.5, (190, 220, 255), 0.5), (35.5, 2.5, 3.2, (90, 255, 140), 0.65),
 (46.5, 5.5, 5, (110, 150, 255), 1.05), (57, 6, 4.5, (120, 255, 200), 0.55), (66.5, 7, 4, (255, 210, 150), 0.45),
 (5.5, 17, 5, (255, 214, 150), 0.75), (6, 22.8, 3.5, (255, 200, 140), 0.35), (17, 16, 4.5, (255, 225, 180), 0.55),
 (36, 21.5, 8, (255, 220, 170), 1.0), (16, 20, 4, (255, 205, 150), 0.6), (26, 22, 4, (255, 210, 160), 0.5),
 (46, 21, 4, (255, 205, 150), 0.6), (56.5, 19, 5, (255, 210, 160), 0.65), (60, 15, 2.2, (110, 200, 255), 0.6),
 (66, 21, 6, (200, 220, 255), 0.4), (11, 27.5, 3.5, (140, 180, 255), 0.75), (5, 31, 5, (255, 175, 100), 0.9),
 (8, 37, 5, (255, 175, 100), 0.6), (12, 42, 4, (255, 175, 100), 0.55), (26, 33, 4.5, (255, 240, 200), 0.9),
 (25.5, 39, 7, (255, 140, 110), 0.35), (40, 37, 5, (150, 190, 255), 0.6), (40, 32.5, 2.5, (120, 170, 255), 0.6),
 (50, 38, 5, (255, 220, 170), 0.5), (63, 37, 6.5, (255, 210, 150), 0.45), (66, 42, 3.5, (255, 220, 120), 0.4),
]
# ---- tambahan props biar atrium & ruangan padat (susah dihafal)
for n in ['easel_landscape', 'easel_abstract', 'lounge_chair_orange', 'high_table', 'round_table_oak', 'round_table_white']:
    if n not in PROPS: AUTO(n)
PLACE += [
 # bawah resepsionis & vestibul
 ('planter_box_oak', 23, 14), ('lobby_chair', 26, 14), ('lobby_chair', 28, 14), ('magazine_table', 27, 14),
 ('fiddle_leaf_fig', 33, 15), ('fiddle_leaf_fig', 38, 15), ('umbrella_stand', 31, 15),
 # kiri bawah atrium
 ('planter_divider', 18, 25), ('waiting_chairs_blue', 19, 28), ('lounge_chair_green', 21, 28), ('snake_plant', 20, 22),
 # antar tiang tengah
 ('round_table_oak', 25, 16), ('lounge_chair_green', 24, 16), ('lounge_chair_green', 26, 16), ('fiddle_leaf_fig', 29, 23),
 ('high_table', 28, 27), ('high_table', 32, 27), ('planter_box', 37, 27), ('snake_plant', 39, 25),
 # pameran karya karyawan (kanan bawah atrium)
 ('easel_landscape', 43, 25), ('easel_abstract', 45, 25), ('easel_landscape', 47, 25), ('floor_globe', 48, 27),
 ('planter_box_oak', 44, 28),
 ('lounge_chair_orange', 41, 22), ('lounge_chair_orange', 43, 23), ('magazine_table', 42, 23),
 # kanan atrium
 ('planter_divider', 52, 25), ('lobby_chair', 56, 27), ('lobby_chair', 55, 26), ('waste_bin', 57, 26),
 ('snake_plant', 51, 19), ('round_table_white', 58, 17), ('lounge_chair_green', 57, 17),
 # lobi lift
 ('waiting_chairs_blue', 2, 18), ('magazine_table', 4, 18), ('planter_box_oak', 8, 17), ('snake_plant', 9, 19),
 # kafe
 ('round_table_set', 7, 29), ('high_table_set', 13, 30), ('lounge_chair_orange', 6, 43),
 # gudang
 ('supply_shelf', 67, 36), ('toner_boxes', 62, 38), ('paper_reams', 64, 39), ('toner_boxes', 69, 38),
 # coworking
 ('snake_plant', 68, 19), ('waste_bin', 70, 28),
]
ZONES += [('floor_terrazzo_cream', (c-1, r-1, c+1, r+3)) for (c, r) in PILLARS]
ZONES += [('floor_carpet_charcoal', (35, 12, 36, 16))]

# ---- titik gameplay (penanda desain; nanti jadi node di Godot)
G_CAS = [(27, 5), (16, 5), (2, 17), (7, 28), (42, 33), (70, 15)]
G_KABEL = [(62, 34), (21, 33), (13, 29), (17, 16)]
G_TUGAS = [(29.5, 33), (68, 35), (40, 33.5), (14, 7), (7, 16), (23, 10), (36, 5), (47, 10)]
G_TUGAS_NO = ['1', '2', '3', '4', '5', '6', '7', '7']
G_HIDE = [(13, 14), (15, 14), (39.5, 38.5), (25.5, 5), (61, 41), (3.5, 30), (33.5, 42.5), (63, 16), (49, 36), (7, 14.5)]
G_KOMPUTER = (46, 7)
G_SATPAM = {
 'F1': [(2, 22.5), (12.5, 22.5), (21, 24), (23, 28.6), (41, 28.6), (52, 28.6), (57, 26), (57, 21), (52, 16), (43, 16),
        (31.5, 15.5), (23.5, 15.5), (21, 24)],
 'F2': [(16, 27.5), (8, 28.5), (8, 35.5), (15, 39), (25.5, 38), (34.5, 39), (37, 39), (42.5, 38.5), (43.5, 33), (43.5, 30), (49.5, 30),
        (49.5, 34), (51, 37), (49.5, 40), (49.5, 30), (52, 28.6), (61, 18.5), (70, 18.5), (70, 23.5), (61, 23.5)],
 'F3': [(16.5, 12.5), (16.5, 9), (12, 9), (16.5, 9), (16.5, 12.5), (45.5, 12.5), (45.5, 9.5), (43, 9), (45.5, 9.5),
        (45.5, 12.5), (57.5, 12.5), (57.5, 9), (57.5, 12.5), (58.5, 29), (58.5, 34.5), (68, 34.5), (68, 39), (61, 38.5)],
}

# ------------------------------------------------------------------ BUILD
def build():
    # dinding: wall top + potongan wall face
    wall_imgs, wall_key, wall_cells = [], {}, {}
    def addw(cell, im):
        k = im.tobytes()
        if k not in wall_key: wall_key[k] = len(wall_imgs); wall_imgs.append(im)
        wall_cells[cell] = wall_key[k]
    for (c, r) in WALLS:
        if 0 <= c < W and 0 <= r < H: addw((c, r), single(wall_top(c, r)))
    for (c, r), (st, half) in FACES.items():
        addw((c, r), single(st).crop((0, half*T, T, half*T+T)))
    # lantai
    floor = [[None]*W for _ in range(H)]
    for _, fl, (c0, r0, c1, r1) in ROOMS:
        for r in range(r0, r1+1):
            for c in range(c0, c1+1):
                if (c, r) not in WALLS: floor[r][c] = fl
    for fl, (c0, r0, c1, r1) in ZONES:
        for r in range(r0, r1+1):
            for c in range(c0, c1+1):
                if floor[r][c] and (c, r) not in FACES: floor[r][c] = fl
    for (c, r), fl in OPENING_FLOOR.items(): floor[r][c] = fl
    floor_order = sorted(set(f for row in floor for f in row if f))
    # props atlas
    used = []
    for n, _, _ in PLACE + WALL_PLACE:
        if n not in used: used.append(n)
    for n in SMALL:
        PROPS['kecil_' + n] = (SMALL[n], 'bubbabba'); WALL_MOUNTED.add('kecil_' + n); used.append('kecil_' + n)
    PC = 16; x = y = rowh = 0; pos = {}
    for n in used:
        im = PROPS[n][0]; w, h = im.width//T, im.height//T
        if x + w > PC: x = 0; y += rowh; rowh = 0
        pos[n] = (x, y); x += w; rowh = max(rowh, h)
    pat = Image.new('RGBA', (PC*T, (y+rowh)*T))
    for n in used: pat.alpha_composite(PROPS[n][0], (pos[n][0]*T, pos[n][1]*T))
    parr = np.array(pat); ptiles = {}
    for n in used:
        px, py = pos[n]; im = PROPS[n][0]
        for dy in range(im.height//T):
            for dx in range(im.width//T):
                cell = parr[(py+dy)*T:(py+dy+1)*T, (px+dx)*T:(px+dx+1)*T]
                if cell[..., 3].max() > 0: ptiles[(px+dx, py+dy)] = n not in WALL_MOUNTED
    props, dekor = {}, {}
    for n, c0, r0 in PLACE + WALL_PLACE:
        px, py = pos[n]; im = PROPS[n][0]
        tgt = dekor if n in WALL_MOUNTED else props
        for dy in range(im.height//T):
            for dx in range(im.width//T):
                if (px+dx, py+dy) in ptiles:
                    key = (c0+dx, r0+dy)
                    if key in tgt: print('OVERLAP', n, key, 'dengan', tgt[key][2], file=sys.stderr)
                    tgt[key] = (px+dx, py+dy, n)
    rnd = random.Random(7)
    sp = list(SMALL_PLACE_FIXED); taken = set((c, r) for _, c, r in sp)
    free = [(c, r) for r in range(H) for c in range(W) if floor[r][c] and (c, r) not in WALLS and (c, r) not in FACES
            and (c, r) not in props and (c, r) not in taken]
    rnd.shuffle(free)
    for (c, r) in free[:N_CLUTTER]: sp.append((rnd.choice(FLOOR_POOL), c, r))
    small = {}
    for n, c, r in sp:
        px, py = pos['kecil_' + n]; small[(c, r)] = (px, py, n)
    WC = 8
    watlas = Image.new('RGBA', (WC*T, ((len(wall_imgs)+WC-1)//WC)*T))
    for i, im in enumerate(wall_imgs): watlas.alpha_composite(im, ((i % WC)*T, (i//WC)*T))
    fat = Image.new('RGBA', (len(floor_order)*T, T))
    for i, n in enumerate(floor_order): fat.alpha_composite(single(n), (i*T, 0))
    return dict(walls=wall_cells, wall_imgs=wall_imgs, wall_coord=lambda i: (i % WC, i//WC), watlas=watlas,
                floor=floor, floor_order=floor_order, fat=fat, props=props, dekor=dekor, small=small,
                ptiles=ptiles, pat=pat, pos=pos, used=used, small_place=sp)

def check(G):
    walk = lambda c, r: (0 <= c < W and 0 <= r < H and G['floor'][r][c] and (c, r) not in G['walls']
                         and (c, r) not in G['props'])
    start = (SPAWNS['PlayerSpawn1'][0]//T, SPAWNS['PlayerSpawn1'][1]//T)
    seen = {start}; q = deque([start])
    while q:
        c, r = q.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c+dc, r+dr)
            if n not in seen and walk(*n): seen.add(n); q.append(n)
    probs = []
    for name, _, (c0, r0, c1, r1) in ROOMS:
        cells = [(c, r) for r in range(r0, r1+1) for c in range(c0, c1+1) if walk(c, r)]
        miss = [x for x in cells if x not in seen]
        if miss: probs.append(f'{name}: {len(miss)} sel tak terjangkau {miss[:8]}')
    ex = (EXIT_POS[0]//T, EXIT_POS[1]//T)
    if ex not in seen: probs.append(f'EXIT {ex} tak terjangkau')
    return probs, seen

def preview(G, path):
    img = Image.new('RGBA', (W*T, H*T), (14, 14, 22, 255))
    fo = G['floor_order']; fat, wat, pat = G['fat'], G['watlas'], G['pat']
    for r in range(H):
        for c in range(W):
            f = G['floor'][r][c]
            if f: i = fo.index(f); img.alpha_composite(fat.crop((i*T, 0, i*T+T, T)), (c*T, r*T))
    for (c, r), i in G['walls'].items():
        ax, ay = G['wall_coord'](i); img.alpha_composite(wat.crop((ax*T, ay*T, ax*T+T, ay*T+T)), (c*T, r*T))
    for grid in (G['dekor'], G['props'], G['small']):
        for (c, r), (ax, ay, n) in sorted(grid.items(), key=lambda k: (k[0][1], k[0][0])):
            img.alpha_composite(pat.crop((ax*T, ay*T, ax*T+T, ay*T+T)), (c*T, r*T))
    img.save(path)


# ================================================================== EKSPOR KE GODOT
# (TileSet .tres + atlas PNG + scenes/level_2.tscn)
B = sys.modules[__name__]
T = B.T; W, H = B.W, B.H
TDIR = 'assets/tiles/lobi'
rnd = random.Random(20261124)

G = B.build()
probs, seen = B.check(G)
assert not probs, probs

# ------------------------------------------------------------ walkable
def walk(c, r):
    return (0 <= c < W and 0 <= r < H and G['floor'][r][c] and (c, r) not in G['walls'] and (c, r) not in G['props'])

def nearest_walk(c, r):
    c0, r0 = int(round(c)), int(round(r))
    best = None
    for dr in range(-4, 5):
        for dc in range(-4, 5):
            cc, rr = c0 + dc, r0 + dr
            if walk(cc, rr) and (cc, rr) in seen:
                d = (cc - c) ** 2 + (rr - r) ** 2
                if best is None or d < best[0]: best = (d, cc, rr)
    assert best, (c, r)
    return best[1], best[2]

def px(c, r): return (c * T + 16, r * T + 16)
def jit(p, a=4): return (p[0] + rnd.randint(-a, a), p[1] + rnd.randint(-a, a))
def dist_to_walk(x, y):
    best = 1e9
    for (c, r) in seen:
        cx, cy = c * T + 16, r * T + 16
        best = min(best, ((cx - x) ** 2 + (cy - y) ** 2) ** .5)
    return best

def near_walk_px(x, y):
    best = None
    for (c, r) in seen:
        cx, cy = c * T + 16, r * T + 16
        d = ((cx - x) ** 2 + (cy - y) ** 2) ** .5
        if best is None or d < best[0]: best = (d, cx, cy)
    return best

def tarik(name, p, maxd=30):
    # posisi pixel titik interaksi; kalau terlalu jauh dari lantai yang bisa
    # diinjak, geser ke arah lantai terdekat (tetap di tepi props-nya)
    x, y = px(*p)
    d, cx, cy = near_walk_px(x, y)
    if d <= maxd: return (x, y)
    f = maxd / d
    nx, ny = round(cx + (x - cx) * f), round(cy + (y - cy) * f)
    report.append(f'{name}: digeser {d:.0f}px -> {maxd}px dari lantai')
    return (nx, ny)

# ------------------------------------------------------------ atlases + tileset
os.makedirs(os.path.join(OUT, TDIR), exist_ok=True)
G['watlas'].save(os.path.join(OUT, TDIR, 'dinding_lobi.png'))
G['fat'].save(os.path.join(OUT, TDIR, 'lantai_lobi.png'))
G['pat'].save(os.path.join(OUT, TDIR, 'props_lobi.png'))
FULL = 'PackedVector2Array(-16, -16, 16, -16, 16, 16, -16, 16)'
L = ['[gd_resource type="TileSet" load_steps=7 format=3]', '',
     f'[ext_resource type="Texture2D" path="res://{TDIR}/dinding_lobi.png" id="1_dinding"]',
     f'[ext_resource type="Texture2D" path="res://{TDIR}/lantai_lobi.png" id="2_lantai"]',
     f'[ext_resource type="Texture2D" path="res://{TDIR}/props_lobi.png" id="3_props"]', '',
     '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_dinding"]', 'resource_name = "dinding lobi"',
     'texture = ExtResource("1_dinding")', 'texture_region_size = Vector2i(32, 32)']
for i in range(len(G['wall_imgs'])):
    cx, cy = G['wall_coord'](i)
    L += [f'{cx}:{cy}/0 = 0', f'{cx}:{cy}/0/physics_layer_0/polygon_0/points = {FULL}']
L += ['', '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_lantai"]', 'resource_name = "lantai"',
      'texture = ExtResource("2_lantai")', 'texture_region_size = Vector2i(32, 32)']
L += [f'{i}:0/0 = 0' for i in range(len(G['floor_order']))]
L += ['', '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_props"]', 'resource_name = "props lobi"',
      'texture = ExtResource("3_props")', 'texture_region_size = Vector2i(32, 32)']
for (ax, ay), col in sorted(G['ptiles'].items(), key=lambda k: (k[0][1], k[0][0])):
    L.append(f'{ax}:{ay}/0 = 0')
    if col: L.append(f'{ax}:{ay}/0/physics_layer_0/polygon_0/points = {FULL}')
L += ['', '[resource]', 'resource_name = "TileSet Lobi (Level 2)"', 'tile_size = Vector2i(32, 32)',
      'physics_layer_0/collision_layer = 1', 'physics_layer_0/collision_mask = 0',
      'sources/0 = SubResource("TileSetAtlasSource_dinding")', 'sources/1 = SubResource("TileSetAtlasSource_lantai")',
      'sources/2 = SubResource("TileSetAtlasSource_props")', '']
open(os.path.join(OUT, TDIR, 'tileset_lobi.tres'), 'w').write('\n'.join(L))

def tmdata(cells):
    b = bytearray(b'\x00\x00')
    for x, y, s, ax, ay in sorted(cells, key=lambda t: (t[1], t[0])):
        b += struct.pack('<hhHHHH', x, y, s, ax, ay, 0)
    return base64.b64encode(bytes(b)).decode()

fo = G['floor_order']
floor_cells = [(c, r, 1, fo.index(G['floor'][r][c]), 0) for r in range(H) for c in range(W) if G['floor'][r][c]]
wall_cells = [(c, r, 0, *G['wall_coord'](i)) for (c, r), i in G['walls'].items()]
prop_cells = [(c, r, 2, ax, ay) for (c, r), (ax, ay, n) in G['props'].items()]
dek_cells = [(c, r, 2, ax, ay) for (c, r), (ax, ay, n) in G['dekor'].items()]
kecil_cells = [(c, r, 2, ax, ay) for (c, r), (ax, ay, n) in G['small'].items()]

# ------------------------------------------------------------ titik gameplay
report = []
SP = B.SPAWNS
spawn_p = {k: v for k, v in SP.items()}
for k, (x, y) in spawn_p.items(): assert walk(x // T, y // T), k

def snapped(name, c, r):
    cc, rr = nearest_walk(c, r)
    if (cc, rr) != (int(round(c)), int(round(r))): report.append(f'{name}: ({c},{r}) -> ({cc},{rr})')
    return cc, rr

ENEMY_SPAWN = [snapped(f'EnemySpawn{i+1}', *p) for i, p in enumerate(
    [(57, 21), (66, 8), (8, 35), (25, 41), (40, 40), (64, 38), (16, 14), (50, 34)])]
REVIVE = [snapped(f'Revive{i+1}', *p) for i, p in enumerate(
    [(13, 9), (44, 10), (58, 10), (3, 15), (30, 20), (66, 26), (12, 38), (52, 42)])]

def route(name, pts):
    out = []
    for i, (c, r) in enumerate(pts):
        cc, rr = nearest_walk(c, r)
        if out and out[-1] == (cc, rr): continue
        out.append((cc, rr))
    return out
F1 = route('F1', B.G_SATPAM['F1'][:-1])
F2 = route('F2', B.G_SATPAM['F2'])
F3 = route('F3', B.G_SATPAM['F3'])

# cek jarak interaksi
TASKS = [  # nama node, task_id, judul, game_type, requires_two, accent, posisi tile, catatan
    ('SpeakerPanggung', 'speaker', 'Matikan speaker panggung', 'email', False, (1.0, 0.55, 0.25), B.G_TUGAS[0],
     'Laporan 22.00. game_type SEMENTARA pakai email; nanti diganti minigame tahan E.'),
    ('Genset', 'genset', 'Nyalakan genset cadangan', 'simon', False, (0.95, 0.85, 0.3), B.G_TUGAS[1], 'Laporan 23.00'),
    ('TV_rapat', 'tv_rapat', 'Matikan TV ruang rapat', 'slides', False, (0.45, 0.7, 1.0), B.G_TUGAS[2], 'Laporan 00.00'),
    ('Fotokopi', 'fotokopi', 'Betulkan mesin fotokopi', 'copy', False, (0.8, 0.8, 0.85), B.G_TUGAS[3], 'Laporan 01.00'),
    ('LiftTurun', 'lift', 'Kunci panel lift', 'excel', False, (0.6, 1.0, 0.7), B.G_TUGAS[4],
     'Laporan 02.00. game_type SEMENTARA pakai excel; nanti diganti keypad.'),
    ('KunciCadangan', 'kunci_cadangan', 'Ambil kunci cadangan', 'archive', False, (1.0, 0.9, 0.5), B.G_TUGAS[5], 'Laporan 03.00'),
    ('PintuKaca', 'pintu_kaca', 'Buka kunci pintu kaca (berdua)', 'server', True, (0.4, 1.0, 0.6), B.G_TUGAS[6],
     'Laporan 04.00, co-op. Bagian ke-2 ada di marker PanelPintu_RSecurity.'),
]
for t in TASKS:
    x, y = px(*t[6]); d = dist_to_walk(x, y)
    assert d <= 50, (t[0], d)
HIDES = [('BilikTelepon', 'bilik_telepon_1'), ('BilikTelepon2', 'bilik_telepon_2'), ('KolongMejaRapat', 'kolong_meja_rapat'),
         ('balik_resepsionis', 'balik_resepsionis'), ('LokerGudang', 'loker_gudang'), ('BalikBarKafe', 'bar_kafe'),
         ('TumpukanKursi', 'tumpukan_kursi'), ('KubikelCoworking', 'kubikel_coworking'), ('RakPojokBaca', 'rak_pojok_baca'),
         ('Lift', 'lift')]
# Lift dipindah ke pintu lift kiri supaya tidak tumpang tindih dengan tugas LiftTurun
# (kalau terlalu dekat, tombol E selalu membuka tugas, bukan sembunyi).
G_HIDE = list(B.G_HIDE); G_HIDE[9] = (3.5, 14.5)
HIDE_PX = [tarik(nm, p, 28) for (nm, sid), p in zip(HIDES, G_HIDE)]
for (nm, _), hp in zip(HIDES, HIDE_PX):
    for t in TASKS:
        tx, ty = px(*t[6])
        assert ((tx - hp[0]) ** 2 + (ty - hp[1]) ** 2) ** .5 > 100, (nm, t[0])
CAS_NAMA = ['CasResepsionis', 'CasRuangSurat', 'CasLobiLift', 'CasKafe', 'CasRuangRapat', 'CasCoworking']
KABEL_NAMA = ['KabelGudang', 'KabelPanggung', 'KabelKafe', 'KabelGaleri']
CAS_PX = [tarik(nm, p, 24) for nm, p in zip(CAS_NAMA, B.G_CAS)]
KABEL_PX = [tarik(nm, p, 24) for nm, p in zip(KABEL_NAMA, B.G_KABEL)]
KOMP_PX = tarik('Komputer', B.G_KOMPUTER, 24)
EXIT = B.EXIT_POS
assert dist_to_walk(*EXIT) <= 40

# ------------------------------------------------------------ tulis .tscn
S = []
def a(*xs): S.extend(xs)
def node(name, typ=None, parent='.', inst=None, **_):
    h = f'[node name="{name}"'
    if typ: h += f' type="{typ}"'
    if parent is not None: h += f' parent="{parent}"'
    if inst: h += f' instance=ExtResource("{inst}")'
    a(h + ']')
def v2(p): return f'Vector2({p[0]:g}, {p[1]:g})'
def col(c, al=1): return f'Color({c[0]:g}, {c[1]:g}, {c[2]:g}, {al:g})'

exts = [('Script', 'res://scripts/level_2.gd', '1_lv2'), ('TileSet', f'res://{TDIR}/tileset_lobi.tres', '2_tiles'),
        ('Texture2D', 'res://assets/sprites/light_soft.png', '3_cahaya'),
        ('PackedScene', 'res://scenes/task_station.tscn', '4_tugas'), ('PackedScene', 'res://scenes/hiding_spot.tscn', '5_sembunyi'),
        ('PackedScene', 'res://scenes/exit_door.tscn', '6_keluar'), ('PackedScene', 'res://scenes/cage.tscn', '7_kurung'),
        ('PackedScene', 'res://scenes/revive_item.tscn', '8_bangkit'), ('PackedScene', 'res://scenes/enemy.tscn', '9_satpam'),
        ('PackedScene', 'res://scenes/hud.tscn', '10_hud')]
a(f'[gd_scene load_steps={len(exts)+1} format=4]', '')
for t, p, i in exts: a(f'[ext_resource type="{t}" path="{p}" id="{i}"]')
a('')
node('Level2', 'Node2D', parent=None); a('script = ExtResource("1_lv2")', '')
node('CanvasModulate', 'CanvasModulate'); a('color = Color(0.17, 0.17, 0.25, 1)', '')
for name, z, cells, desc in (('Lantai', -10, floor_cells, None), ('Dinding', -5, wall_cells, None),
                             ('hiasan_dinding', -4, dek_cells, 'poster, jam, papan, rak dinding (tanpa collision)'),
                             ('Props', 5, prop_cells, None), ('Props2', 6, kecil_cells, 'barang kecil: kertas, kardus, gelas dll (tanpa collision)')):
    node(name, 'TileMapLayer')
    if desc: a(f'editor_description = "{desc}"')
    a(f'z_index = {z}', f'tile_map_data = PackedByteArray("{tmdata(cells)}")', 'tile_set = ExtResource("2_tiles")', '')

# --- nama ruangan (panduan editor, disembunyikan saat main oleh script)
node('NamaRuangan', 'Node2D'); a('editor_description = "Panduan di editor saja. level_2.gd menyembunyikan node ini saat game jalan."', 'z_index = 30', '')
lab_names = {'Kafe & Game': 'LabelKafe', 'Atrium Lobi Utama': 'LabelAtrium', 'R. Security': 'security'}
k = 0
for n, (lc, lr) in B.LABELS.items():
    nm = lab_names.get(n)
    if not nm:
        nm = 'Label' if k == 0 else f'Label{k+1}'; k += 1
    x, y = lc * T + rnd.randint(-3, 3), lr * T + rnd.randint(-2, 2)
    wdt = 60 + rnd.choice([0, 0, 4, 10])
    node(nm, 'Label', 'NamaRuangan')
    a(f'offset_left = {x-wdt:.0f}.0', f'offset_top = {y-12:.0f}.0', f'offset_right = {x+wdt:.0f}.0', f'offset_bottom = {y+12:.0f}.0',
      'theme_override_colors/font_color = Color(1, 1, 1, 0.55)', 'theme_override_font_sizes/font_size = 13',
      f'text = "{n}"', 'horizontal_alignment = 1', '')

# --- lampu (dikelompokkan setengah-setengah, seperti dikerjakan bertahap)
LG = B.LIGHTS
LAMPU = [  # (index LIGHTS, nama, grup)
    (0, 'LampuTangga', None), (1, 'PointLight2D', None), (2, 'PointLight2D', 'Resepsionis'), (3, 'Akuarium', 'Resepsionis'),
    (5, 'ExitSign', None), (4, 'CahayaBulan', None), (6, 'LayarCCTV', None), (7, 'lampu_server', None),
    (8, 'PointLight2D2', None), (9, 'LampuLift', None), (10, 'PointLight2D3', None),
    (12, 'LampuAtrium', 'Atrium'), (11, 'PointLight2D', 'Atrium'), (13, 'PointLight2D2', 'Atrium'), (14, 'PointLight2D3', 'Atrium'),
    (15, 'PointLight2D4', 'Atrium'), (16, 'PointLight2D5', 'Atrium'), (17, 'TV', 'Atrium'),
    (18, 'LampuCoworking', None), (19, 'Vending', 'kafe'), (20, 'PointLight2D', 'kafe'), (21, 'PointLight2D2', 'kafe'),
    (22, 'PointLight2D3', 'kafe'), (23, 'SpotPanggung', None), (24, 'PointLight2D4', None),
    (25, 'PointLight2D', 'RuangRapat'), (26, 'LayarTV', 'RuangRapat'), (27, 'LampuBaca', None),
    (28, 'PointLight2D', 'Gudang'), (29, 'PointLight2D2', 'Gudang'),
]
assert sorted(i for i, _, _ in LAMPU) == list(range(len(LG)))
node('Lampu', 'Node2D'); a('')
made = set()
for i, nm, grp in LAMPU:
    if grp and grp not in made:
        node(grp, 'Node2D', 'Lampu'); a(''); made.add(grp)
    c, r, rad, rgb, en = LG[i]
    p = jit(px(c, r), 5)
    node(nm, 'PointLight2D', f'Lampu/{grp}' if grp else 'Lampu')
    a(f'position = {v2(p)}', f'color = {col(tuple(round(v/255, 2) for v in rgb))}', f'energy = {round(en, 2):g}',
      'texture = ExtResource("3_cahaya")', f'texture_scale = {round(rad/4, 2):g}', '')

# --- spawn
node('Spawn', 'Node2D'); a('')
for kk, p in spawn_p.items():
    node(kk, 'Marker2D', 'Spawn'); a(f'position = {v2(jit(p, 3))}', '')
node('musuh', 'Node2D', 'Spawn'); a('editor_description = "Titik muncul/teleport Satpam (dipakai AI musuh Level 1)."', '')
for i, (c, r) in enumerate(ENEMY_SPAWN):
    node(f'EnemySpawn{i+1}', 'Marker2D', 'Spawn/musuh'); a(f'position = {v2(jit(px(c, r), 4))}', '')
for i, (c, r) in enumerate(REVIVE):
    node(f'Revive{i+1}', 'Marker2D', 'Spawn'); a(f'position = {v2(jit(px(c, r), 4))}', '')

# --- titik cas (marker, script menyusul)
node('TitikCas', 'Node2D'); a('editor_description = "6 titik cas HP. Belum ada script: nanti dibaca level_2.gd untuk sistem baterai."', '')
for nm, p in zip(CAS_NAMA, CAS_PX):
    node(nm, 'Marker2D', 'TitikCas'); a(f'position = {v2(jit(p, 3))}', 'gizmo_extents = 16.0', '')

# --- jalur satpam (Line2D, digambar di editor)
node('JalurSatpam', 'Node2D'); a('editor_description = "Rute patroli Satpam. Geser titik Line2D di editor. Fase1 dipakai sekarang; Fase2 & Fase3 untuk sistem fase nanti. Disembunyikan saat main."', 'z_index = 25', '')
for nm, pts, c_, closed in (('Fase1', F1, (1, 0.35, 0.35), True), ('Fase2', F2, (0.35, 0.6, 1), False), ('Fase3', F3, (0.75, 0.45, 1), False)):
    node(nm, 'Line2D', 'JalurSatpam')
    flat = ', '.join(f'{c*T+16}, {r*T+16}' for c, r in pts)
    a(f'points = PackedVector2Array({flat})')
    if closed: a('closed = true')
    a('width = 4.0', f'default_color = {col(c_, 0.75)}', '')

# --- tugas
node('Tugas', 'Node2D'); a('')
for nm, tid, title, gt, two, acc, p, note in TASKS:
    node(nm, None, 'Tugas', '4_tugas')
    a(f'position = {v2(jit(px(*p), 2))}', f'editor_description = "{note}"', f'task_id = &"{tid}"', f'title = "{title}"', f'game_type = &"{gt}"')
    if two: a('requires_two = true')
    a(f'accent = {col(acc)}', '')
node('PanelPintu_RSecurity', 'Marker2D', 'Tugas')
a(f'position = {v2(jit(px(*B.G_TUGAS[7]), 3))}', 'editor_description = "Bagian ke-2 tugas Pintu Kaca (operator di R. Security). Belum dipakai script."', '')

# --- tempat sembunyi
node('TempatSembunyi', 'Node2D'); a('')
for (nm, sid), p in zip(HIDES, HIDE_PX):
    node(nm, None, 'TempatSembunyi', '5_sembunyi'); a(f'position = {v2(jit(p, 2))}', f'spot_id = &"{sid}"', '')

node('TitikKabel', 'Node2D'); a('editor_description = "4 titik kabel untuk error komputer. Belum ada script."', '')
for nm, p in zip(KABEL_NAMA, KABEL_PX):
    node(nm, 'Marker2D', 'TitikKabel'); a(f'position = {v2(jit(p, 3))}', '')

node('PintuKeluar', None, '.', '6_keluar'); a(f'position = {v2(EXIT)}', '')
node('Kurungan', None, '.', '7_kurung'); a(f'position = {v2(px(6, 9))}', '')
node('ItemBangkit', None, '.', '8_bangkit'); a(f'position = {v2(px(7, 9))}', '')
node('Pemain', 'Node2D'); a('')
sx = px(*ENEMY_SPAWN[0])
node('Satpam', None, '.', '9_satpam'); a(f'position = {v2(sx)}', '')
node('KomputerSecurity', 'Marker2D'); a(f'position = {v2(jit(KOMP_PX, 2))}', 'editor_description = "Komputer operator. Script komputer & denah menyusul."', 'gizmo_extents = 20.0', '')
node('HUD', None, '.', '10_hud'); a('')
open(os.path.join(OUT, 'scenes', 'level_2.tscn'), 'w').write('\n'.join(S))

print('tile: lantai', len(floor_cells), 'dinding', len(wall_cells), 'props', len(prop_cells), 'hiasan', len(dek_cells), 'kecil', len(kecil_cells))
print('F1', F1)
print('\n'.join(report) or 'tidak ada titik yang digeser')
