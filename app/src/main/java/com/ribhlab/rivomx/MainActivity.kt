package com.ribhlab.rivomx

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.content.ContextCompat
import com.google.ar.core.ArCoreApk
import com.google.ar.core.Config
import com.google.ar.core.Session
import org.json.JSONArray
import org.json.JSONObject

class MainActivity : ComponentActivity() {
    private lateinit var arView: ArCameraView
    private var session: Session? = null
    private var running = false
    private var requestedInstall = false
    private var status by mutableStateOf("Waiting for camera permission")
    private var readout by mutableStateOf(Readout())
    private var projected by mutableStateOf(emptyList<Projected>())
    private var mode by mutableStateOf(MeasureMode.DISTANCE)
    private var unit by mutableStateOf(UnitOfLength.CM)
    private var history by mutableStateOf(emptyList<SavedMeasurement>())
    private val prefs by lazy { getSharedPreferences("rivomx",MODE_PRIVATE) }

    private val permission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { yes ->
        if(yes) startCamera() else status="Camera permission required"
    }
    private val pdf = registerForActivityResult(ActivityResultContracts.CreateDocument("application/pdf")) { uri ->
        if(uri!=null) {
            runCatching {
                contentResolver.openOutputStream(uri)!!.use { PdfExport.write(it,history) }
            }.onSuccess { status="PDF exported" }
                .onFailure { status="PDF export failed: "+it.message }
        }
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        history=load()
        arView=ArCameraView(this){ s,r,p -> status=s; readout=r; projected=p }
        setContent {
            RivoScreen(
                view=arView, status=status, readout=readout, points=projected, mode=mode, unit=unit, history=history,
                onMode={ mode=it;readout=Readout();projected=emptyList();arView.mode(it) },
                onUnit={unit=it},
                onClear={readout=Readout();projected=emptyList();arView.clear()},
                onSave={
                    if(readout.length!=null && (mode==MeasureMode.DISTANCE || readout.width!=null)) {
                        val item=SavedMeasurement(System.currentTimeMillis(),readout.length!!,readout.width,readout.source)
                        history=(listOf(item)+history).take(200)
                        persist(history)
                        status="Saved on this phone"
                    } else status="Tap all required points before saving"
                },
                onPdf={if(history.isEmpty())status="Save one measurement first" else pdf.launch("RivoMx.pdf")},
                onRetry={if(hasCamera())startCamera() else permission.launch(Manifest.permission.CAMERA)}
            )
        }
        if(!hasCamera()) permission.launch(Manifest.permission.CAMERA)
    }
    override fun onResume() {
        super.onResume()
        if(::arView.isInitialized && hasCamera())startCamera()
    }
    private fun hasCamera()=ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED
    private fun startCamera() {
        if(running || !hasCamera() || !::arView.isInitialized) return
        try {
            if(ArCoreApk.getInstance().requestInstall(this,!requestedInstall)==ArCoreApk.InstallStatus.INSTALL_REQUESTED){
                requestedInstall=true
                status="Install Google Play Services for AR"
                return
            }
            val s=session ?: Session(this).also { created ->
                val config=Config(created)
                config.planeFindingMode=Config.PlaneFindingMode.HORIZONTAL_AND_VERTICAL
                if(created.isDepthModeSupported(Config.DepthMode.AUTOMATIC))
                    config.depthMode=Config.DepthMode.AUTOMATIC
                created.configure(config)
                session=created
            }
            arView.attach(s)
            s.resume()
            arView.onResume()
            running=true
            status="Move phone to scan a surface"
        } catch(e:Exception) {
            status="AR unavailable: "+(e.message?:e.javaClass.simpleName)
        }
    }
    override fun onPause(){
        if(running){arView.onPause();session?.pause();running=false}
        super.onPause()
    }
    override fun onDestroy(){
        if(::arView.isInitialized)arView.release()
        session?.close()
        session=null
        super.onDestroy()
    }
    private fun load():List<SavedMeasurement> = runCatching {
        val array=JSONArray(prefs.getString("history","[]"))
        (0 until array.length()).map { n ->
            val j=array.getJSONObject(n)
            SavedMeasurement(j.getLong("id"),j.getDouble("length"),
                if(j.isNull("width"))null else j.getDouble("width"),j.optString("source"))
        }
    }.getOrDefault(emptyList())
    private fun persist(items:List<SavedMeasurement>){
        val array=JSONArray()
        items.forEach { it ->
            array.put(JSONObject().apply{
                put("id",it.id);put("length",it.length)
                put("width",it.width?:JSONObject.NULL);put("source",it.source)
            })
        }
        prefs.edit().putString("history",array.toString()).apply()
    }
}
