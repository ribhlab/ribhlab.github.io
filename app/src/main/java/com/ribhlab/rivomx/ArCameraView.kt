package com.ribhlab.rivomx

import android.content.Context
import android.opengl.GLES11Ext
import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.Matrix
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.WindowManager
import com.google.ar.core.Anchor
import com.google.ar.core.Config
import com.google.ar.core.Coordinates2d
import com.google.ar.core.DepthPoint
import com.google.ar.core.Frame
import com.google.ar.core.Plane
import com.google.ar.core.Point
import com.google.ar.core.Session
import com.google.ar.core.TrackingState
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.util.concurrent.ConcurrentLinkedQueue
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10

/**
 * ARCore owns the camera. The GL thread is the only owner of ARCore frame and anchor access.
 * The app converts hit tests into 3D anchors; it never guesses dimensions from image pixels.
 */
class ArCameraView(context: Context, private val publish: (String, Readout, List<Projected>) -> Unit) :
    GLSurfaceView(context) {
    @Volatile private var session: Session? = null
    private val renderer = CameraRenderer(context, { session }, publish)

    init {
        setEGLContextClientVersion(2)
        preserveEGLContextOnPause = true
        setRenderer(renderer)
        renderMode = RENDERMODE_CONTINUOUSLY
    }
    fun attach(session: Session) { this.session = session }
    fun clear() = renderer.clear()
    fun mode(mode: MeasureMode) = renderer.mode(mode)
    fun tap(x: Float, y: Float) = renderer.tap(x, y)
    fun release() { session = null }

    private sealed interface Command {
        data class Tap(val x: Float, val y: Float) : Command
        data class Mode(val value: MeasureMode) : Command
        data object Clear : Command
    }

    private class CameraRenderer(
        private val context: Context,
        private val currentSession: () -> Session?,
        private val publish: (String, Readout, List<Projected>) -> Unit
    ) : Renderer {
        private var textureId = 0
        private var programId = 0
        private var width = 1
        private var height = 1
        private var mode = MeasureMode.DISTANCE
        private var lastPublished = 0L
        private val commands = ConcurrentLinkedQueue<Command>()
        private val anchors = mutableListOf<Anchor>()
        private val sourceNames = mutableListOf<String>()
        private val handler = Handler(Looper.getMainLooper())
        private val square = buffer(floatArrayOf(-1f,-1f, 1f,-1f, -1f,1f, 1f,1f))
        private val uv = buffer(FloatArray(8))
        private val view = FloatArray(16)
        private val projection = FloatArray(16)
        private val pv = FloatArray(16)

        fun tap(x: Float, y: Float) { commands.add(Command.Tap(x, y)) }
        fun clear() { commands.add(Command.Clear) }
        fun mode(value: MeasureMode) { commands.add(Command.Mode(value)) }

        override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
            val id = IntArray(1)
            GLES20.glGenTextures(1, id, 0)
            textureId = id[0]
            GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, textureId)
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
            programId = program(
                """attribute vec2 aPosition; attribute vec2 aUv; varying vec2 vUv;
                void main(){gl_Position=vec4(aPosition,0.,1.);vUv=aUv;}""",
                """#extension GL_OES_EGL_image_external : require
                precision mediump float; varying vec2 vUv; uniform samplerExternalOES tex;
                void main(){gl_FragColor=texture2D(tex,vUv);}"""
            )
            GLES20.glClearColor(0.01f,0.04f,0.07f,1f)
        }
        override fun onSurfaceChanged(gl: GL10?, w: Int, h: Int) {
            width = w.coerceAtLeast(1)
            height = h.coerceAtLeast(1)
            GLES20.glViewport(0,0,width,height)
        }
        override fun onDrawFrame(gl: GL10?) {
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
            val session = currentSession() ?: return
            if (textureId == 0 || programId == 0) return
            try {
                @Suppress("DEPRECATION")
                val rotation = (context.getSystemService(Context.WINDOW_SERVICE) as WindowManager).defaultDisplay.rotation
                session.setDisplayGeometry(rotation,width,height)
                session.setCameraTextureName(textureId)
                val frame = session.update()
                if (frame.timestamp == 0L) return
                square.position(0)
                uv.position(0)
                frame.transformCoordinates2d(
                    Coordinates2d.OPENGL_NORMALIZED_DEVICE_COORDINATES, square,
                    Coordinates2d.TEXTURE_NORMALIZED, uv
                )
                square.position(0)
                uv.position(0)
                GLES20.glDisable(GLES20.GL_DEPTH_TEST)
                GLES20.glUseProgram(programId)
                val xy = GLES20.glGetAttribLocation(programId,"aPosition")
                val st = GLES20.glGetAttribLocation(programId,"aUv")
                GLES20.glEnableVertexAttribArray(xy)
                GLES20.glEnableVertexAttribArray(st)
                GLES20.glVertexAttribPointer(xy,2,GLES20.GL_FLOAT,false,0,square)
                GLES20.glVertexAttribPointer(st,2,GLES20.GL_FLOAT,false,0,uv)
                GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
                GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES,textureId)
                GLES20.glUniform1i(GLES20.glGetUniformLocation(programId,"tex"),0)
                GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP,0,4)
                GLES20.glDisableVertexAttribArray(xy)
                GLES20.glDisableVertexAttribArray(st)

                val camera = frame.camera
                var cmd = commands.poll()
                while(cmd != null) {
                    when(cmd) {
                        Command.Clear -> dropAnchors()
                        is Command.Mode -> { dropAnchors(); mode=cmd.value }
                        is Command.Tap -> if (camera.trackingState == TrackingState.TRACKING) handleTap(frame,cmd.x,cmd.y)
                    }
                    cmd = commands.poll()
                }
                val now = SystemClock.elapsedRealtime()
                if (now - lastPublished >= 150L) {
                    lastPublished=now
                    val tracking = camera.trackingState == TrackingState.TRACKING
                    val status = if (!tracking) "Scan a textured surface slowly" else
                        if (session.config.depthMode == Config.DepthMode.AUTOMATIC) "Tracking • Depth on" else "Tracking • Plane mode"
                    val points = if (tracking) {
                        camera.getViewMatrix(view,0)
                        camera.getProjectionMatrix(projection,0,0.1f,100f)
                        Matrix.multiplyMM(pv,0,projection,0,view,0)
                        anchors.mapNotNull { if (it.trackingState==TrackingState.TRACKING) project(it) else null }
                    } else emptyList()
                    val readout = currentReadout()
                    handler.post { publish(status,readout,points) }
                }
            } catch (e: Exception) {
                val now = SystemClock.elapsedRealtime()
                if(now-lastPublished > 700L) {
                    lastPublished=now
                    handler.post { publish("AR error: " + (e.message ?: "unknown"),Readout(),emptyList()) }
                }
            }
        }
        private fun handleTap(frame: Frame,x:Float,y:Float) {
            val hit=frame.hitTest(x,y).firstOrNull { result ->
                when(val item = result.trackable) {
                    is DepthPoint -> true
                    is Plane -> item.isPoseInPolygon(result.hitPose)
                    is Point -> item.orientationMode == Point.OrientationMode.ESTIMATED_SURFACE_NORMAL
                    else -> false
                }
            } ?: return
            if (anchors.size>=mode.points) dropAnchors()
            anchors.add(hit.createAnchor())
            sourceNames.add(when(hit.trackable) {
                is DepthPoint -> "Depth"
                is Plane -> "Plane"
                else -> "Feature"
            })
        }
        private fun currentReadout():Readout {
            fun distance(i:Int,j:Int):Double? {
                if (anchors.size <= j || anchors[i].trackingState != TrackingState.TRACKING ||
                    anchors[j].trackingState != TrackingState.TRACKING) return null
                val a=anchors[i].pose; val b=anchors[j].pose
                return MeasureMath.distance(
                    Point3(a.tx().toDouble(),a.ty().toDouble(),a.tz().toDouble()),
                    Point3(b.tx().toDouble(),b.ty().toDouble(),b.tz().toDouble())
                )
            }
            return Readout(distance(0,1),if(mode==MeasureMode.RECTANGLE) distance(2,3) else null,
                anchors.size,sourceNames.distinct().joinToString(" + "))
        }
        private fun project(anchor:Anchor):Projected? {
            val pose=anchor.pose
            val input=floatArrayOf(pose.tx(),pose.ty(),pose.tz(),1f)
            val out=FloatArray(4)
            Matrix.multiplyMV(out,0,pv,0,input,0)
            if (out[3]<=0.0001f) return null
            val nx=out[0]/out[3]; val ny=out[1]/out[3]
            if(!nx.isFinite()||!ny.isFinite())return null
            return Projected((nx+1f)*width/2f,(1f-ny)*height/2f)
        }
        private fun dropAnchors() {
            anchors.forEach { it.detach() }
            anchors.clear()
            sourceNames.clear()
        }
        private fun program(vertex:String,fragment:String):Int {
            fun compile(type:Int,source:String):Int {
                val sh=GLES20.glCreateShader(type)
                GLES20.glShaderSource(sh,source)
                GLES20.glCompileShader(sh)
                val ok=IntArray(1)
                GLES20.glGetShaderiv(sh,GLES20.GL_COMPILE_STATUS,ok,0)
                check(ok[0]!=0){ GLES20.glGetShaderInfoLog(sh) }
                return sh
            }
            val vs=compile(GLES20.GL_VERTEX_SHADER,vertex)
            val fs=compile(GLES20.GL_FRAGMENT_SHADER,fragment)
            val p=GLES20.glCreateProgram()
            GLES20.glAttachShader(p,vs)
            GLES20.glAttachShader(p,fs)
            GLES20.glLinkProgram(p)
            val ok=IntArray(1)
            GLES20.glGetProgramiv(p,GLES20.GL_LINK_STATUS,ok,0)
            check(ok[0]!=0){ GLES20.glGetProgramInfoLog(p) }
            GLES20.glDeleteShader(vs)
            GLES20.glDeleteShader(fs)
            return p
        }
        companion object {
            fun buffer(data:FloatArray):FloatBuffer =
                ByteBuffer.allocateDirect(data.size*4).order(ByteOrder.nativeOrder()).asFloatBuffer().apply{
                    put(data);position(0)
                }
        }
    }
}
