extends Node2D
## Level 2 — Lobi Kantor "Gelap Gulita" (TileMap 72 x 46).
##
## Dasarnya sama dengan level_1.gd (tugas lewat minigame, sembunyi,
## kurungan + item bangkit, pintu keluar, bintang), supaya Level 2 sudah
## bisa dimainkan dari awal. Bedanya:
## - node di scene boleh dikelompokkan bebas (dicari rekursif),
## - rute patroli Satpam dibaca dari Line2D JalurSatpam/Fase1,
## - lobi lebih gelap dan cahaya HP pemain lebih kecil,
## - tidak ada pintu terkunci; pintu kaca terbuka setelah semua tugas.
## Mekanik khusus Level 2 (baterai & titik cas, Satpam + Mantan Bos,
## komputer security, error kabel, jam 21.00-05.00) dikerjakan bertahap;
## node penandanya sudah ada di scene (TitikCas, TitikKabel, KomputerSecurity).

const PLAYER_SCENE: PackedScene = preload("res://scenes/player.tscn")
const LEVEL_ID: String = "level_2"
const PAR_TIME: float = 720.0
const TASK_RANGE: float = 62.0
const HIDE_RANGE: float = 50.0
const REVIVE_RANGE: float = 52.0
const CAGE_RANGE: float = 68.0
const EXIT_RADIUS: float = 72.0
const EXIT_HOLD: float = 1.5
const RESCUE_TIME: float = 2.0
const SOLO_REVIVE_DELAY: float = 12.0
const BASE_MODULATE: Color = Color(0.17, 0.17, 0.25)
const BLACKOUT_MODULATE: Color = Color(0.04, 0.04, 0.06)
const MAP_SIZE_TILES: Vector2i = Vector2i(72, 46)
## Skala Light pemain (bawaan player.tscn 1.4). 0.75 = radius kira-kira 3 tile,
## sesuai desain "HP menyala". Nanti sistem baterai yang mengubah nilai ini.
const PLAYER_LIGHT_SCALE: float = 0.75

var _level_active: bool = false
var _level_ended: bool = false
var _paused_for_disconnect: bool = false
var _level_time: float = 0.0
var _deaths_total: int = 0
var _exit_open: bool = false
var _exit_progress: float = 0.0
var _rescue_progress: float = 0.0
var _cage_peer: int = -1
var _revive_carrier: int = -1
var _revive_visible: bool = false
var _solo_revive_timer: float = -1.0
var _wipe_timer: float = -1.0
var _blackout_timer: float = 0.0
var _disconnect_timer: float = -1.0
var _progress_broadcast_timer: float = 0.0
var _flicker_time: float = 0.0

var _players: Dictionary = {}  # peer_id -> Player
var _holding: Dictionary = {}  # peer_id -> bool
var _tasks: Dictionary = {}  # StringName -> Dictionary node/progress/completed/game_type/requires_two
var _doors: Dictionary = {}  # String -> LockedDoor
var _spots: Array[Node2D] = []
var _lights: Array[PointLight2D] = []
var _light_base: Array[float] = []
var _light_phase: Array[float] = []
var _pathfinder: GridPathfinder = null
var _server_parts: Dictionary = {}  # peer_id -> true (bagian server selesai)
var minigame_layer: MinigameLayer = null

@onready var floor_layer: TileMapLayer = get_node_or_null("Lantai")
@onready var walls_layer: TileMapLayer = get_node_or_null("Dinding")
@onready var props_layer: TileMapLayer = get_node_or_null("Props")
@onready var canvas_modulate: CanvasModulate = get_node_or_null("CanvasModulate")
@onready var players_container: Node2D = get_node_or_null("Pemain")
@onready var tasks_container: Node2D = get_node_or_null("Tugas")
@onready var spots_container: Node2D = get_node_or_null("TempatSembunyi")
@onready var doors_container: Node2D = get_node_or_null("Pintu")  # Level 2 tidak punya pintu terkunci (boleh kosong)
@onready var spawns_container: Node2D = get_node_or_null("Spawn")
@onready var lights_container: Node2D = get_node_or_null("Lampu")
@onready var enemy: CharacterBody2D = get_node_or_null("Satpam")
@onready var exit_door: Node2D = get_node_or_null("PintuKeluar")
@onready var cage: Node2D = get_node_or_null("Kurungan")
@onready var revive_item: Node2D = get_node_or_null("ItemBangkit")
@onready var hud: CanvasLayer = get_node_or_null("HUD")


func _ready() -> void:
	add_to_group("LevelManager")
	randomize()
	_collect_level_nodes()
	_setup_pathfinder()
	_setup_enemy()
	_setup_lights()
	_sembunyikan_panduan_editor()
	_laporan_node()
	NetworkManager.peer_joined.connect(_on_peer_joined)
	NetworkManager.peer_left.connect(_on_peer_left)
	NetworkManager.host_disconnected.connect(_on_host_disconnected)
	_level_active = true
	if NetworkManager.is_server_authority():
		_spawn_player(NetworkManager.local_peer_id(), 0, true)
		var idx: int = 1
		for pid: int in NetworkManager.connected_ids:
			_spawn_player(pid, idx, true)
			idx += 1
	elif NetworkManager.mode == NetworkManager.Mode.CLIENT:
		rpc_id(1, "request_sync_rpc")
	minigame_layer = MinigameLayer.new()
	minigame_layer.name = "MinigameLayer"
	add_child(minigame_layer)
	_update_hud_static()


func is_level_running() -> bool:
	return _level_active and not _level_ended and not _paused_for_disconnect


func _collect_level_nodes() -> void:
	# Isi Tugas / TempatSembunyi boleh dikelompokkan dalam Node2D lain,
	# jadi dicari rekursif. Node yang bukan tugas (misal Marker2D catatan)
	# dilewati karena tidak punya properti task_id.
	for st: Node in _semua_anak(tasks_container):
		if not ("task_id" in st):
			continue
		_tasks[st.task_id] = {
			"node": st,
			"progress": 0.0,
			"completed": false,
			"game_type": st.game_type,
			"requires_two": st.requires_two,
		}
	for d: Node in _semua_anak(doors_container):
		if "door_id" in d:
			_doors[d.door_id] = d
	for s: Node in _semua_anak(spots_container):
		if s.has_method("set_occupied"):
			_spots.append(s)


func _semua_anak(root: Node) -> Array[Node]:
	# Semua turunan sebuah node (anak, cucu, dst).
	var out: Array[Node] = []
	if root == null:
		return out
	for c: Node in root.get_children():
		out.append(c)
		out.append_array(_semua_anak(c))
	return out


func _sembunyikan_panduan_editor() -> void:
	# NamaRuangan & JalurSatpam cuma panduan saat menyusun map di editor.
	# Saat game jalan disembunyikan supaya pemain tidak dapat "contekan".
	for nama: String in ["NamaRuangan", "JalurSatpam"]:
		var n: Node = get_node_or_null(nama)
		if n is CanvasItem:
			(n as CanvasItem).visible = false


func _laporan_node() -> void:
	# Cek cepat di panel Output: kalau angkanya 0, berarti ada node yang
	# namanya berubah / pindah folder.
	var rute: int = enemy.patrol_points.size() if enemy != null else 0
	print("[Level 2] tugas: %d | tempat sembunyi: %d | lampu: %d | titik cas: %d | titik kabel: %d | titik rute satpam: %d" % [
		_tasks.size(), _spots.size(), _lights.size(), _hitung_marker("TitikCas"), _hitung_marker("TitikKabel"), rute])


func _hitung_marker(nama_grup: String) -> int:
	var n: int = 0
	for c: Node in _semua_anak(get_node_or_null(nama_grup)):
		if c is Marker2D:
			n += 1
	return n


func _setup_pathfinder() -> void:
	if floor_layer == null or walls_layer == null:
		push_warning("Level 2: TileMapLayer Lantai/Dinding tidak ditemukan; pathfinding Satpam nonaktif.")
		return
	var blocked: Dictionary = {}
	for d: Node in _doors.values():
		for cell: Vector2i in d.door_cells:
			blocked[cell] = true
	_pathfinder = GridPathfinder.new()
	_pathfinder.setup(floor_layer, walls_layer, props_layer, blocked)


func _setup_enemy() -> void:
	if enemy == null:
		return
	enemy.pathfinder = _pathfinder
	enemy.patrol_points = _rute_satpam("Fase1")
	enemy.spawn_points = _marker_positions("EnemySpawn", 8, [Vector2i(57, 21), Vector2i(66, 8), Vector2i(8, 35), Vector2i(25, 41), Vector2i(40, 39), Vector2i(64, 38), Vector2i(16, 14), Vector2i(50, 34)])
	var start: Vector2 = _marker_pos("EnemySpawn1", Vector2i(57, 21))
	enemy.global_position = start


func _rute_satpam(nama_fase: String) -> Array[Vector2]:
	# Rute patroli digambar pakai Line2D di JalurSatpam, jadi bisa digeser
	# langsung di editor. Kalau Line2D-nya tidak ketemu, pakai rute cadangan.
	var out: Array[Vector2] = []
	var jalur: Node = get_node_or_null("JalurSatpam")
	var line: Line2D = null
	if jalur != null:
		line = jalur.get_node_or_null(nama_fase) as Line2D
	if line != null:
		for pt: Vector2 in line.points:
			out.append(line.to_global(pt))
	if out.size() < 2:
		out.clear()
		for cell: Vector2i in [Vector2i(2, 22), Vector2i(12, 22), Vector2i(21, 24), Vector2i(23, 29), Vector2i(41, 29), Vector2i(52, 29), Vector2i(57, 25), Vector2i(57, 21), Vector2i(52, 16), Vector2i(43, 16), Vector2i(32, 15), Vector2i(23, 15)]:
			out.append(Vector2(cell) * 32.0 + Vector2(16, 16))
	return out


func _setup_lights() -> void:
	# Lampu dikelompokkan per area (Lampu/Atrium, Lampu/kafe, ...), jadi rekursif.
	for l: Node in _semua_anak(lights_container):
		if l is PointLight2D:
			_lights.append(l)
			_light_base.append(l.energy)
			_light_phase.append(randf() * TAU)


func _marker_pos(marker_name: String, fallback_cell: Vector2i) -> Vector2:
	if spawns_container != null:
		# find_child: marker boleh ada di dalam folder (misal Spawn/musuh).
		var m: Node2D = spawns_container.find_child(marker_name, true, false) as Node2D
		if m != null:
			return m.global_position
	return Vector2(fallback_cell) * 32.0 + Vector2(16, 16)


func _marker_positions(prefix: String, count: int, fallbacks: Array) -> Array[Vector2]:
	var out: Array[Vector2] = []
	for i: int in range(count):
		out.append(_marker_pos(prefix + str(i + 1), fallbacks[i]))
	return out


func _revive_points() -> Array[Vector2]:
	return _marker_positions("Revive", 8, [Vector2i(13, 9), Vector2i(44, 10), Vector2i(58, 10), Vector2i(2, 15), Vector2i(30, 20), Vector2i(66, 24), Vector2i(13, 38), Vector2i(52, 42)])


# ---------------------------------------------------------------- spawn ---
func _spawn_player(peer_id: int, index: int, broadcast: bool) -> void:
	if _players.has(peer_id):
		return
	if players_container == null:
		return
	var p: CharacterBody2D = PLAYER_SCENE.instantiate()
	p.name = "Player_%d" % peer_id
	p.set_multiplayer_authority(peer_id)
	p.player_index = index + 1
	p.position = _marker_pos("PlayerSpawn%d" % (index + 1), Vector2i(3, 10) if index == 0 else Vector2i(5, 10))
	players_container.add_child(p)
	var lampu_hp: PointLight2D = p.get_node_or_null("Light") as PointLight2D
	if lampu_hp != null:
		lampu_hp.texture_scale = PLAYER_LIGHT_SCALE
	_players[peer_id] = p
	_holding[peer_id] = false
	if broadcast and NetworkManager.is_networked() and NetworkManager.is_server_authority():
		rpc("_spawn_player_rpc", peer_id, index)


@rpc("authority", "call_remote", "reliable")
func _spawn_player_rpc(peer_id: int, index: int) -> void:
	_spawn_player(peer_id, index, false)


func _on_peer_joined(peer_id: int) -> void:
	if not NetworkManager.is_server_authority() or _level_ended:
		return
	var index: int = 1 if _players.size() >= 1 else 0
	_spawn_player(peer_id, index, true)


func _on_peer_left(_peer_id: int) -> void:
	if _level_ended:
		return
	_paused_for_disconnect = true
	if hud != null:
		hud.show_disconnect("Partner terputus. Kembali ke menu untuk main lagi.")


func _on_host_disconnected() -> void:
	if _level_ended:
		return
	_paused_for_disconnect = true
	_disconnect_timer = 4.0
	if hud != null:
		hud.show_disconnect("Host terputus. Kembali ke menu...")


# ------------------------------------------------------------- sync RPC ---
@rpc("any_peer", "call_remote", "reliable")
func request_sync_rpc() -> void:
	if not NetworkManager.is_server_authority():
		return
	var sender: int = multiplayer.get_remote_sender_id()
	var players_data: Array = []
	for pid: int in _players.keys():
		var p: Node = _players[pid]
		players_data.append([pid, p.player_index - 1, p.global_position])
	var tasks_data: Dictionary = {}
	for tid: StringName in _tasks.keys():
		var t: Dictionary = _tasks[tid]
		tasks_data[tid] = [t["progress"], t["completed"]]
	var doors_data: Dictionary = {}
	for did: String in _doors.keys():
		doors_data[did] = _doors[did].is_open
	var data: Dictionary = {
		"players": players_data,
		"tasks": tasks_data,
		"doors": doors_data,
		"enemy_pos": enemy.global_position if enemy != null else Vector2.ZERO,
		"enemy_state": enemy.state if enemy != null else 0,
		"time": _level_time,
		"deaths": _deaths_total,
		"exit_open": _exit_open,
		"cage_peer": _cage_peer,
		"cage_pos": cage.global_position if cage != null else Vector2.ZERO,
		"revive_visible": _revive_visible,
		"revive_pos": revive_item.global_position if revive_item != null else Vector2.ZERO,
		"carrier": _revive_carrier,
	}
	rpc_id(sender, "_full_state_rpc", data)


@rpc("authority", "call_remote", "reliable")
func _full_state_rpc(data: Dictionary) -> void:
	for row: Array in data["players"]:
		_spawn_player(int(row[0]), int(row[1]), false)
		var p: Node = _players.get(int(row[0]))
		if p != null:
			p.global_position = row[2]
	var tasks_data: Dictionary = data["tasks"]
	for tid: String in tasks_data.keys():
		var key := StringName(tid)
		if _tasks.has(key):
			var t: Dictionary = _tasks[key]
			t["progress"] = float(tasks_data[tid][0])
			t["completed"] = bool(tasks_data[tid][1])
			t["node"].set_progress(t["progress"])
			if t["completed"]:
				t["node"].set_completed()
	var doors_data: Dictionary = data["doors"]
	for did: String in doors_data.keys():
		if bool(doors_data[did]) and _doors.has(did):
			_apply_door_open(did)
	if enemy != null:
		enemy.global_position = data["enemy_pos"]
		enemy.state = int(data["enemy_state"])
	_level_time = float(data["time"])
	_deaths_total = int(data["deaths"])
	_exit_open = bool(data["exit_open"])
	if _exit_open and exit_door != null:
		exit_door.set_locked(false)
	_cage_peer = int(data["cage_peer"])
	_revive_carrier = int(data["carrier"])
	_revive_visible = bool(data["revive_visible"])
	if _cage_peer != -1 and cage != null:
		cage.show_at(data["cage_pos"])
	if _revive_visible and revive_item != null:
		revive_item.show_at(data["revive_pos"])
	_update_hud_static()


# ------------------------------------------------------------ interaksi ---
func notify_interact_pressed(peer_id: int) -> void:
	if NetworkManager.is_server_authority():
		_handle_press(peer_id)
	else:
		rpc_id(1, "request_press_rpc", peer_id)


func notify_interact_released(peer_id: int) -> void:
	if NetworkManager.is_server_authority():
		_holding[peer_id] = false
	else:
		rpc_id(1, "request_release_rpc", peer_id)


@rpc("any_peer", "call_remote", "reliable")
func request_press_rpc(peer_id: int) -> void:
	if not NetworkManager.is_server_authority():
		return
	if multiplayer.get_remote_sender_id() != peer_id:
		return
	_handle_press(peer_id)


@rpc("any_peer", "call_remote", "reliable")
func request_release_rpc(peer_id: int) -> void:
	if not NetworkManager.is_server_authority():
		return
	if multiplayer.get_remote_sender_id() != peer_id:
		return
	_holding[peer_id] = false


func _handle_press(peer_id: int) -> void:
	if not is_level_running():
		return
	var p: Node = _players.get(peer_id)
	if p == null or p.is_downed:
		return
	if p.is_hidden:
		_set_player_hidden(p, false)
		return
	# 1) Selamatkan teman (butuh item; hold ditangani _physics_process).
	if _cage_peer != -1 and _revive_carrier == peer_id and p.global_position.distance_to(cage.global_position) <= CAGE_RANGE:
		_holding[peer_id] = true
		return
	# 2) Ambil item bangkit.
	if _revive_visible and revive_item != null and p.global_position.distance_to(revive_item.global_position) <= REVIVE_RANGE:
		_revive_visible = false
		_revive_carrier = peer_id
		revive_item.hide_item()
		p.apply_local_state(false, false, true)
		p.broadcast_state()
		if NetworkManager.is_networked():
			rpc("_revive_taken_rpc", peer_id)
		_show_message("Item Bangkit didapat! Selamatkan temanmu di kurungan.")
		return
	# 3) Kerjakan tugas (buka minigame di layar pemain itu).
	var tid: StringName = _nearest_task(p.global_position)
	if tid != StringName(""):
		_try_open_minigame(peer_id, tid)
		return
	# 4) Sembunyi.
	if _nearest_spot(p.global_position) != null:
		_set_player_hidden(p, true)
		return


@rpc("authority", "call_remote", "reliable")
func _revive_taken_rpc(peer_id: int) -> void:
	_revive_visible = false
	_revive_carrier = peer_id
	if revive_item != null:
		revive_item.hide_item()


func _set_player_hidden(p: Node, hidden: bool) -> void:
	p.apply_local_state(p.is_downed, hidden, p.carrying_revive)
	p.broadcast_state()


func _nearest_task(pos: Vector2) -> StringName:
	for tid: StringName in _tasks.keys():
		var t: Dictionary = _tasks[tid]
		if t["completed"]:
			continue
		if pos.distance_to((t["node"] as Node2D).global_position) <= TASK_RANGE:
			return tid
	return StringName("")


func _nearest_spot(pos: Vector2) -> Node2D:
	for s: Node2D in _spots:
		if pos.distance_to(s.global_position) <= HIDE_RANGE:
			return s
	return null


# ------------------------------------------------------------ minigame ---
func get_local_player() -> Node:
	return _players.get(NetworkManager.local_peer_id())


func task_position(tid: StringName) -> Vector2:
	if _tasks.has(tid):
		return (_tasks[tid]["node"] as Node2D).global_position
	return Vector2.ZERO


func is_task_completed(tid: StringName) -> bool:
	return _tasks.has(tid) and bool(_tasks[tid]["completed"])


func set_local_minigame_open(open: bool) -> void:
	var p: Node = get_local_player()
	if p == null:
		return
	p.minigame_open = open
	if open:
		p.velocity = Vector2.ZERO
		p.interact_held = false


func open_minigame_for_local(tid: StringName) -> void:
	if minigame_layer == null or not _tasks.has(tid):
		return
	minigame_layer.open_minigame(tid, _tasks[tid]["game_type"])


func _try_open_minigame(peer_id: int, tid: StringName) -> void:
	var t: Dictionary = _tasks[tid]
	if t["requires_two"] and _server_needed() > 1:
		var in_range: int = 0
		for pid: int in _players.keys():
			var p: Node = _players[pid]
			if p.is_downed or p.is_hidden:
				continue
			if p.global_position.distance_to((t["node"] as Node2D).global_position) <= TASK_RANGE:
				in_range += 1
		if in_range < 2:
			_notice_to(peer_id, "Butuh 2 pemain di dekat server untuk mulai!")
			return
	if peer_id == NetworkManager.local_peer_id():
		open_minigame_for_local(tid)
	elif NetworkManager.is_networked():
		rpc_id(peer_id, "_open_minigame_rpc", String(tid))


@rpc("authority", "call_remote", "reliable")
func _open_minigame_rpc(tid: String) -> void:
	open_minigame_for_local(StringName(tid))


func submit_minigame_result(tid: StringName) -> void:
	if NetworkManager.is_server_authority():
		_handle_minigame_result(NetworkManager.local_peer_id(), tid)
	elif NetworkManager.is_networked():
		rpc_id(1, "request_minigame_result_rpc", NetworkManager.local_peer_id(), String(tid))


@rpc("any_peer", "call_remote", "reliable")
func request_minigame_result_rpc(peer_id: int, tid: String) -> void:
	if not NetworkManager.is_server_authority():
		return
	if multiplayer.get_remote_sender_id() != peer_id:
		return
	_handle_minigame_result(peer_id, StringName(tid))


func _handle_minigame_result(peer_id: int, tid: StringName) -> void:
	if not _tasks.has(tid) or bool(_tasks[tid]["completed"]):
		return
	var p: Node = _players.get(peer_id)
	if p == null or p.is_downed or p.is_hidden:
		return
	if p.global_position.distance_to((_tasks[tid]["node"] as Node2D).global_position) > TASK_RANGE + 30.0:
		return
	if not bool(_tasks[tid]["requires_two"]):
		_complete_task(tid)
		return
	# Tugas co-op: bank bagian pemain ini, selesaikan kalau semua
	# bagian terkumpul DAN semua pemain berada di dekat stasiun.
	_server_parts[peer_id] = true
	if _server_parts_ready(tid):
		_complete_task(tid)
	else:
		_notice_to(peer_id, "Bagianmu selesai! Menunggu partner menyelesaikan bagiannya.")


func _server_needed() -> int:
	# Solo: 1 pemain cukup (kalau tidak, game tidak bisa tamat solo).
	return 1 if not NetworkManager.is_networked() else 2


func _server_parts_ready(tid: StringName) -> bool:
	if _server_parts.size() < _server_needed():
		return false
	var station_pos: Vector2 = (_tasks[tid]["node"] as Node2D).global_position
	for pid: int in _players.keys():
		var p: Node = _players[pid]
		if p.is_downed or p.is_hidden:
			return false
		if p.global_position.distance_to(station_pos) > TASK_RANGE + 30.0:
			return false
	return true


func report_minigame_progress(tid: StringName, progress: float) -> void:
	if NetworkManager.is_server_authority():
		_apply_task_progress(tid, progress)
	elif NetworkManager.is_networked():
		rpc_id(1, "report_minigame_progress_rpc", String(tid), progress)


@rpc("any_peer", "call_remote", "unreliable")
func report_minigame_progress_rpc(tid: String, progress: float) -> void:
	if not NetworkManager.is_server_authority():
		return
	_apply_task_progress(StringName(tid), progress)


func _apply_task_progress(tid: StringName, progress: float) -> void:
	if not _tasks.has(tid) or bool(_tasks[tid]["completed"]):
		return
	var t: Dictionary = _tasks[tid]
	t["progress"] = clampf(progress, 0.0, 1.0)
	t["node"].set_progress(t["progress"])


func _notice_to(peer_id: int, text: String) -> void:
	if peer_id == NetworkManager.local_peer_id():
		_show_message(text)
	elif NetworkManager.is_networked():
		rpc_id(peer_id, "_notice_rpc", text)


@rpc("authority", "call_remote", "reliable")
func _notice_rpc(text: String) -> void:
	_show_message(text)


# -------------------------------------------------------------- physics ---
func _physics_process(delta: float) -> void:
	if _level_active and not _level_ended:
		_level_time += delta
	if _disconnect_timer > 0.0:
		_disconnect_timer -= delta
		if _disconnect_timer <= 0.0:
			_go_to_menu()
			return
	if not NetworkManager.is_server_authority():
		return
	if not is_level_running():
		return
	_tick_tasks(delta)
	_tick_rescue(delta)
	_tick_exit(delta)
	_tick_revive_timers(delta)
	_progress_broadcast_timer -= delta
	if _progress_broadcast_timer <= 0.0:
		_progress_broadcast_timer = 0.25
		_broadcast_progress()


func _tick_tasks(_delta: float) -> void:
	# Tugas biasa selesai lewat minigame (submit_minigame_result).
	# Di sini hanya menyelesaikan tugas co-op yang bagiannya sudah
	# terkumpul begitu semua pemain kembali berkumpul di stasiun.
	for tid: StringName in _tasks.keys():
		var t: Dictionary = _tasks[tid]
		if t["completed"] or not bool(t["requires_two"]):
			continue
		if _server_parts_ready(tid):
			_complete_task(tid)


func _complete_task(tid: StringName) -> void:
	var t: Dictionary = _tasks[tid]
	t["completed"] = true
	t["progress"] = 1.0
	t["node"].set_completed()
	if NetworkManager.is_networked():
		rpc("_task_completed_rpc", String(tid))
	_show_message("Tugas selesai: %s (%d/%d)" % [t["node"].title, _completed_count(), _tasks.size()])
	if _completed_count() >= _tasks.size() and not _exit_open:
		_exit_open = true
		if exit_door != null:
			exit_door.set_locked(false)
		if NetworkManager.is_networked():
			rpc("_exit_opened_rpc")
		_show_message("Semua laporan beres! Pintu kaca terbuka, kabur berdua lewat Vestibul!")


@rpc("authority", "call_remote", "reliable")
func _task_completed_rpc(tid: String) -> void:
	var key := StringName(tid)
	if _tasks.has(key):
		var t: Dictionary = _tasks[key]
		t["completed"] = true
		t["progress"] = 1.0
		t["node"].set_completed()


@rpc("authority", "call_remote", "reliable")
func _exit_opened_rpc() -> void:
	_exit_open = true
	if exit_door != null:
		exit_door.set_locked(false)
	_show_message("Semua laporan beres! Pintu kaca terbuka, kabur berdua lewat Vestibul!")


func _broadcast_progress() -> void:
	if not NetworkManager.is_networked():
		return
	var data: Dictionary = {}
	for tid: StringName in _tasks.keys():
		var t: Dictionary = _tasks[tid]
		if not t["completed"] and float(t["progress"]) > 0.0:
			data[String(tid)] = float(t["progress"])
	rpc("_tasks_progress_rpc", data, _exit_progress, _rescue_progress)


@rpc("authority", "call_remote", "unreliable")
func _tasks_progress_rpc(data: Dictionary, exit_progress: float, rescue_progress: float) -> void:
	for tid: String in data.keys():
		var key := StringName(tid)
		if _tasks.has(key):
			var t: Dictionary = _tasks[key]
			t["progress"] = float(data[tid])
			t["node"].set_progress(t["progress"])
	_exit_progress = exit_progress
	_rescue_progress = rescue_progress
	if exit_door != null:
		exit_door.set_progress(_exit_progress)
	if cage != null and cage.visible:
		cage.set_rescue_progress(_rescue_progress)


func _tick_rescue(delta: float) -> void:
	if _cage_peer == -1 or _revive_carrier == -1:
		_rescue_progress = 0.0
		return
	var carrier: Node = _players.get(_revive_carrier)
	if carrier == null or carrier.is_downed or carrier.is_hidden:
		_rescue_progress = maxf(0.0, _rescue_progress - delta * 0.5)
		return
	if bool(_holding.get(_revive_carrier, false)) and carrier.global_position.distance_to(cage.global_position) <= CAGE_RANGE:
		_rescue_progress += delta / RESCUE_TIME
		if cage != null:
			cage.set_rescue_progress(_rescue_progress)
		if _rescue_progress >= 1.0:
			_revive_player(_cage_peer)
	else:
		_rescue_progress = maxf(0.0, _rescue_progress - delta * 0.5)
		if cage != null:
			cage.set_rescue_progress(_rescue_progress)


func _tick_exit(delta: float) -> void:
	if not _exit_open or exit_door == null:
		return
	var expected: int = 2 if NetworkManager.is_networked() else 1
	var inside: int = 0
	for pid: int in _players.keys():
		var p: Node = _players[pid]
		if p.is_downed:
			continue
		if p.global_position.distance_to(exit_door.global_position) <= EXIT_RADIUS:
			inside += 1
	if inside >= expected:
		_exit_progress += delta / EXIT_HOLD
	else:
		_exit_progress = maxf(0.0, _exit_progress - delta)
	exit_door.set_progress(_exit_progress)
	if _exit_progress >= 1.0:
		_finish_level(true)


func _tick_revive_timers(delta: float) -> void:
	if _solo_revive_timer > 0.0:
		_solo_revive_timer -= delta
		if _solo_revive_timer <= 0.0 and _cage_peer != -1:
			_show_message("Kamu berhasil keluar dari kurungan (mode solo).")
			_revive_player(_cage_peer)
	if _wipe_timer > 0.0:
		_wipe_timer -= delta
		if _wipe_timer <= 0.0:
			_finish_level(false)


# --------------------------------------------------------- pintu & cage ---
func _open_door(door_id: String) -> void:
	if not _doors.has(door_id) or _doors[door_id].is_open:
		return
	_apply_door_open(door_id)
	if NetworkManager.is_networked():
		rpc("_door_opened_rpc", door_id)
	_show_message("Pintu %s terbuka!" % door_id)


func _apply_door_open(door_id: String) -> void:
	var d: Node = _doors[door_id]
	d.open_door()
	if _pathfinder != null:
		for cell: Vector2i in d.door_cells:
			_pathfinder.set_door_blocked(cell, false)


@rpc("authority", "call_remote", "reliable")
func _door_opened_rpc(door_id: String) -> void:
	if _doors.has(door_id):
		_apply_door_open(door_id)


func on_player_caught(peer_id: int) -> void:
	if not NetworkManager.is_server_authority() or _level_ended:
		return
	var p: Node = _players.get(peer_id)
	if p == null or p.is_downed:
		return
	_deaths_total += 1
	p.apply_local_state(true, false, false)
	p.grant_iframes(0.0)
	p.broadcast_state()
	_cage_peer = peer_id
	_rescue_progress = 0.0
	if cage != null:
		cage.show_at(p.global_position)
	var revive_pos: Vector2 = Vector2.ZERO
	if not _revive_visible and _revive_carrier == -1 and revive_item != null:
		var pts: Array[Vector2] = _revive_points()
		revive_pos = pts[randi() % pts.size()]
		_revive_visible = true
		revive_item.show_at(revive_pos)
	if NetworkManager.is_networked():
		rpc("_player_downed_rpc", peer_id, p.global_position, revive_pos, _revive_visible)
	_show_message("P%d tertangkap! Cari Item Bangkit lalu selamatkan dia!" % p.player_index)
	if _all_players_downed():
		if NetworkManager.mode == NetworkManager.Mode.SOLO:
			_solo_revive_timer = SOLO_REVIVE_DELAY
		else:
			_wipe_timer = 1.5


@rpc("authority", "call_remote", "reliable")
func _player_downed_rpc(peer_id: int, cage_pos: Vector2, revive_pos: Vector2, revive_visible: bool) -> void:
	_cage_peer = peer_id
	_rescue_progress = 0.0
	if cage != null:
		cage.show_at(cage_pos)
	_revive_visible = revive_visible
	if revive_visible and revive_item != null:
		revive_item.show_at(revive_pos)
	var p: Node = _players.get(peer_id)
	if p != null:
		_show_message("P%d tertangkap! Cari Item Bangkit lalu selamatkan dia!" % p.player_index)


func _revive_player(peer_id: int) -> void:
	var p: Node = _players.get(peer_id)
	if p == null:
		return
	var pos: Vector2 = cage.global_position if cage != null else p.global_position
	p.global_position = pos + Vector2(20, 0)
	p.velocity = Vector2.ZERO
	p.apply_local_state(false, false, false)
	p.grant_iframes(2.0)
	p.broadcast_state()
	if _revive_carrier != -1:
		var carrier: Node = _players.get(_revive_carrier)
		if carrier != null and carrier != p:
			carrier.apply_local_state(carrier.is_downed, carrier.is_hidden, false)
			carrier.broadcast_state()
	_revive_carrier = -1
	_revive_visible = false
	_cage_peer = -1
	_rescue_progress = 0.0
	_solo_revive_timer = -1.0
	if cage != null:
		cage.hide_cage()
	if revive_item != null:
		revive_item.hide_item()
	if NetworkManager.is_networked():
		rpc("_player_revived_rpc", peer_id, p.global_position)
	_show_message("P%d bebas dari kurungan!" % p.player_index)


@rpc("authority", "call_remote", "reliable")
func _player_revived_rpc(peer_id: int, pos: Vector2) -> void:
	var p: Node = _players.get(peer_id)
	if p != null:
		p.global_position = pos
		p.velocity = Vector2.ZERO
		_show_message("P%d bebas dari kurungan!" % p.player_index)
	_revive_carrier = -1
	_revive_visible = false
	_cage_peer = -1
	_rescue_progress = 0.0
	if cage != null:
		cage.hide_cage()
	if revive_item != null:
		revive_item.hide_item()


func _all_players_downed() -> bool:
	if _players.is_empty():
		return false
	for pid: int in _players.keys():
		if not _players[pid].is_downed:
			return false
	return true


# -------------------------------------------------------------- blackout ---
func trigger_blackout_pulse() -> void:
	_apply_blackout_local()
	if NetworkManager.is_networked():
		rpc("_blackout_rpc")


@rpc("authority", "call_remote", "reliable")
func _blackout_rpc() -> void:
	_apply_blackout_local()


func _apply_blackout_local() -> void:
	_blackout_timer = 1.6
	if hud != null:
		hud.flash_blackout()
	var local_p: Node = _players.get(NetworkManager.local_peer_id())
	if local_p != null:
		local_p.add_trauma(0.55)
	_show_message("Lampu darurat padam sesaat... langkah Satpam tidak terdengar lagi.")


# ---------------------------------------------------------------- ending ---
func _finish_level(success: bool) -> void:
	if _level_ended:
		return
	_level_ended = true
	var stars: int = 0
	var ending: String = "GAGAL"
	if success:
		ending = "Happy Ending" if _deaths_total == 0 else "Bad Ending"
		if _level_time <= PAR_TIME and _deaths_total == 0:
			stars = 3
		elif _level_time <= PAR_TIME * 1.5 or _deaths_total <= 1:
			stars = 2
		else:
			stars = 1
	_apply_finished(success, stars, ending)
	if NetworkManager.is_networked():
		rpc("_level_finished_rpc", success, stars, ending, _level_time, _deaths_total)


@rpc("authority", "call_remote", "reliable")
func _level_finished_rpc(success: bool, stars: int, ending: String, time_sec: float, deaths: int) -> void:
	_level_time = time_sec
	_deaths_total = deaths
	_level_ended = true
	_apply_finished(success, stars, ending)


func _apply_finished(success: bool, stars: int, ending: String) -> void:
	if minigame_layer != null:
		minigame_layer.force_close()
	GameProgress.record_level_result(LEVEL_ID, stars, _level_time, ending, success)
	if hud != null:
		hud.show_result(success, stars, ending, _level_time, _deaths_total, _completed_count(), _tasks.size())


func request_restart() -> void:
	if NetworkManager.is_server_authority():
		if NetworkManager.is_networked():
			rpc("_restart_rpc")
		_do_restart()
	else:
		rpc_id(1, "request_restart_rpc")


@rpc("any_peer", "call_remote", "reliable")
func request_restart_rpc() -> void:
	if NetworkManager.is_server_authority():
		request_restart()


@rpc("authority", "call_remote", "reliable")
func _restart_rpc() -> void:
	_do_restart()


func _do_restart() -> void:
	get_tree().reload_current_scene()


func request_menu() -> void:
	_go_to_menu()


func _go_to_menu() -> void:
	NetworkManager.disconnect_all()
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")


# ---------------------------------------------------------------- visuals ---
func _process(delta: float) -> void:
	_flicker_time += delta
	if _blackout_timer > 0.0:
		_blackout_timer -= delta
	if canvas_modulate != null:
		var target: Color = BLACKOUT_MODULATE if _blackout_timer > 0.0 else BASE_MODULATE
		canvas_modulate.color = canvas_modulate.color.lerp(target, minf(1.0, delta * 6.0))
	var blackout_mult: float = 0.15 if _blackout_timer > 0.0 else 1.0
	for i: int in range(_lights.size()):
		var flicker: float = 0.88 + 0.12 * sin(_flicker_time * 7.0 + _light_phase[i])
		if randf() < 0.003:
			flicker *= 0.35
		_lights[i].energy = _light_base[i] * flicker * blackout_mult
	# Visual tempat sembunyi = turunan dari posisi pemain yang sembunyi.
	for s: Node2D in _spots:
		var occ: bool = false
		for pid: int in _players.keys():
			var p: Node = _players[pid]
			if p.is_hidden and p.global_position.distance_to(s.global_position) <= HIDE_RANGE:
				occ = true
				break
		s.set_occupied(occ)
	_update_hud_frame()


func _completed_count() -> int:
	var n: int = 0
	for tid: StringName in _tasks.keys():
		if bool(_tasks[tid]["completed"]):
			n += 1
	return n


func _update_hud_static() -> void:
	if hud == null:
		return
	hud.set_task_total(_tasks.size())


func _update_hud_frame() -> void:
	if hud == null:
		return
	hud.update_timer(_level_time)
	hud.update_tasks(_completed_count(), _tasks.size(), _exit_open)
	var status_lines: Array[String] = []
	for pid: int in _players.keys():
		var p: Node = _players[pid]
		var st: String = "TERKURUNG" if p.is_downed else ("SEMBUNYI" if p.is_hidden else "AKTIF")
		status_lines.append("P%d: %s%s" % [p.player_index, st, " [+ITEM]" if p.carrying_revive else ""])
	hud.update_status(status_lines)
	hud.show_prompt(_compute_prompt())


func _compute_prompt() -> String:
	var local_p: Node = _players.get(NetworkManager.local_peer_id())
	if local_p == null or local_p.is_downed or _level_ended:
		return ""
	if local_p.is_hidden:
		return "[E] Keluar dari persembunyian"
	if _cage_peer != -1 and _revive_carrier == NetworkManager.local_peer_id() and cage != null and local_p.global_position.distance_to(cage.global_position) <= CAGE_RANGE:
		return "[Tahan E] Selamatkan teman dari kurungan"
	if _revive_visible and revive_item != null and local_p.global_position.distance_to(revive_item.global_position) <= REVIVE_RANGE:
		return "[E] Ambil Item Bangkit"
	var tid: StringName = _nearest_task(local_p.global_position)
	if tid != StringName(""):
		var t: Dictionary = _tasks[tid]
		if t["requires_two"] and _server_needed() > 1:
			return "[E] %s — BUTUH 2 PEMAIN!" % t["node"].title
		return "[E] Kerjakan: %s" % t["node"].title
	if _nearest_spot(local_p.global_position) != null:
		return "[E] Sembunyi"
	if _exit_open and exit_door != null and local_p.global_position.distance_to(exit_door.global_position) <= EXIT_RADIUS + 40.0:
		return "Berdiri berdua di pintu keluar untuk kabur!"
	return ""


func get_map_size_tiles() -> Vector2i:
	# Dibaca player.gd untuk batas kamera (map Level 2 lebih besar dari Level 1).
	return MAP_SIZE_TILES


func _show_message(text: String) -> void:
	if hud != null:
		hud.show_message(text)
