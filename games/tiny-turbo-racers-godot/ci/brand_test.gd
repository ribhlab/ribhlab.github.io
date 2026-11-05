extends SceneTree
## v0.7: all six distinct artist-licensed glTF cars must IMPORT successfully.
const Catalog = preload("res://scripts/brand_catalog.gd")
const Car = preload("res://scripts/real_car.gd")
func _initialize() -> void:
	call_deferred("_test")

func _test() -> void:
	if Catalog.CARS.size()!=6 or Catalog.count_available()!=6 or not Catalog.all_credited():
		push_error("Six branded model files or artist credits missing")
		quit(41)
		return
	var names: Array[String] = []
	for i in range(Catalog.CARS.size()):
		var entry:Dictionary=Catalog.get_car(i)
		var car=Car.new()
		car.set_model_file(str(entry["file"]))
		car.configure(Color("#eeeeee"),i%4)
		root.add_child(car)
		if not car.imported_vehicle or car.external_mesh_count<1:
			push_error("Car failed to import: "+str(entry["name"]))
			quit(42)
			return
		names.append(str(entry["name"]))
		root.remove_child(car)
		car.free()
	var game=load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	game._open_garage()
	game._select_brand(5)
	if game.selected_car!=5 or not game.player.imported_vehicle:
		push_error("Car choice not applied")
		quit(43)
		return
	print("TINY_TURBO_BRANDS_PASS ",", ".join(names))
	game.queue_free()
	quit(0)
