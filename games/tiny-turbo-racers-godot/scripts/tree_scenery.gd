@tool
extends Node3D
## Real scene-imported CC0 Kenney trees, not primitive green spheres.
## 7 different tree models: detailed broadleaf, oak, pine, palms and cypress.
## Models are physically different 3D geometry. Kenney Nature Kit is stylized
## geometry (NOT photogrammetry); per-tree size/rotation break repetition.
const ROOT: String = "res://assets/nature/"
const TREE_NAMES: Array[String] = [
	"tree-detailed.glb","tree-oak.glb","tree-pinetalla-detailed.glb",
	"tree-pinetallb-detailed.glb","tree-palmdetailedtall.glb",
	"tree-default.glb","tree-cone.glb"
]
var tree_count: int = 0
var loaded_variants: int = 0
var photo_tree_count: int = 0
const PHOTO_PINE: String = "res://assets/nature/pine_sapling_ph_1k_lod.glb"

func setup(track: Node3D, route: int) -> void:
	var available: Array[PackedScene] = []
	for name in TREE_NAMES:
		var path: String=ROOT+name
		if ResourceLoader.exists(path):
			var scene: Resource=load(path)
			if scene is PackedScene:
				available.append(scene as PackedScene)
	loaded_variants=available.size()
	var photogrammetry: PackedScene = load(PHOTO_PINE) as PackedScene if ResourceLoader.exists(PHOTO_PINE) else null
	if available.is_empty():
		push_warning("Kenney CC0 tree GLBs not imported. Enable nature asset workflow.")
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 790011 + route*227
	var count: int = [32,82,112][clampi(route,0,2)]
	for i in range(count):
		var index: int = i%available.size()
		# Coastal route is palm-heavy, mountain primarily tall pine.
		if route==1 and i%4==0 and available.size()>4:
			index=4
		if route==2 and i%3!=0 and available.size()>3:
			index=2+(i%2)
		var use_photo: bool=photogrammetry!=null and ((route==2 and i%13==0) or (route==1 and i%21==0) or (route==0 and i%16==0))
		var model: Node3D=photogrammetry.instantiate() as Node3D if use_photo else available[index].instantiate() as Node3D
		if model==null:
			continue
		model.name="RealTree%03d" % i
		model.rotation.y=rng.randf_range(-PI,PI)
		var scale_factor: float=rng.randf_range(1.4,2.2) if use_photo else rng.randf_range(4.5,7.1)
		if use_photo:
			photo_tree_count+=1
		model.scale=Vector3.ONE*scale_factor
		var angle: float=TAU*(float(i)+rng.randf_range(.2,.8))/float(count)
		var distance: float=rng.randf_range(23.0,53.0)
		var side: float=1.0 if i%2==0 else -1.0
		model.position=track.road_position(angle,distance*side)+Vector3(0,.04,0)
		# Trees should remain outside the full road/sidewalk boundary.
		model.visible=true
		add_child(model)
		tree_count+=1
