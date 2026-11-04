/* Tiny Turbo Racers — kid-friendly original racing audio synthesized offline.
 * No copyrighted samples, network downloads, tracking, SDKs or external audio files.
 */
(function(){
 "use strict";
 const AudioCtor=window.AudioContext||window.webkitAudioContext;
 const notes=[0,4,7,12,7,4,2,7,0,4,9,12,9,7,4,2];
 const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
 class Sound {
  constructor(){this.ctx=null;this.enabled=true;this.playing=false;this.nextMusic=0;this.lastSkid=0;
   this.engine1=null;this.engine2=null;this.filter=null;this.driveGain=null;this.windGain=null;}
  startAudio(){
   if(!this.enabled||!AudioCtor)return false;
   try{
    if(!this.ctx){
     const a=this.ctx=new AudioCtor();
     const master=this.master=a.createGain();master.gain.value=.48;master.connect(a.destination);
     const filter=this.filter=a.createBiquadFilter();filter.type="lowpass";filter.frequency.value=450;filter.Q.value=.5;
     const driveGain=this.driveGain=a.createGain();driveGain.gain.value=0;filter.connect(driveGain);driveGain.connect(master);
     for(let k=0;k<2;k++){
      const osc=a.createOscillator();osc.type=k?"triangle":"sawtooth";osc.frequency.value=k?84:59;
      const gain=a.createGain();gain.gain.value=k?.12:.16;osc.connect(gain);gain.connect(filter);osc.start();
      if(k)this.engine2=osc;else this.engine1=osc;
     }
     const samples=Math.round(a.sampleRate*.8),buf=a.createBuffer(1,samples,a.sampleRate),ch=buf.getChannelData(0);
     let seed=56345;for(let i=0;i<samples;i++){seed=(seed*16807)%2147483647;ch[i]=(seed/1073741823)-1}
     const noise=a.createBufferSource();noise.buffer=buf;noise.loop=true;
     const windFilter=a.createBiquadFilter();windFilter.type="lowpass";windFilter.frequency.value=520;
     const windGain=this.windGain=a.createGain();windGain.gain.value=0;
     noise.connect(windFilter);windFilter.connect(windGain);windGain.connect(master);noise.start();
    }
    if(this.ctx.state==="suspended")this.ctx.resume().catch(()=>{});
    return true;
   }catch(e){console.warn("Sound unavailable",e);return false}
  }
  setEnabled(enabled){
   this.enabled=!!enabled;
   if(!this.enabled){this.stop();if(this.ctx&&this.ctx.state==="running")this.ctx.suspend().catch(()=>{})}
   else if(this.ctx&&this.ctx.state==="suspended")this.ctx.resume().catch(()=>{});
  }
  tone(frequency,duration=.13,volume=.06,type="sine",delay=0,endFreq=null){
   if(!this.enabled||!this.startAudio())return;
   try{
    const a=this.ctx,start=a.currentTime+delay,osc=a.createOscillator(),gain=a.createGain();
    osc.type=type;osc.frequency.setValueAtTime(Math.max(25,frequency),start);
    if(endFreq!==null)osc.frequency.exponentialRampToValueAtTime(Math.max(25,endFreq),start+duration);
    gain.gain.setValueAtTime(.0001,start);
    gain.gain.linearRampToValueAtTime(volume,start+.014);
    gain.gain.exponentialRampToValueAtTime(.0001,start+duration);
    osc.connect(gain);gain.connect(this.master);osc.start(start);osc.stop(start+duration+.025);
   }catch(e){}
  }
  menu(freq=610,dur=.075,type="sine"){this.tone(freq,dur,.048,type)}
  countdown(value){
   if(value>0)this.tone(370+value*90,.22,.11,"triangle");
   else{this.tone(880,.25,.16,"triangle");this.tone(1180,.28,.11,"sine",.085)}
  }
  raceStart(){
   if(!this.startAudio())return;
   this.playing=true;this.nextMusic=0;
   this.tone(250,.34,.09,"sawtooth",0,470);
  }
  stop(){
   this.playing=false;
   if(!this.ctx)return;
   const now=this.ctx.currentTime;
   if(this.driveGain)this.driveGain.gain.setTargetAtTime(0,now,.12);
   if(this.windGain)this.windGain.gain.setTargetAtTime(0,now,.12);
  }
  pause(){this.stop();this.tone(340,.12,.07,"sine")}
  resume(){this.playing=true;this.tone(510,.10,.07,"sine")}
  star(){
   [0,4,7,12].forEach((n,i)=>this.tone(520*Math.pow(2,n/12),.18,.09,"sine",i*.065));
  }
  turbo(){this.tone(170,.48,.12,"sawtooth",0,760);this.tone(410,.31,.07,"triangle",.06,920)}
  skid(){this.tone(210,.12,.036,"sawtooth",0,125)}
  lap(){this.tone(570,.16,.075,"triangle");this.tone(860,.20,.07,"triangle",.10)}
  victory(){
   this.stop();
   [0,4,7,12,16,19].forEach((n,i)=>this.tone(395*Math.pow(2,n/12),.36,.10,"triangle",i*.135));
  }
  frame(r,turn){
   if(!this.ctx||!this.enabled||!this.playing)return;
   const a=this.ctx,now=a.currentTime;
   if(!r||r.paused||r.countdown>-.6){this.driveGain.gain.setTargetAtTime(0,now,.06);this.windGain.gain.setTargetAtTime(0,now,.06);return}
   const boosted=r.boost>0,speed=boosted?1:.72;
   const rpm=68+Math.min(58,(r.progress%300)*.07)+(boosted?48:0);
   this.engine1.frequency.setTargetAtTime(rpm,now,.075);
   this.engine2.frequency.setTargetAtTime(rpm*1.93,now,.08);
   this.filter.frequency.setTargetAtTime(boosted?980:520,now,.09);
   this.driveGain.gain.setTargetAtTime(boosted?.38:.23,now,.07);
   this.windGain.gain.setTargetAtTime(.025+speed*.022,now,.1);
   if(turn&&now-this.lastSkid>1.4 && Math.abs(r.lane)>.78){this.skid();this.lastSkid=now}
   // Cheerful original synthesized music, kept low enough for engine feedback.
   if(now>this.nextMusic){
    const i=Math.floor(r.t*4)%notes.length;
    this.tone(330*Math.pow(2,notes[i]/12),.13,.020,"triangle");
    this.nextMusic=now+.22;
   }
  }
 }
 window.TurboSound=new Sound();
 document.addEventListener("visibilitychange",()=>{
  if(document.hidden)window.TurboSound.stop();
 });
})();