extends SceneTree
## v0.6: verify that all six different artist-licensed 3D brand model files
## are present, importable and really used by the playable garage.
const Catalog = preload("res://scripts/brand_catalog.gd")
const CarScene = preload("res://scripts/real_car.gd")

func _initialize() -> void:
	call_deferred("_verify")

func _verify() -> void:
	if not Catalog.all_credited():
		push_error("Some brand models missing attribution")
		quit(21)
		return
	if Catalog.CARS.size()!=6 or Catalog.count_available()!=6:
		push_error("Missing licensed 3D cars: catalog="+str(Catalog.CARS.size())+
			" available="+str(Catalog.count_available()))
		quit(22)
		return
	var tested: Array[String] = []
	for i in range(Catalog.CARS.size()):
		var data: Dictionary = Catalog.get_car(i)
		var sports_car = CarScene.new()
		sports_car.set_model_file(str(data["file"]))
		sports_car.configure(Color("#eeeeee"),i%4)
		root.add_child(sports_car)
		if not sports_car.imported_vehicle or sports_car.external_mesh_count < 1:
			push_error("The brand sports-car model failed actual Godot scene import: "+str(data["name"]))
			quit(23)
			return
		print("GODOT_BRAND_MODEL_PASS: ",data["name"]," mesh_nodes=",sports_car.external_mesh_count)
		tested.append(str(data["name"]))
		root.remove_child(sports_car)
		sports_car.free()
	var scene: PackedScene = load("res://scenes/main.tscn")
	var game = scene.instantiate()
	root.add_child(game)
	game._select_brand(5)
	if game.selected_car != 5 or not game.player.imported_vehicle:
		push_error("Garage did not change the playable car")
		quit(24)
		return
	if not game.garage_car_label.text.contains("Audi R8"):
		push_error("Garage model name not updated")
		quit(25)
		return
	print("TINY_TURBO_SIX_BRAND_GARAGE_PASS ",", ".join(tested))
	game.queue_free()
	quit(0)
