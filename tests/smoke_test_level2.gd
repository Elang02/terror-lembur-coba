extends Node
## Smoke test Level 2 (Lobi Kantor "Gelap Gulita").
## Cara pakai paling gampang: buka tests/smoke_test_level2.tscn lalu tekan F6,
## kemudian baca panel Output. Bisa juga headless:
##   godot --headless --path . res://tests/smoke_test_level2.tscn
## Keluar 0 kalau semua cek lolos, 1 kalau ada yang gagal.
## Yang dicek: scene termuat, jumlah tile, collision dinding, A* (semua tugas,
## tempat sembunyi, titik cas, titik kabel & pintu keluar bisa dicapai dari
## spawn), jumlah node gameplay, pemain & Satpam ter-spawn, batas kamera.

const T: float = 32.0
const TASK_RANGE: float = 62.0
const HIDE_RANGE: float = 50.0

var _failures: Array[String] = []
var _checks: int = 0


func _ready() -> void:
	await _run()
	print("SMOKE L2: %d cek, %d gagal" % [_checks, _failures.size()])
	for f: String in _failures:
		print("SMOKE L2 FAIL: ", f)
	if _failures.is_empty():
		print("SMOKE L2: ALL PASS")
	get_tree().quit(0 if _failures.is_empty() else 1)


func _check(cond: bool, label: String) -> void:
	_checks += 1
	if cond:
		print("SMOKE L2 OK: ", label)
	else:
		_failures.append(label)
		print("SMOKE L2 FAIL: ", label)


func _cell(cell: Vector2i) -> Vector2:
	return Vector2(cell) * T + Vector2(16, 16)


func _children_of(level: Node, path: String) -> Array[Node]:
	var out: Array[Node] = []
	var root: Node = level.get_node_or_null(path)
	if root == null:
		return out
	for c: Node in root.get_children():
		out.append(c)
		for cc: Node in c.get_children():
			out.append(cc)
	return out


func _run() -> void:
	NetworkManager.start_solo()
	var scene: PackedScene = load("res://scenes/level_2.tscn")
	_check(scene != null, "level_2.tscn termuat")
	if scene == null:
		return
	var level: Node2D = scene.instantiate()
	add_child(level)
	for i: int in range(3):
		await get_tree().physics_frame

	# --- Struktur & tile ---
	var lantai: TileMapLayer = level.get_node_or_null("Lantai")
	var dinding: TileMapLayer = level.get_node_or_null("Dinding")
	var props: TileMapLayer = level.get_node_or_null("Props")
	_check(lantai != null and dinding != null and props != null, "3 TileMapLayer ada (Lantai/Dinding/Props)")
	if lantai == null or dinding == null or props == null:
		return
	_check(lantai.get_used_cells().size() == 2740, "Lantai = 2740 sel (dapat %d)" % lantai.get_used_cells().size())
	_check(dinding.get_used_cells().size() == 750, "Dinding = 750 sel (dapat %d)" % dinding.get_used_cells().size())
	_check(props.get_used_cells().size() == 736, "Props = 736 sel (dapat %d)" % props.get_used_cells().size())
	_check(dinding.get_used_rect() == Rect2i(0, 0, 72, 46), "Ukuran map 72 x 46 (dapat %s)" % str(dinding.get_used_rect()))

	# --- Collision ---
	var space: PhysicsDirectSpaceState2D = level.get_world_2d().direct_space_state
	var pq := PhysicsPointQueryParameters2D.new()
	pq.collision_mask = 1
	pq.position = _cell(Vector2i(22, 17))
	_check(not space.intersect_point(pq).is_empty(), "Tiang atrium (22,17) punya collision")
	pq.position = _cell(Vector2i(30, 29))
	_check(space.intersect_point(pq).is_empty(), "Lantai lorong atrium (30,29) bebas collision")
	var ray := PhysicsRayQueryParameters2D.create(_cell(Vector2i(5, 10)), _cell(Vector2i(12, 10)), 1)
	_check(not space.intersect_ray(ray).is_empty(), "Tangga Darurat -> Ruang Surat terhalang dinding")
	var ray2 := PhysicsRayQueryParameters2D.create(_cell(Vector2i(17, 29)), _cell(Vector2i(60, 29)), 1)
	_check(space.intersect_ray(ray2).is_empty(), "Lorong bawah atrium (baris 29) bebas halangan")

	# --- A* ---
	var pf: GridPathfinder = level._pathfinder
	_check(pf != null, "GridPathfinder terbentuk")
	if pf != null:
		_check(pf.walkable_point_count() == 1764, "Titik walkable A* = 1764 (dapat %d)" % pf.walkable_point_count())
		var spawn: Vector2 = level.get_node("Spawn/PlayerSpawn1").global_position
		var targets: Array = []  # [label, posisi, jarak maksimal]
		for n: Node in _children_of(level, "Tugas"):
			if "task_id" in n:
				targets.append(["tugas " + n.name, (n as Node2D).global_position, TASK_RANGE])
		for n: Node in _children_of(level, "TempatSembunyi"):
			targets.append(["sembunyi " + n.name, (n as Node2D).global_position, HIDE_RANGE])
		for grp: String in ["TitikCas", "TitikKabel"]:
			for n: Node in _children_of(level, grp):
				targets.append([grp + " " + n.name, (n as Node2D).global_position, 40.0])
		targets.append(["PintuKeluar", level.get_node("PintuKeluar").global_position, 72.0])
		targets.append(["KomputerSecurity", level.get_node("KomputerSecurity").global_position, 40.0])
		for t: Array in targets:
			var path: PackedVector2Array = pf.find_path_world(spawn, t[1])
			var ok: bool = not path.is_empty() and path[path.size() - 1].distance_to(t[1]) <= float(t[2])
			_check(ok, "A* spawn -> %s bisa dicapai" % t[0])

	# --- Node gameplay ---
	_check(level._tasks.size() == 7, "7 tugas (dapat %d)" % level._tasks.size())
	_check(level._spots.size() == 10, "10 tempat sembunyi (dapat %d)" % level._spots.size())
	_check(level._lights.size() == 30, "30 lampu (dapat %d)" % level._lights.size())
	_check(level._hitung_marker("TitikCas") == 6, "6 titik cas")
	_check(level._hitung_marker("TitikKabel") == 4, "4 titik kabel")
	var nama_ruangan: CanvasItem = level.get_node_or_null("NamaRuangan")
	_check(nama_ruangan != null and not nama_ruangan.visible, "NamaRuangan disembunyikan saat main")

	# --- Pemain, Satpam, kamera ---
	var players: Array[Node] = get_tree().get_nodes_in_group("Player")
	_check(players.size() == 1, "Solo: 1 pemain ter-spawn (dapat %d)" % players.size())
	if not players.is_empty():
		var p: Node2D = players[0]
		var cam: Camera2D = p.get_node_or_null("Camera2D")
		_check(cam != null and cam.limit_right == 72 * 32 and cam.limit_bottom == 46 * 32, "Batas kamera 2304 x 1472")
		var lampu: PointLight2D = p.get_node_or_null("Light")
		_check(lampu != null and is_equal_approx(lampu.texture_scale, 0.75), "Cahaya HP pemain diperkecil (0.75)")
	var satpam: Node = level.get_node_or_null("Satpam")
	_check(satpam != null, "Satpam ada di scene")
	if satpam != null:
		_check(satpam.patrol_points.size() == 12, "Rute Fase1 = 12 titik (dapat %d)" % satpam.patrol_points.size())
		_check(satpam.pathfinder != null, "Satpam memakai pathfinder")
