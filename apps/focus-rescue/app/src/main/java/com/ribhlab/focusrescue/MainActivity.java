package com.ribhlab.focusrescue;

import android.Manifest;
import android.app.Activity;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.*;
import android.view.*;
import android.widget.*;
import java.util.*;

public class MainActivity extends Activity {
    private CameraManager manager;
    private HandlerThread cameraThread;
    private Handler bg, ui = new Handler(Looper.getMainLooper());
    private TextureView preview;
    private TextView status, modeText;
    private Spinner cameraSpinner;
    private Button startButton, stopButton, autoButton, manualButton;
    private SeekBar speedBar;
    private final ArrayList<String> ids = new ArrayList<>();
    private CameraDevice camera;
    private CameraCaptureSession session;
    private Surface surface;
    private CaptureRequest.Builder request;
    private String selectedId;
    private volatile boolean running = false, foreground = false;
    private boolean manualSupported, autoSupported, manualMode;
    private float maxDistance;
    private int afMode = CaptureRequest.CONTROL_AF_MODE_AUTO;
    private int stepCount = 0;
    private int gapMs = 1500;
    private long finishAt = 0;
    private Runnable nextStep;
    private int cameraGeneration = 0;

    private int dp(int v) { return (int)(getResources().getDisplayMetrics().density*v+.5f); }
    private TextView text(String s, int size) {
        TextView t=new TextView(this); t.setText(s);t.setTextSize(size);
        t.setTextColor(Color.rgb(231,242,239)); t.setPadding(dp(10),dp(8),dp(10),dp(8));return t;
    }
    private Button button(String s) {
        Button b=new Button(this);b.setText(s);b.setAllCaps(false);return b;
    }
    private void report(String s) { ui.post(() -> { if(status!=null)status.setText(s); }); }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        manager=(CameraManager)getSystemService(CAMERA_SERVICE);
        cameraThread=new HandlerThread("RibhLab-Camera2");cameraThread.start();bg=new Handler(cameraThread.getLooper());
        LinearLayout screen=new LinearLayout(this);screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundColor(Color.rgb(11,28,29)); setContentView(screen);
        ScrollView scroll=new ScrollView(this);screen.addView(scroll,new LinearLayout.LayoutParams(-1,-1));
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12),dp(10),dp(12),dp(20));scroll.addView(root);
        TextView title=text("RibhLab  •  Focus Rescue",24); title.setTextColor(Color.rgb(99,228,185));root.addView(title);
        root.addView(text("تجربة تحريك تركيز العدسة - ما كتصلحش العطب الميكانيكي المضمون",13));
        cameraSpinner=new Spinner(this);root.addView(cameraSpinner,new LinearLayout.LayoutParams(-1,dp(54)));
        preview=new TextureView(this); root.addView(preview,new LinearLayout.LayoutParams(-1,dp(265)));
        status=text("جاري فحص الكاميرات...",14);root.addView(status);
        modeText=text("التركيز: غير محدد",13);root.addView(modeText);
        LinearLayout modes=new LinearLayout(this); modes.setOrientation(LinearLayout.HORIZONTAL);root.addView(modes);
        autoButton=button("Autofocus");manualButton=button("Manual sweep");
        modes.addView(autoButton,new LinearLayout.LayoutParams(0,dp(54),1));
        modes.addView(manualButton,new LinearLayout.LayoutParams(0,dp(54),1));
        root.addView(text("سرعة إعادة المحاولة",14));
        speedBar=new SeekBar(this);speedBar.setMax(2);speedBar.setProgress(1);root.addView(speedBar);
        LinearLayout actions=new LinearLayout(this);root.addView(actions);
        startButton=button("▶ ابدأ تجربة 30 ثانية");stopButton=button("■ توقيف");
        actions.addView(startButton,new LinearLayout.LayoutParams(0,dp(60),2));
        actions.addView(stopButton,new LinearLayout.LayoutParams(0,dp(60),1));
        root.addView(text("وقف التجربة إلا سمعت صوت غير عادي أو حسّيتي بسخونية. التطبيق كيستعمل Camera2 وما كيزيدش قوة موتور العدسة.",12));
        autoButton.setOnClickListener(v -> {if(!running&&autoSupported){manualMode=false;refreshMode();bg.post(() -> applyAuto());}});
        manualButton.setOnClickListener(v -> {if(!running&&manualSupported){manualMode=true;refreshMode();bg.post(() -> applyManual(0f));}});
        startButton.setOnClickListener(v -> begin());
        stopButton.setOnClickListener(v -> halt("تم إيقاف التجربة"));
        speedBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar v,int p,boolean user){gapMs=p==0?2600:p==1?1500:850;}
            public void onStartTrackingTouch(SeekBar v){}
            public void onStopTrackingTouch(SeekBar v){}
        });
        cameraSpinner.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(android.widget.AdapterView<?> a){}
            public void onItemSelected(android.widget.AdapterView<?> a,View v,int pos,long id){
                if(pos<0||pos>=ids.size())return;
                String next=ids.get(pos);
                if(!next.equals(selectedId)){
                    halt("تغيير الكاميرا");selectedId=next;readCapabilities();openSelected();
                }
            }
        });
        preview.setSurfaceTextureListener(new TextureView.SurfaceTextureListener(){
            public void onSurfaceTextureAvailable(SurfaceTexture s,int w,int h){openSelected();}
            public void onSurfaceTextureSizeChanged(SurfaceTexture s,int w,int h){}
            public boolean onSurfaceTextureDestroyed(SurfaceTexture s){bg.post(() -> closeCamera());return true;}
            public void onSurfaceTextureUpdated(SurfaceTexture s){}
        });
        refreshMode();
        if(checkSelfPermission(Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED)discover();
        else requestPermissions(new String[]{Manifest.permission.CAMERA},123);
    }
    @Override public void onRequestPermissionsResult(int req,String[] perms,int[] grants){
        super.onRequestPermissionsResult(req,perms,grants);
        if(req==123 && grants.length>0 && grants[0]==PackageManager.PERMISSION_GRANTED)discover();
        else report("صلاحية الكاميرا ضرورية باش تخدم التجربة");
    }
    private void discover(){
        try{
            ids.clear();ArrayList<String> titles=new ArrayList<>();
            for(String id:manager.getCameraIdList()){
                CameraCharacteristics c=manager.getCameraCharacteristics(id);
                Integer facing=c.get(CameraCharacteristics.LENS_FACING);
                String side=facing!=null&&facing==CameraCharacteristics.LENS_FACING_FRONT?"أمامية":
                    facing!=null&&facing==CameraCharacteristics.LENS_FACING_BACK?"خلفية":"أخرى";
                ids.add(id); titles.add("Camera "+id+"  •  "+side);
            }
            if(ids.isEmpty()){report("ما لقيتش كاميرا متاحة");return;}
            ArrayAdapter<String> ad=new ArrayAdapter<>(this,android.R.layout.simple_spinner_item,titles);
            ad.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);cameraSpinner.setAdapter(ad);
            selectedId=ids.get(0);readCapabilities();openSelected();
        }catch(Exception e){report("تعذر قراءة الكاميرا: "+e.getMessage());}
    }
    private void readCapabilities(){
        try{
            CameraCharacteristics c=manager.getCameraCharacteristics(selectedId);
            Float dist=c.get(CameraCharacteristics.LENS_INFO_MINIMUM_FOCUS_DISTANCE);
            maxDistance=dist==null?0:dist;
            manualSupported=false;autoSupported=false;
            int[] capabilities=c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
            if(capabilities!=null)for(int x:capabilities)
                if(x==CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR)manualSupported=true;
            manualSupported=manualSupported && maxDistance>0;
            int[] modes=c.get(CameraCharacteristics.CONTROL_AF_AVAILABLE_MODES);
            if(modes!=null)for(int x:modes) {
                if(x==CaptureRequest.CONTROL_AF_MODE_AUTO) {autoSupported=true;afMode=x;break;}
                if(x==CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE ||
                   x==CaptureRequest.CONTROL_AF_MODE_MACRO){autoSupported=true;afMode=x;}
            }
            manualMode=!autoSupported && manualSupported;
            refreshMode();
            report(manualSupported?"العدسة كتدعم التحكم اليدوي فالتركيز":"التحكم اليدوي ما مدعومش؛ غادي نجرب Autofocus إلا متاح");
        }catch(Exception e){report("مشكل فخصائص الكاميرا: "+e.getMessage());}
    }
    private void refreshMode(){
        ui.post(() -> {
            autoButton.setEnabled(autoSupported&&!running);
            manualButton.setEnabled(manualSupported&&!running);
            startButton.setEnabled(!running&&(manualMode?manualSupported:autoSupported));
            stopButton.setEnabled(running);
            modeText.setText("الوضع: "+(manualMode?"Manual focus":"Autofocus")
                +"  |  يدوي: "+(manualSupported?"نعم":"لا")+"  |  تلقائي: "+(autoSupported?"نعم":"لا"));
        });
    }
    private void openSelected(){
        if(!foreground||selectedId==null||!preview.isAvailable()||
            checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED)return;
        String target=selectedId;
        bg.post(() -> {
            closeCamera();
            final int generation=++cameraGeneration;
            try{
                manager.openCamera(target,new CameraDevice.StateCallback(){
                    public void onOpened(CameraDevice d){
                        if(generation!=cameraGeneration||!foreground||!target.equals(selectedId)){d.close();return;}
                        camera=d; makePreview(d,generation);
                    }
                    public void onDisconnected(CameraDevice d){d.close();if(camera==d)camera=null;report("انفصلت الكاميرا");}
                    public void onError(CameraDevice d,int error){d.close();if(camera==d)camera=null;report("خطأ كاميرا "+error);}
                },bg);
            }catch(Exception e){report("تعذر فتح الكاميرا: "+e.getMessage());}
        });
    }
    private void makePreview(CameraDevice d,int generation){
        try {
            SurfaceTexture texture=preview.getSurfaceTexture();
            if(texture==null)return;
            texture.setDefaultBufferSize(1280,720);
            surface=new Surface(texture);
            request=d.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            request.addTarget(surface);
            d.createCaptureSession(Collections.singletonList(surface),new CameraCaptureSession.StateCallback(){
                public void onConfigured(CameraCaptureSession s){
                    if(generation!=cameraGeneration||d!=camera){s.close();return;}
                    session=s;
                    if(manualMode)applyManual(0f);else applyAuto();
                    report("الكاميرا واجدة. اختار الوضع واضغط ابدأ.");
                }
                public void onConfigureFailed(CameraCaptureSession s){report("فشل إعداد المعاينة");}
            },bg);
        }catch(Exception e){report("فشل تشغيل المعاينة: "+e.getMessage());}
    }
    private void applyAuto(){
        if(session==null||request==null)return;
        try {
            request.set(CaptureRequest.CONTROL_MODE,CaptureRequest.CONTROL_MODE_AUTO);
            request.set(CaptureRequest.CONTROL_AF_MODE,afMode);
            request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
            session.setRepeatingRequest(request.build(),null,bg);
        } catch(Exception e){report("فشل Autofocus: "+e.getMessage());}
    }
    private void applyManual(float diopters){
        if(session==null||request==null||!manualSupported)return;
        try {
            request.set(CaptureRequest.CONTROL_MODE,CaptureRequest.CONTROL_MODE_AUTO);
            request.set(CaptureRequest.CONTROL_AF_MODE,CaptureRequest.CONTROL_AF_MODE_OFF);
            request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
            request.set(CaptureRequest.LENS_FOCUS_DISTANCE,Math.max(0f,Math.min(maxDistance,diopters)));
            session.setRepeatingRequest(request.build(),null,bg);
        }catch(Exception e){report("فشل التحريك اليدوي: "+e.getMessage());}
    }
    private void triggerAf(){
        if(session==null||request==null||!autoSupported)return;
        try{
            request.set(CaptureRequest.CONTROL_AF_MODE,afMode);
            request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_START);
            session.capture(request.build(),null,bg);
            request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
            session.setRepeatingRequest(request.build(),null,bg);
        }catch(Exception e){report("تعذر طلب Autofocus: "+e.getMessage());}
    }
    private void begin(){
        if(running || selectedId==null)return;
        if(manualMode&&!manualSupported || !manualMode&&!autoSupported){report("الوضع ما مدعومش");return;}
        running=true;stepCount=0;finishAt=SystemClock.elapsedRealtime()+30000;
        refreshMode();
        nextStep=new Runnable(){
            public void run(){
                if(!running)return;
                if(SystemClock.elapsedRealtime()>=finishAt){ui.post(() -> halt("سالَت التجربة بعد 30 ثانية"));return;}
                int n=++stepCount;
                if(manualMode)applyManual((n%2==0)?0f:maxDistance);
                else triggerAf();
                report("التجربة خدامة • خطوة "+n+" • "+(manualMode?"تحريك العدسة":"طلب تركيز تلقائي"));
                bg.postDelayed(this,gapMs);
            }
        };
        bg.post(nextStep);
    }
    private void halt(String message){
        running=false;refreshMode();
        bg.post(() -> {
            if(nextStep!=null){bg.removeCallbacks(nextStep);nextStep=null;}
            if(session!=null){if(manualMode)applyAuto();else applyAuto();}
        });
        report(message);
    }
    private void closeCamera(){
        cameraGeneration++;
        if(nextStep!=null){bg.removeCallbacks(nextStep);nextStep=null;}
        running=false;
        try{if(session!=null)session.close();}catch(Exception ignored){}
        session=null;request=null;
        try{if(camera!=null)camera.close();}catch(Exception ignored){}
        camera=null;
        if(surface!=null){surface.release();surface=null;}
        refreshMode();
    }
    @Override protected void onResume(){super.onResume();foreground=true;if(preview!=null&&preview.isAvailable())openSelected();}
    @Override protected void onPause(){foreground=false;running=false;bg.post(() -> closeCamera());super.onPause();}
    @Override protected void onDestroy(){cameraThread.quitSafely();super.onDestroy();}
}