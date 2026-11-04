extends SceneTree
# Run with: godot --headless --editor --path PROJECT --script res://ci/configure_android.gd
func _initialize() -> void:
	var settings = EditorInterface.get_editor_settings()
	var sdk: String = OS.get_environment("ANDROID_SDK_ROOT")
	var java: String = OS.get_environment("JAVA_HOME")
	if sdk.is_empty() or java.is_empty():
		push_error("ANDROID_SDK_ROOT / JAVA_HOME missing")
		quit(1)
		return
	settings.set_setting("export/android/android_sdk_path", sdk)
	settings.set_setting("export/android/java_sdk_path", java)
	print("TinyTurbo Android SDK configured: ", sdk)
	print("TinyTurbo Java configured: ", java)
	quit()
