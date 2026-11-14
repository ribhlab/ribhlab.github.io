package com.ribhlab.focusrescue;

import android.Manifest;
import android.app.Activity;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Rect;
import android.util.Range;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.*;
import android.media.*;
import java.io.ByteArrayOutputStream;
import android.view.*;
import android.widget.*;
import java.util.*;

public class MainActivity extends Activity {
    private CameraManager manager;
    private HandlerThread cameraThread;
    private Handler bg, ui = new Handler(Looper.getMainLooper());
    private TextureView preview;
    private TextView status, modeText, afLiveText, cameraInfoText, diagnosisText;
    private Spinner cameraSpinner;
    private Button startButton, stopButton, autoButton, manualButton;
    private Button micButton, playButton, diagnosisButton;
    private CheckBox clickSound, fastZoom;
    private TextView zoomText;
    private TextView gainLabel;
    private int playbackGain = 6;
    private ToneGenerator commandTone;
    private volatile boolean recording = false, playing = false;
    private volatile AudioRecord microphone;
    private volatile AudioTrack player;
    private volatile byte[] recordedClip;
    private static final int AUDIO_RATE = 16000;
    private static final long RECORD_MS = 8000L;
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
    private int gapMs = 550;
    private int zoomIntervalMs = 100;
    private long finishAt = 0;
    private Runnable nextStep, zoomStep;
    private float zoomMin = 1f, zoomMax = 1f, zoomPosition = 1f;
    private boolean zoomSupported=false, useZoomRatio=false;
    private Rect zoomSensorRect;
    private float zoomProgress = 0f;
    private int zoomDirection = 1;

    private int cameraGeneration = 0;
    // Smart diagnostic: bounded asynchronous AF checks using real camera results.
    private boolean diagnosing = false, diagnosticWaiting = false;
    private int diagnosticAttempt=0, diagnosticFocused=0, diagnosticFailed=0, diagnosticTimeouts=0;
    private long diagnosticTriggerAt=0, lastAfUi=0;
    private Runnable diagnosticTimeout;
    private String cameraDetails = "";
    private final CameraCaptureSession.CaptureCallback resultsCallback = new CameraCaptureSession.CaptureCallback(){
        @Override public void onCaptureCompleted(CameraCaptureSession s,CaptureRequest req,TotalCaptureResult result){
            if(s!=session || !foreground)return;
            Integer state=result.get(CaptureResult.CONTROL_AF_STATE);
            Integer lens=result.get(CaptureResult.LENS_STATE);
            Float diopters=result.get(CaptureResult.LENS_FOCUS_DISTANCE);
            long now=SystemClock.elapsedRealtime();
            if(now-lastAfUi>400){
                lastAfUi=now;
                String value="AF: "+afName(state)+"  |  العدسة: "+(lens==null?"غير متاح":lens==CaptureResult.LENS_STATE_MOVING?"كتتحرك":"ثابتة");
                if(diopters!=null)value+="  |  Focus: "+String.format(java.util.Locale.US,"%.2f D",diopters);
                final String line=value;
                ui.post(() -> {if(afLiveText!=null)afLiveText.setText(line);});
            }
            if(diagnosing && diagnosticWaiting && state!=null &&
                now-diagnosticTriggerAt>180 &&
                (state==CaptureResult.CONTROL_AF_STATE_FOCUSED_LOCKED ||
                 state==CaptureResult.CONTROL_AF_STATE_NOT_FOCUSED_LOCKED)){
                diagnosticWaiting=false;
                if(diagnosticTimeout!=null)bg.removeCallbacks(diagnosticTimeout);
                if(state==CaptureResult.CONTROL_AF_STATE_FOCUSED_LOCKED)diagnosticFocused++;
                else diagnosticFailed++;
                int step=diagnosticAttempt;
                int count=diagnosticFocused;
                int fail=diagnosticFailed;
                ui.post(() -> diagnosisText.setText("اختبار "+step+"/3: "+
                    (count>0?"نجح "+count+" | ":"")+"فشل "+fail+
                    " | بدون نتيجة "+diagnosticTimeouts));
                bg.postDelayed(() -> startDiagnosticAttempt(),650);
            }
        }
    };
    private String afName(Integer s){
        if(s==null)return "ماكايناش بيانات";
        switch(s){
            case CaptureResult.CONTROL_AF_STATE_INACTIVE:return "غير نشط";
            case CaptureResult.CONTROL_AF_STATE_PASSIVE_SCAN:return "بحث تلقائي";
            case CaptureResult.CONTROL_AF_STATE_PASSIVE_FOCUSED:return "ركز تلقائياً";
            case CaptureResult.CONTROL_AF_STATE_ACTIVE_SCAN:return "كيبحث على التركيز";
            case CaptureResult.CONTROL_AF_STATE_FOCUSED_LOCKED:return "Focus OK";
            case CaptureResult.CONTROL_AF_STATE_NOT_FOCUSED_LOCKED:return "Focus FAILED";
            case CaptureResult.CONTROL_AF_STATE_PASSIVE_UNFOCUSED:return "غير مركز";
            default:return "رمز "+s;
        }
    }

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
        TextView title=text("RibhLab • Focus Rescue v1.3",24); title.setTextColor(Color.rgb(99,228,185));root.addView(title);
        root.addView(text("تجربة تحريك تركيز العدسة - ما كتصلحش العطب الميكانيكي المضمون",13));
        cameraSpinner=new Spinner(this);root.addView(cameraSpinner,new LinearLayout.LayoutParams(-1,dp(54)));
        preview=new TextureView(this); root.addView(preview,new LinearLayout.LayoutParams(-1,dp(265)));
        status=text("جاري فحص الكاميرات...",14);root.addView(status);

        modeText=text("التركيز: غير محدد",13);root.addView(modeText);
        cameraInfoText=text("Camera2: انتظار البيانات",13);root.addView(cameraInfoText);
        afLiveText=text("AF: انتظار نتائج المستشعر",14);root.addView(afLiveText);
        diagnosisButton=button("🔎 Smart Focus Diagnosis — اختبار 3 مرات");
        root.addView(diagnosisButton,new LinearLayout.LayoutParams(-1,dp(58)));
        diagnosisText=text("شخّص الكاميرا بلا Zoom وبلا تكرار سريع للأوامر. النتائج من Camera2 ولا تثبت جودة الصورة.",13);
        root.addView(diagnosisText);
        diagnosisButton.setOnClickListener(v -> startDiagnostic());
        LinearLayout modes=new LinearLayout(this); modes.setOrientation(LinearLayout.HORIZONTAL);root.addView(modes);
        autoButton=button("Autofocus");manualButton=button("Manual sweep");
        modes.addView(autoButton,new LinearLayout.LayoutParams(0,dp(54),1));
        modes.addView(manualButton,new LinearLayout.LayoutParams(0,dp(54),1));
        fastZoom = new CheckBox(this);
        fastZoom.setText("Zoom In / Out متواصل مع التركيز (أقصى زوم مدعوم)");
        fastZoom.setTextColor(Color.rgb(231,242,239));
        fastZoom.setChecked(false);
        root.addView(fastZoom);
        zoomText = text("Zoom: فحص إمكانيات الكاميرا...",14);
        root.addView(zoomText);
        root.addView(text("سرعة الوضع اليدوي والزوم (اختبار Smart Diagnosis مستقل وآمن)",14));
        speedBar=new SeekBar(this);speedBar.setMax(2);speedBar.setProgress(2);root.addView(speedBar);
        LinearLayout actions=new LinearLayout(this);root.addView(actions);
        startButton=button("▶ ابدأ تجربة 30 ثانية");stopButton=button("■ توقيف");
        actions.addView(startButton,new LinearLayout.LayoutParams(0,dp(60),2));
        actions.addView(stopButton,new LinearLayout.LayoutParams(0,dp(60),1));

        root.addView(text("🔊 الاستماع لحركة الكاميرا",19));
        clickSound=new CheckBox(this);
        clickSound.setText("صوت إلكتروني قصير مع كل أمر تحريك (ماشي صوت الموتور الحقيقي)");
        clickSound.setTextColor(Color.rgb(231,242,239));
        clickSound.setChecked(true);
        root.addView(clickSound);
        commandTone=new ToneGenerator(AudioManager.STREAM_MUSIC,75);
        micButton=button("🎙 سجّل صوت العدسة بالميكروفون (8 ثوان)");
        playButton=button("▶ سمع التسجيل المكبّر");
        root.addView(micButton,new LinearLayout.LayoutParams(-1,dp(58)));
        root.addView(playButton,new LinearLayout.LayoutParams(-1,dp(58)));
        playButton.setEnabled(false);
        gainLabel=text("تكبير صوت الميكروفون: ×6",14);
        root.addView(gainLabel);
        SeekBar gainBar=new SeekBar(this);
        gainBar.setMax(11);gainBar.setProgress(5);root.addView(gainBar);
        gainBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar bar,int progress,boolean fromUser){
                playbackGain=progress+1;
                gainLabel.setText("تكبير صوت الميكروفون: ×"+playbackGain);
            }
            public void onStartTrackingTouch(SeekBar bar){}
            public void onStopTrackingTouch(SeekBar bar){}
        });
        micButton.setOnClickListener(v -> recordLensAudio());
        playButton.setOnClickListener(v -> playRecordedAudio());
        root.addView(text("الميكروفون كيسجّل الصوت الحقيقي اللي حد الهاتف، ومن بعد كيشغّلو مكبّر. الضجيج حتى هو غادي يتكبّر. التسجيل مؤقت فالذاكرة وما كيتحفظش فملف.",12));
        root.addView(text("وقف التجربة إلا سمعت صوت غير عادي أو حسّيتي بسخونية. التطبيق كيستعمل Camera2 وما كيزيدش قوة موتور العدسة.",12));
        autoButton.setOnClickListener(v -> {if(!running&&autoSupported){manualMode=false;refreshMode();bg.post(() -> applyAuto());}});
        manualButton.setOnClickListener(v -> {if(!running&&manualSupported){manualMode=true;refreshMode();bg.post(() -> applyManual(0f));}});
        startButton.setOnClickListener(v -> begin());
        stopButton.setOnClickListener(v -> halt("تم إيقاف التجربة"));
        speedBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar v,int p,boolean user){
                gapMs=p==0?1200:p==1?550:180;
                zoomIntervalMs=p==0?260:p==1?140:70;
            }
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

        if(req==123){
            if(grants.length>0 && grants[0]==PackageManager.PERMISSION_GRANTED)discover();
            else report("صلاحية الكاميرا ضرورية باش تخدم التجربة");
        } else if(req==124){
            if(grants.length>0 && grants[0]==PackageManager.PERMISSION_GRANTED)recordLensAudio();
            else report("خاص صلاحية الميكروفون باش تسمع تسجيل الصوت الحقيقي");
        }
    }
    private void discover(){
        try{
            ids.clear();ArrayList<String> titles=new ArrayList<>();
            for(String id:manager.getCameraIdList()){
                CameraCharacteristics c=manager.getCameraCharacteristics(id);
                Integer facing=c.get(CameraCharacteristics.LENS_FACING);
                String side=facing!=null&&facing==CameraCharacteristics.LENS_FACING_FRONT?"أمامية":
                    facing!=null&&facing==CameraCharacteristics.LENS_FACING_BACK?"خلفية":"أخرى";

                ids.add(id);
                float[] focal=c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
                String focalInfo="";
                if(focal!=null&&focal.length>0){
                    StringBuilder fl=new StringBuilder();
                    for(int fi=0;fi<Math.min(focal.length,4);fi++){
                        if(fi>0)fl.append("/");
                        fl.append(String.format(java.util.Locale.US,"%.1f",focal[fi]));
                    }
                    focalInfo=" • "+fl+"mm";
                }
                titles.add("Camera2 ID "+id+" • "+side+focalInfo);
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
            float[] focals=c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
            StringBuilder spec=new StringBuilder("Camera2 ID "+selectedId);
            if(focals!=null&&focals.length>0){
                spec.append(" • بُعد بؤري: ");
                for(int i=0;i<Math.min(focals.length,4);i++){
                    if(i>0)spec.append("/");
                    spec.append(String.format(java.util.Locale.US,"%.1f",focals[i]));
                }
                spec.append(" mm");
            }
            if(Build.VERSION.SDK_INT>=28){
                Set<String> physical=c.getPhysicalCameraIds();
                if(!physical.isEmpty())spec.append(" • عدسات مرتبطة: ").append(physical.toString());
            }
            spec.append(" • ممكن بعض عدسات S22 Ultra ما تظهرش منفصلة فـ Camera2");
            cameraDetails=spec.toString();
            ui.post(()-> cameraInfoText.setText(cameraDetails));
            zoomMin=1f;zoomMax=1f;zoomPosition=1f;
            zoomSensorRect=c.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
            useZoomRatio=false;
            if(Build.VERSION.SDK_INT>=30){
                Range<Float> range=c.get(CameraCharacteristics.CONTROL_ZOOM_RATIO_RANGE);
                if(range!=null && range.getUpper()!=null && range.getUpper()>1.01f){
                    zoomMin=1f;zoomMax=range.getUpper();
                    useZoomRatio=true;
                }
            }
            if(!useZoomRatio){
                Float max=c.get(CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM);
                if(max!=null && max>1.01f && zoomSensorRect!=null){
                    zoomMax=max;
                }
            }
            zoomSupported=zoomMax>1.01f;
            ui.post(()->{
                fastZoom.setEnabled(zoomSupported);
                zoomText.setText(zoomSupported?"Zoom مدعوم: 1× → "+String.format(java.util.Locale.US,"%.1f",zoomMax)+"×"+
                    (useZoomRatio?" (Device zoom)":" (Digital crop)") :
                    "Zoom متحرك ما مدعومش فهاد الكاميرا");
            });
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

            autoButton.setEnabled(autoSupported&&!running&&!diagnosing);
            manualButton.setEnabled(manualSupported&&!running&&!diagnosing);
            diagnosisButton.setEnabled(autoSupported&&!running&&!diagnosing&&!recording&&session!=null);
            startButton.setEnabled(!running&&!diagnosing&&(manualMode?manualSupported:autoSupported));
            stopButton.setEnabled(running||diagnosing);
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

                    refreshMode();
                    report("الكاميرا واجدة. جرّب Smart Diagnosis وشوف AF State.");
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
            session.setRepeatingRequest(request.build(),resultsCallback,bg);
        } catch(Exception e){report("فشل Autofocus: "+e.getMessage());}
    }
    private void applyManual(float diopters){
        if(session==null||request==null||!manualSupported)return;
        try {
            request.set(CaptureRequest.CONTROL_MODE,CaptureRequest.CONTROL_MODE_AUTO);
            request.set(CaptureRequest.CONTROL_AF_MODE,CaptureRequest.CONTROL_AF_MODE_OFF);
            request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
            request.set(CaptureRequest.LENS_FOCUS_DISTANCE,Math.max(0f,Math.min(maxDistance,diopters)));
            session.setRepeatingRequest(request.build(),resultsCallback,bg);
        }catch(Exception e){report("فشل التحريك اليدوي: "+e.getMessage());}
    }
    private void triggerAf(){
        if(session==null||request==null||!autoSupported)return;
        try{
            request.set(CaptureRequest.CONTROL_AF_MODE,afMode);
            request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_START);
            session.capture(request.build(),null,bg);
            request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
            session.setRepeatingRequest(request.build(),resultsCallback,bg);
        }catch(Exception e){report("تعذر طلب Autofocus: "+e.getMessage());}
    }

    private void startDiagnostic(){
        if(!foreground || !autoSupported || session==null || request==null || diagnosing || running || recording){
            report("خاص كاميرا واجدة ووضع Autofocus مدعوم باش نبداو التشخيص");
            return;
        }
        diagnosing=true; diagnosticWaiting=false;
        diagnosticAttempt=0;diagnosticFocused=0;diagnosticFailed=0;diagnosticTimeouts=0;
        if(fastZoom!=null)fastZoom.setChecked(false);
        manualMode=false;
        refreshMode();
        diagnosisText.setText("التشخيص: 3 محاولات بمهلة لكل محاولة. وجه الهاتف لهدف ثابت ومضاء.");
        bg.post(() -> {
            stopZoom();
            startDiagnosticAttempt();
        });
    }
    private void startDiagnosticAttempt(){
        if(!diagnosing || !foreground || session==null || request==null)return;
        if(diagnosticAttempt>=3){
            finishDiagnostic(false);
            return;
        }
        diagnosticAttempt++;
        diagnosticWaiting=false;
        try{
            request.set(CaptureRequest.CONTROL_AF_MODE,afMode);
            request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_CANCEL);
            session.capture(request.build(),null,bg);
            request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
            session.setRepeatingRequest(request.build(),resultsCallback,bg);
            // Allow the lens to settle after CANCEL before starting one AF pass.
            bg.postDelayed(() -> {
                if(!diagnosing||!foreground||session==null||request==null)return;
                try{
                    diagnosticWaiting=true;
                    diagnosticTriggerAt=SystemClock.elapsedRealtime();
                    request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_START);
                    session.capture(request.build(),resultsCallback,bg);
                    request.set(CaptureRequest.CONTROL_AF_TRIGGER,CaptureRequest.CONTROL_AF_TRIGGER_IDLE);
                    session.setRepeatingRequest(request.build(),resultsCallback,bg);
                    final int active=diagnosticAttempt;
                    diagnosticTimeout=() -> {
                        if(!diagnosing||!diagnosticWaiting||active!=diagnosticAttempt)return;
                        diagnosticWaiting=false;
                        diagnosticTimeouts++;
                        bg.postDelayed(() -> startDiagnosticAttempt(),500);
                    };
                    bg.postDelayed(diagnosticTimeout,2600);
                    report("Smart Diagnosis • محاولة "+active+"/3 ...");
                }catch(Exception ex){diagnosticTimeouts++;diagnosticWaiting=false;
                    report("AF request error: "+ex.getMessage());
                    bg.postDelayed(() -> startDiagnosticAttempt(),500);
                }
            },350);
        }catch(Exception ex){
            diagnosticTimeouts++;
            report("Reset AF error: "+ex.getMessage());
            bg.postDelayed(() -> startDiagnosticAttempt(),500);
        }
    }
    private void finishDiagnostic(boolean stopped){
        if(!diagnosing)return;
        diagnosing=false;diagnosticWaiting=false;
        if(diagnosticTimeout!=null){bg.removeCallbacks(diagnosticTimeout);diagnosticTimeout=null;}
        if(session!=null)applyAuto();
        int total=diagnosticAttempt;
        String summary=stopped?"تم توقيف التشخيص بعد "+total+" محاولة.":
            "النتيجة Camera2: نجاح "+diagnosticFocused+"/3 • فشل "+diagnosticFailed+
            "/3 • بدون نتيجة "+diagnosticTimeouts+
            ". إذا الصورة باقي Flou رغم نجاح AF، خاص فحص الزجاج/العدسة. هاد المؤشر ما كيضمنش وضوح الصورة.";
        ui.post(() -> {diagnosisText.setText(summary);refreshMode();});
        report(summary);
    }
    private void begin(){
        if(running || diagnosing || selectedId==null)return;
        if(session==null || request==null){report("خاص الكاميرا تكون واجدة قبل التجربة");return;}
        if(manualMode&&!manualSupported || !manualMode&&!autoSupported){report("الوضع ما مدعومش");return;}
        running=true;stepCount=0;finishAt=SystemClock.elapsedRealtime()+30000;
        final boolean doZoom = fastZoom.isChecked() && zoomSupported;
        zoomProgress=0f;zoomDirection=1;
        refreshMode();
        if(doZoom)bg.post(() -> startZoom());
        nextStep=new Runnable(){
            public void run(){
                if(!running)return;
                if(SystemClock.elapsedRealtime()>=finishAt){ui.post(() -> halt("سالَت التجربة بعد 30 ثانية"));return;}
                int n=++stepCount;

                if(manualMode)applyManual((n%2==0)?0f:maxDistance);
                else triggerAf();
                // Confirmation tone is synthetic and never mixed into a genuine microphone recording.
                if(!recording)ui.post(() -> {
                    if(clickSound!=null && clickSound.isChecked() && commandTone!=null)
                        commandTone.startTone(ToneGenerator.TONE_PROP_BEEP,70);
                });
                report("تركيز "+n+" + "+(doZoom?"Zoom In/Out ":"")+
                    "• "+(manualMode?"تحريك عدسة":"Autofocus")+
                    " • "+(Math.max(0,(finishAt-SystemClock.elapsedRealtime())/1000))+" ثانية باقية");
                bg.postDelayed(this,gapMs);
            }
        };
        bg.post(nextStep);
    }

    private void halt(String message){
        if(diagnosing)bg.post(()-> finishDiagnostic(true));
        running=false;refreshMode();
        bg.post(() -> {
            if(nextStep!=null){bg.removeCallbacks(nextStep);nextStep=null;}
            stopZoom();
            if(session!=null)applyAuto();
        });
        report(message);
    }

    private void recordLensAudio(){
        if(recording){report("التسجيل خدام دابا");return;}
        if(!foreground || selectedId==null || session==null){
            report("شغّل الكاميرا حتى تبان المعاينة قبل تسجيل الصوت");
            return;
        }
        if(!(manualMode?manualSupported:autoSupported)){
            report("الكاميرا المختارة ما كتدعمش الوضع الحالي");
            return;
        }
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},124);
            return;
        }
        stopPlayback();
        if(running)halt("إيقاف التجربة السابقة");
        recording=true;
        recordedClip=null;
        micButton.setEnabled(false);playButton.setEnabled(false);
        report("جاري تسجيل صوت الميكروفون 8 ثوان مع تحريك التركيز...");
        new Thread(() -> {
            AudioRecord ar=null;
            ByteArrayOutputStream out=new ByteArrayOutputStream();
            try{
                int min=AudioRecord.getMinBufferSize(AUDIO_RATE,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT);
                if(min<=0)throw new IllegalStateException("هذا الميكروفون ما كيدعمش تسجيل 16 kHz");
                ar=new AudioRecord(MediaRecorder.AudioSource.MIC,AUDIO_RATE,AudioFormat.CHANNEL_IN_MONO,
                        AudioFormat.ENCODING_PCM_16BIT,Math.max(min,4096));
                if(ar.getState()!=AudioRecord.STATE_INITIALIZED)
                    throw new IllegalStateException("تعذر فتح الميكروفون");
                microphone=ar;
                ar.startRecording();
                if(ar.getRecordingState()!=AudioRecord.RECORDSTATE_RECORDING)
                    throw new IllegalStateException("الميكروفون ما بداش التسجيل");
                ui.post(() -> {
                    // Start the autofocus test after opening the microphone.
                    if(recording && foreground)begin();
                });
                short[] samples=new short[1024];
                long until=SystemClock.elapsedRealtime()+RECORD_MS;
                while(recording && foreground && SystemClock.elapsedRealtime()<until){
                    int n=ar.read(samples,0,samples.length);
                    if(n<0)throw new IllegalStateException("AudioRecord: "+n);
                    for(int i=0;i<n;i++){
                        int v=samples[i];
                        out.write(v&255);out.write((v>>8)&255);
                    }
                }
            }catch(Exception ex){
                report("تعذر تسجيل الصوت: "+ex.getMessage());
            }finally{
                recording=false;
                try{if(ar!=null && ar.getRecordingState()==AudioRecord.RECORDSTATE_RECORDING)ar.stop();}
                catch(Exception ignored){}
                try{if(ar!=null)ar.release();}catch(Exception ignored){}
                microphone=null;
                byte[] sound=out.toByteArray();
                boolean captured=sound.length>3000 && foreground;
                if(captured)recordedClip=sound;
                ui.post(() -> {
                    halt(captured?"تسجّل الصوت الحقيقي. كيتشغّل مكبّر دابا.":"توقف التسجيل أو ما تقطّعش صوت كافي");
                    micButton.setEnabled(true);
                    playButton.setEnabled(captured);
                    if(captured)playRecordedAudio();
                });
            }
        },"LensAudioCapture").start();
    }
    private void stopPlayback(){
        playing=false;
        AudioTrack current=player;
        player=null;
        if(current!=null){
            try{current.pause();current.flush();}catch(Exception ignored){}
            try{current.release();}catch(Exception ignored){}
        }
    }
    private void playRecordedAudio(){
        final byte[] input=recordedClip;
        if(input==null || input.length<3000){report("سجّل الصوت أولا");return;}
        stopPlayback();
        final int gain=playbackGain;
        playing=true;
        report("كتسمع الآن صوت الميكروفون ×"+gain+" (ماشي صوت مركّب)");
        new Thread(() -> {
            AudioTrack track=null;
            try{
                byte[] amplified=new byte[input.length];
                for(int i=0;i+1<input.length;i+=2){
                    int v=(short)((input[i]&255)|(input[i+1]<<8));
                    int a=Math.max(-32768,Math.min(32767,v*gain));
                    amplified[i]=(byte)(a&255);
                    amplified[i+1]=(byte)((a>>8)&255);
                }
                int min=AudioTrack.getMinBufferSize(AUDIO_RATE,AudioFormat.CHANNEL_OUT_MONO,AudioFormat.ENCODING_PCM_16BIT);
                if(min<=0)throw new IllegalStateException("لا يمكن تشغيل الصوت");
                track=new AudioTrack(AudioManager.STREAM_MUSIC,AUDIO_RATE,AudioFormat.CHANNEL_OUT_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,Math.max(min,amplified.length),AudioTrack.MODE_STATIC);
                if(track.getState()!=AudioTrack.STATE_INITIALIZED)throw new IllegalStateException("تعذر فتح مكبر الصوت");
                player=track;
                int n=track.write(amplified,0,amplified.length);
                if(n!=amplified.length)throw new IllegalStateException("الصوت ناقص");
                if(playing){
                    track.play();
                    long until=SystemClock.elapsedRealtime()+(long)input.length*1000/(AUDIO_RATE*2)+200;
                    while(playing && foreground && SystemClock.elapsedRealtime()<until)
                        SystemClock.sleep(60);
                }
            }catch(Exception ex){report("فشل تشغيل التسجيل: "+ex.getMessage());}
            finally{
                AudioTrack current=track;
                if(player==current)player=null;
                try{if(current!=null){current.stop();current.release();}}catch(Exception ignored){}
                playing=false;
            }
        },"LensAudioPlayback").start();
    }
    private void startZoom(){
        if(!running||!zoomSupported||session==null||request==null)return;
        if(zoomStep!=null)bg.removeCallbacks(zoomStep);
        zoomStep = new Runnable(){
            @Override public void run(){
                if(!running || !foreground || session==null || request==null)return;
                if(SystemClock.elapsedRealtime()>=finishAt)return;
                // Move rapidly through the full advertised zoom range, reverse at either endpoint.
                zoomProgress += zoomDirection*0.17f;
                if(zoomProgress>=1f){zoomProgress=1f;zoomDirection=-1;}
                else if(zoomProgress<=0f){zoomProgress=0f;zoomDirection=1;}
                float z=zoomMin+(zoomMax-zoomMin)*zoomProgress;
                setZoom(z);
                bg.postDelayed(this,zoomIntervalMs);
            }
        };
        bg.post(zoomStep);
    }
    private void setZoom(float ratio){
        if(!zoomSupported||session==null||request==null)return;
        ratio=Math.max(zoomMin,Math.min(zoomMax,ratio));
        try{
            if(useZoomRatio && Build.VERSION.SDK_INT>=30){
                request.set(CaptureRequest.CONTROL_ZOOM_RATIO,ratio);
            }else if(zoomSensorRect!=null){
                int width=Math.max(2,Math.round(zoomSensorRect.width()/ratio));
                int height=Math.max(2,Math.round(zoomSensorRect.height()/ratio));
                int left=zoomSensorRect.left+(zoomSensorRect.width()-width)/2;
                int top=zoomSensorRect.top+(zoomSensorRect.height()-height)/2;
                request.set(CaptureRequest.SCALER_CROP_REGION,new Rect(left,top,left+width,top+height));
            }
            session.setRepeatingRequest(request.build(),resultsCallback,bg);
            zoomPosition=ratio;
            if(zoomText!=null) {
                final float z=ratio;
                ui.post(() -> zoomText.setText("Zoom: "+String.format(java.util.Locale.US,"%.1f×",z)+
                    " | 1×–"+String.format(java.util.Locale.US,"%.1f×",zoomMax)+
                    (useZoomRatio?" • Device":" • Digital")));
            }
        }catch(Exception e){report("الكاميرا رفضات أمر zoom: "+e.getMessage());}
    }
    private void stopZoom(){
        if(zoomStep!=null){bg.removeCallbacks(zoomStep);zoomStep=null;}
        if(zoomSupported&&session!=null&&request!=null)setZoom(1f);
    }

    private void closeCamera(){
        if(diagnosing)finishDiagnostic(true);
        cameraGeneration++;
        stopZoom();
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

    @Override protected void onPause(){

        foreground=false;running=false;recording=false;diagnosing=false;diagnosticWaiting=false;
        if(diagnosticTimeout!=null)bg.removeCallbacks(diagnosticTimeout);
        AudioRecord current=microphone;
        if(current!=null)try{current.stop();}catch(Exception ignored){}
        stopPlayback();
        bg.post(() -> closeCamera());
        super.onPause();
    }
    @Override protected void onDestroy(){
        if(commandTone!=null){commandTone.release();commandTone=null;}
        cameraThread.quitSafely();super.onDestroy();
    }
}