extends RefCounted
## Tiny Turbo Racers GT — 6 real-car reference models, each licensed by its 3D author.
##
## IMPORTANT: CC BY covers an artist's mesh, not necessarily manufacturer
## trademarks, emblems, trade dress or other third-party rights. This library
## is a NON-OFFICIAL development showcase. Do not market it as manufacturer-
## licensed or ship car brands/logos commercially without separate rights review.
##
## Originals and full credit lines: res://assets/BRANDED_MODEL_CREDITS.md
const CARS: Array[Dictionary] = [
	{
		"name": "BMW M4 CSL",
		"maker": "BMW",
		"id": "bmw-m4-csl",
		"file": "res://assets/brands/bmw-m4-csl.glb",
		"paint": Color("#43a2f6"),
		"top_speed": 39.5,
		"accel": 1.08,
		"source": "https://sketchfab.com/3d-models/none-26d05968e63b4fc28205cbb9abb0ea41",
		"artist": "Black Snow"
	},
	{
		"name": "Mercedes-AMG GT",
		"maker": "Mercedes-Benz",
		"id": "mercedes-benz-amg-gt",
		"file": "res://assets/brands/mercedes-benz-amg-gt.glb",
		"paint": Color("#d9e2f3"),
		"top_speed": 38.0,
		"accel": 1.04,
		"source": "https://sketchfab.com/3d-models/661dcab94455463784651a3ebc63cfb9",
		"artist": "Yan Carvalho"
	},
	{
		"name": "Porsche 911 GT3",
		"maker": "Porsche",
		"id": "porsche-911-gt3",
		"file": "res://assets/brands/porsche-911-gt3.glb",
		"paint": Color("#ffd44d"),
		"top_speed": 40.0,
		"accel": 1.07,
		"source": "https://sketchfab.com/3d-models/none-78d5c47ab2554c2592b7e499179a0792",
		"artist": "ChevroletSS"
	},
	{
		"name": "Lamborghini Aventador SVJ",
		"maker": "Lamborghini",
		"id": "lamborghini-aventador-svj",
		"file": "res://assets/brands/lamborghini-aventador-svj.glb",
		"paint": Color("#45d78a"),
		"top_speed": 42.5,
		"accel": 1.13,
		"source": "https://sketchfab.com/3d-models/none-784e4656aca649cca55d6b18740a19b2",
		"artist": "SDC PERFORMANCE"
	},
	{
		"name": "Ferrari F40",
		"maker": "Ferrari",
		"id": "ferrari-f40",
		"file": "res://assets/brands/ferrari-f40.glb",
		"paint": Color("#f03b42"),
		"top_speed": 40.5,
		"accel": 1.09,
		"source": "https://sketchfab.com/3d-models/none-52a66c41cfcd4f999fb1b1c49bf24d70",
		"artist": "Black Snow"
	},
	{
		"name": "Audi R8",
		"maker": "Audi",
		"id": "audi-r8",
		"file": "res://assets/brands/audi-r8.glb",
		"paint": Color("#9b75fc"),
		"top_speed": 39.5,
		"accel": 1.09,
		"source": "https://sketchfab.com/3d-models/none-e17e438f076f4427a58d93aa779edaed",
		"artist": "wallon"
	}
]

static func get_car(index: int) -> Dictionary:
	return CARS[clampi(index,0,CARS.size()-1)]

static func available(index: int) -> bool:
	return ResourceLoader.exists(str(get_car(index)["file"]))

static func count_available() -> int:
	var count: int = 0
	for i in range(CARS.size()):
		if available(i):
			count += 1
	return count

static func all_credited() -> bool:
	for car in CARS:
		if str(car["artist"]).is_empty() or str(car["source"]).is_empty():
			return false
	return true
