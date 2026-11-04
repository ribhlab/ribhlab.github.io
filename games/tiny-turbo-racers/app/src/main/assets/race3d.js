/* Tiny Turbo Racers — original offline WebGL 3D renderer.
 * 2026 RibhLab. No libraries, textures, network access or third-party assets.
 * Real 3D triangle meshes, perspective camera, depth-buffered racing environment.
 */
(function () {
 "use strict";
 const TAU=Math.PI*2;
 function hex(s){s=s.replace("#","");if(s.length===3)s=s.split("").map(a=>a+a).join("");const n=parseInt(s,16);return [(n>>16&255)/255,(n>>8&255)/255,(n&255)/255]}
 const mix=(a,b,t)=>a.map((v,i)=>v*(1-t)+b[i]*t);
 const norm=a=>{const d=Math.hypot(...a)||1;return a.map(v=>v/d)};
 const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
 function perspective(fov,aspect,near,far){
  const f=1/Math.tan(fov/2),nf=1/(near-far);
  return new Float32Array([f/aspect,0,0,0,0,f,0,0,0,0,(far+near)*nf,-1,0,0,2*far*near*nf,0]);
 }
 function lookAt(eye,at){
  const z=norm(eye.map((v,i)=>v-at[i])),x=norm(cross([0,1,0],z)),y=cross(z,x);
  return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,
   -x.reduce((s,v,i)=>s+v*eye[i],0),-y.reduce((s,v,i)=>s+v*eye[i],0),
   -z.reduce((s,v,i)=>s+v*eye[i],0),1]);
 }
 class Mesh {
  constructor(){this.data=[];this.origin=[0,0,0];this.angle=0}
  pose(x,y,z,angle,fn){
   const old=this.origin,oldA=this.angle;this.origin=[x,y,z];this.angle=angle||0;
   fn();this.origin=old;this.angle=oldA;
  }
  v(p,c,n){const a=this.angle,cs=Math.cos(a),sn=Math.sin(a);
   const x=p[0]*cs+p[2]*sn+this.origin[0],z=-p[0]*sn+p[2]*cs+this.origin[2];
   this.data.push(x,p[1]+this.origin[1],z,c[0],c[1],c[2],n[0],n[1],n[2]);
  }
  tri(a,b,c,col){
   const u=b.map((v,i)=>v-a[i]),v=c.map((w,i)=>w-a[i]),n=norm(cross(u,v)),cl=typeof col==="string"?hex(col):col;
   this.v(a,cl,n);this.v(b,cl,n);this.v(c,cl,n);
  }
  quad(a,b,c,d,col){this.tri(a,b,c,col);this.tri(a,c,d,col)}
  box(x,y,z,w,h,d,col){
   const l=x-w/2,r=x+w/2,b=y-h/2,t=y+h/2,f=z-d/2,k=z+d/2;
   const c=typeof col==="string"?hex(col):col;
   this.quad([l,t,f],[r,t,f],[r,t,k],[l,t,k],mix(c,[1,1,1],.20));
   this.quad([l,b,k],[r,b,k],[r,b,f],[l,b,f],mix(c,[0,0,0],.30));
   this.quad([l,b,f],[r,b,f],[r,t,f],[l,t,f],c);
   this.quad([r,b,k],[l,b,k],[l,t,k],[r,t,k],mix(c,[0,0,0],.08));
   this.quad([l,b,k],[l,b,f],[l,t,f],[l,t,k],mix(c,[0,0,0],.17));
   this.quad([r,b,f],[r,b,k],[r,t,k],[r,t,f],mix(c,[1,1,1],.08));
  }
  sphere(x,y,z,rx,ry,rz,col,lat=5,lon=9){
   const c=typeof col==="string"?hex(col):col;
   const pt=(th,ph)=>[x+Math.sin(th)*Math.cos(ph)*rx,y+Math.cos(th)*ry,z+Math.sin(th)*Math.sin(ph)*rz];
   for(let a=0;a<lat;a++)for(let b=0;b<lon;b++){
    const t0=a*Math.PI/lat,t1=(a+1)*Math.PI/lat,p0=b*TAU/lon,p1=(b+1)*TAU/lon;
    this.quad(pt(t0,p0),pt(t0,p1),pt(t1,p1),pt(t1,p0),c);
   }
  }
  cylinder(x,y,z,r,h,col,segments=9){
   const c=typeof col==="string"?hex(col):col;
   const top=y+h/2,bot=y-h/2;
   for(let j=0;j<segments;j++){let a=j*TAU/segments,b=(j+1)*TAU/segments;
    const p=[x+Math.cos(a)*r,z+Math.sin(a)*r],q=[x+Math.cos(b)*r,z+Math.sin(b)*r];
    this.quad([p[0],bot,p[1]],[q[0],bot,q[1]],[q[0],top,q[1]],[p[0],top,p[1]],c);
    this.tri([x,top,z],[p[0],top,p[1]],[q[0],top,q[1]],mix(c,[1,1,1],.14));
   }
  }
  wheel(x,y,z,r){
   this.sphere(x,y,z,.30,r,r,"#20283d",5,9);
   this.sphere(x+(x>0?.26:-.26),y,z,.055,r*.55,r*.55,"#d8f5ff",4,9);
   this.sphere(x+(x>0?.30:-.30),y,z,.06,r*.23,r*.23,"#ffdd59",4,7);
  }
  cone(x,y,z,r,h,col,segments=9){
   const c=typeof col==="string"?hex(col):col;
   for(let i=0;i<segments;i++){
    const a=i*TAU/segments,b=(i+1)*TAU/segments;
    this.tri([x+Math.cos(a)*r,y,z+Math.sin(a)*r],[x+Math.cos(b)*r,y,z+Math.sin(b)*r],[x,y+h,z],i%2?c:mix(c,[1,1,1],.16));
   }
  }
 }
 const sky=["#74daff","#76d9fa","#ffa6ed","#88d9ec"];
 const ground=["#77d67a","#f9dc91","#9be786","#79d88e"];
 const roads=["#5e718f","#596f83","#89658f","#667d89"];
 const body=["#ff4650","#368ef7","#ffe04b","#44d795"];
 function car(m,x,z,color,kind,yaw=0,boost=false,bounce=0){
  m.pose(x,.05+bounce,z,yaw,()=>{
   // soft ground shadow
   m.sphere(0,.025,0,1.64,.045,2.32,"#38576c",3,10);
   // four thick rounded wheels (real 3D)
   [-1,1].forEach(s=>[-1,1].forEach(f=>m.wheel(s*1.14,.57,f*1.09,.48)));
   m.box(0,.92,0,2.22,.86,3.30,color);
   m.box(0,.69,-1.54,2.17,.32,.23,"#f3f9ff");
   m.box(0,.67,1.56,2.17,.22,.25,"#ffe9f8");
   // front glass / cabin and metallic roof
   m.box(0,1.60,.12,1.66,.93,1.68,"#78b8ec");
   m.box(0,2.07,.10,1.43,.15,1.62,mix(hex(color),[1,1,1],.20));
   m.box(0,1.61,-.77,1.43,.75,.10,"#9bdcfa");
   m.box(0,1.61,.97,1.43,.75,.10,"#9bdcfa");
   // eyes and highlights, visible from behind for small racers
   [-.41,.41].forEach(e=>{
    m.sphere(e,1.66,-.89,.27,.32,.13,"#ffffff");
    m.sphere(e+.05,1.65,-1.00,.135,.20,.08,"#254f83");
    m.sphere(e+.1,1.73,-1.06,.055,.065,.025,"#ffffff");
   });
   m.sphere(0,.99,-1.74,.37,.10,.09,"#8f315c",4,9); // smile
   m.sphere(0,.89,-1.78,.22,.04,.05,"#ffb4cd",3,7);
   [-.81,.81].forEach(e=>m.sphere(e,.91,-1.70,.23,.15,.10,"#fff5b4",4,8));
   m.box(0,1.37,1.59,2.14,.14,.37,color); // spoiler
   if(kind===1)m.box(0,2.18,.30,.50,.09,.75,"#f8faff");
   if(kind===2){m.sphere(.86,2.18,.30,.30,.18,.28,"#ff90c4");m.sphere(.90,2.22,.23,.14,.18,.18,"#fff7b4")}
   if(kind===3){m.box(0,2.19,.16,1.32,.12,.35,"#fce89a");m.sphere(-.4,2.34,.09,.18,.15,.16,"#c4faff");}
   // shiny stripes and cheerful star motif
   m.box(0,1.37,-1.14,.22,.025,.50,"#f7f8ff");
   if(boost){[-.63,.63].forEach(e=>{m.cone(e,.5,-2.0,.19,.82,"#ffe559");m.cone(e,.5,-2.3,.12,.55,"#ff892b")})}
  });
 }
 function sign(m,x,z,col="#fff"){
  m.box(x,2,z,.19,4,.17,"#fff5da");
  m.box(x,4,z,.85,.62,.17,col);
 }
 function tree(m,x,z,seed){
  const y=.9+seed*.5;
  m.cylinder(x,y,z,.24,y*2,"#b88758",7);
  m.sphere(x,2.7+seed*.4,z,.85,1.28,.77,seed>.5?"#4acb72":"#78d965",5,8);
  m.sphere(x+.46,2.6,z+.15,.5,.72,.5,"#a2f486",4,7);
 }
 function prop(m,x,z,type,idx,t){
  const p=Math.abs(Math.sin(idx*12.34+type*4.5));
  if(type===0){
   const h=3.6+p*6,col=["#ffb957","#f786ba","#68adff","#b5eb78"][Math.abs(idx)%4];
   m.box(x,h/2,z,3.2,h,3.1,col);
   m.box(x,h*.70,z-1.57,1.9,.35,.1,"#f7f8ff");
   m.box(x,h*.35,z-1.60,1.8,.38,.1,"#e8f5ff");
   m.box(x,h*.57,z-1.60,1.8,.38,.1,"#e8f5ff");
   m.box(x,h+.27,z,.32,.54,.3,"#ffe86a");
  }else if(type===1){
   m.cylinder(x,2.2,z,.27,4.4,"#b77d57");
   for(let j=0;j<5;j++){const a=j*TAU/5;
    m.sphere(x+Math.cos(a)*1.2,4.35,z+Math.sin(a)*1.2,1.65,.24,.54,"#53ce7b",4,7);}
   m.sphere(x,4.55,z,.45,.45,.45,"#ffe58a");
  }else if(type===2){
   m.cylinder(x,1.75,z,.20,3.50,"#fcfff0",7);
   m.sphere(x,3.68,z,1.05,1.12,.55,["#ff6aac","#a66def","#ffe47b"][Math.abs(idx)%3],7,10);
   m.sphere(x+.25,4.01,z-.32,.24,.25,.19,"#ffffff",4,7);
   m.sphere(x+1.1,.36,z+.8,.7,.48,.7,"#a9e887",4,8);
  }else{
   m.cone(x,0,z,2.3,5.3,"#7f9d87",8);
   m.sphere(x-1.4,.65,z,1.3,.72,.95,"#59c78a",4,8);
   // a friendly low-poly dino in the hills
   if(idx%3===0){
    m.sphere(x+.7,1.2,z+.4,1.6,.83,.69,"#51bb8a");
    m.cylinder(x+1.6,2.2,z+.4,.34,2.8,"#51bb8a",7);
    m.sphere(x+1.6,3.7,z+.4,.72,.66,.65,"#65d9a0");
    m.sphere(x+1.35,3.88,z-.17,.10,.13,.08,"#fff");
   }
  }
  // trackside pennants and balloon bunches
  if(idx%4===0){
   m.cylinder(x-2,1.8,z,.065,3.6,"#fff");
   m.sphere(x-2.6,3.8+Math.sin(t+idx)*.12,z,.47,.58,.47,"#ff65a9",5,8);
   m.sphere(x-1.4,4.15+Math.sin(t+idx)*.10,z,.45,.54,.44,"#ffdc52",5,8);
  }
 }
 function arch(m,z,t){
  const main="#ffffff",red="#fc618d";
  for(const s of [-1,1]){m.box(s*7.8,3.4,z,.95,6.8,.92,main);m.box(s*7.8,5.15,z,.98,.9,.98,red)}
  m.box(0,6.7,z,16.6,1.2,1.04,main);
  for(let i=0;i<16;i++)m.box(-7.6+i*1.04,6.7,z-.54,1.03,.58,.05,i%2?"#23375d":"#f9fdff");
  m.sphere(0,7.3,z,1.0,.98,.18,"#ffe44f",5,11);
  m.sphere(0,7.3,z-.25,.49,.46,.08,"#fff9c5",4,8);
 }
 function twinkle(m,x,y,z,s){
  const gold="#ffe447";m.sphere(x,y,z,s,s,s*.38,gold,5,9);
  m.box(x,y,z-s*.1,s*.43,s*3.0,s*.22,"#fff2ab");
  m.box(x,y,z-s*.1,s*3.0,s*.43,s*.22,"#fff2ab");
 }
 function compile(gl,type,source){
  const shader=gl.createShader(type);gl.shaderSource(shader,source);gl.compileShader(shader);
  if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(shader));
  return shader;
 }
 class RacerRenderer {
  constructor(canvas){
   this.canvas=canvas;this.gl=canvas.getContext("webgl",{alpha:false,antialias:true,depth:true,preserveDrawingBuffer:false});
   if(!this.gl)throw Error("WebGL unavailable");
   const gl=this.gl;
   const vert=compile(gl,gl.VERTEX_SHADER,
    "attribute vec3 aPos; attribute vec3 aColor; attribute vec3 aNormal;"+
    "uniform mat4 uProj; uniform mat4 uView; varying vec3 vColor; varying float vFog;"+
    "void main(){ vec4 v=uView*vec4(aPos,1.0);"+
    "float light=0.72+0.28*max(dot(normalize(aNormal),normalize(vec3(0.34,0.85,-0.50))),0.0);"+
    "vColor=aColor*light;vFog=clamp((-v.z-55.0)/130.0,0.0,0.80);gl_Position=uProj*v;}");
   const frag=compile(gl,gl.FRAGMENT_SHADER,
    "precision mediump float; varying vec3 vColor;varying float vFog;uniform vec3 uSky;"+
    "void main(){gl_FragColor=vec4(mix(vColor,uSky,vFog),1.0);}");
   const program=gl.createProgram();gl.attachShader(program,vert);gl.attachShader(program,frag);
   gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
   this.program=program;gl.useProgram(program);
   this.loc={pos:gl.getAttribLocation(program,"aPos"),color:gl.getAttribLocation(program,"aColor"),
    normal:gl.getAttribLocation(program,"aNormal"),proj:gl.getUniformLocation(program,"uProj"),
    view:gl.getUniformLocation(program,"uView"),sky:gl.getUniformLocation(program,"uSky")};
   this.buffer=gl.createBuffer();
   gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
   for(const [key,off] of [["pos",0],["color",3],["normal",6]]){
    const loc=this.loc[key];gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,3,gl.FLOAT,false,36,off*4);
   }
   gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);
   gl.clearDepth(1.0);
   this.ready=true;
   canvas.addEventListener("webglcontextlost",e=>{e.preventDefault();this.ready=false});
  }
  frame(r,garage=false){
   if(!this.ready)return false;
   const gl=this.gl,c=this.canvas;
   // Resolution cap preserves battery on entry-level Android devices.
   const ratio=Math.min(1.5,window.devicePixelRatio||1),W=Math.max(2,Math.round(c.clientWidth*ratio)),H=Math.max(2,Math.round(c.clientHeight*ratio));
   if(c.width!==W||c.height!==H){c.width=W;c.height=H}
   gl.viewport(0,0,W,H);
   const world=r.world||0,p=r.progress||0,t=r.t||0,boost=!!(r.boost>0);
   const skyRGB=hex(garage?"#9fe9ff":sky[world]);
   gl.clearColor(...skyRGB,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
   const m=new Mesh(),road=roads[world],grass=ground[world];
   m.box(0,-.28,95,410,.45,360,grass);
   m.sphere(-42,47,146,9,9,4,"#fff2a6",7,10);
   for(let i=0;i<7;i++){
    const x=-60+i*21,z=75+(i%3)*21;
    m.sphere(x,25+i%2*4,z,7,2.3,2.5,"#ffffff",4,8);
    m.sphere(x+4,25+i%2*4,z,4,1.7,2.1,"#fcffff",4,7);
   }
   if(garage){
    m.cylinder(0,-.15,0,4.3,.4,"#58bcef",22);
    m.cylinder(0,-.38,0,5.2,.35,"#e9faff",22);
    for(let j=0;j<9;j++)twinkle(m,Math.sin(j*2)*5,2.5+(j%3)*.9,Math.cos(j*2)*4,.18);
    car(m,0,0,r.color||body[0],r.car||0,Math.sin(t*.45)*.35,false,Math.sin(t*3)*.03);
   }else{
    const curve=z=>3*Math.sin((p+z)*.015)-3*Math.sin(p*.015);
    for(let z=-25;z<190;z+=4){
     const z1=z+4,c0=curve(z),c1=curve(z1),y=.02;
     m.quad([c0-7.15,y,z],[c0+7.15,y,z],[c1+7.15,y,z1],[c1-7.15,y,z1],road);
     const stripe=Math.floor((p+z)/8)%2===0;
     for(let s of [-1,1]){
      const x0=c0+s*7.28,x1=c1+s*7.28,edgeColor=Math.floor((p+z)/5)%2===0?"#fc5562":"#ffffff";
      m.quad([x0-s*.28,.08,z],[x0+s*.28,.08,z],[x1+s*.28,.08,z1],[x1-s*.28,.08,z1],edgeColor);
      if(stripe)m.quad([c0+s*2.45-.08,.07,z],[c0+s*2.45+.08,.07,z],
        [c1+s*2.45+.08,.07,z1],[c1+s*2.45-.08,.07,z1],"#fff9e2");
     }
     if(Math.floor((p+z)/8)%2===0) m.quad([c0-.12,.07,z],[c0+.12,.07,z],[c1+.12,.07,z1],[c1-.12,.07,z1],"#fff7dd");
    }
    for(let j=Math.floor((p-24)/18);j<Math.floor((p+174)/18);j++){
     const z=j*18-p;if(z< -28||z>180)continue;
     const center=curve(z);
     for(let side of [-1,1]){
      const x=center+side*(13+Math.sin(j*1.87)*2);
      prop(m,x,z,world,j,t);
      m.box(center+side*8.15,1.05,z,.28,1.55,.23,"#fffdf3");
      m.box(center+side*8.15,1.84,z,.30,.22,5.2,"#ffaf69");
     }
    }
    const archZ=65-(p%150);if(archZ> -17&&archZ<175)arch(m,archZ,t);
    for(let i=0;i<3;i++){
      const z=12+i*13+Math.sin(t*.8+i*1.4)*2.6;
      const x=curve(z)+[-3.8,0,3.8][i]+Math.sin(t*.5+i)*.25;
      car(m,x,z,body[i+1],i+1,Math.sin(t+i)*.035,false,Math.sin(t*8+i)*.028);
    }
    for(let j=0;j<3;j++){
      const index=(r.nextStar||0)+j,d=80+index*112-p;
      if(d>-8&&d<180)twinkle(m,curve(d)+Math.sin(index*2.6)*4.75,1.75+Math.sin(t*5+index)*.35,d,.65);
    }
    const playerX=(r.lane||0)*4.75;
    car(m,playerX,0,r.color||body[0],r.car||0,(r.turn||0)*.09,boost,Math.sin(t*12)*.032);
    if(boost){for(let i=0;i<8;i++){const zz=-4-(i*2.4+t*9)%16;twinkle(m,playerX+Math.sin(i*3)*1.5,.5,zz,.18)}}
   }
   const playerX=garage?0:(r.lane||0)*4.75;
   const eye=garage?[6.5,4.8,-9.8]:[playerX*.55,6.6,-14.8];
   const at=garage?[0,1.25,0]:[playerX*.23,1.3,24];
   gl.uniformMatrix4fv(this.loc.proj,false,perspective(garage?Math.PI/3.3:Math.PI/3.0,W/H,.08,340));
   gl.uniformMatrix4fv(this.loc.view,false,lookAt(eye,at));
   gl.uniform3fv(this.loc.sky,new Float32Array(skyRGB));
   const data=new Float32Array(m.data);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
   gl.bufferData(gl.ARRAY_BUFFER,data,gl.DYNAMIC_DRAW);
   gl.drawArrays(gl.TRIANGLES,0,data.length/9);
   return true;
  }
 }
 let race3D=null,garage3D=null,badRace=false,badGarage=false;
 window.TinyTurbo3D={
  get supported(){return !badRace},
  race(canvas,state){
   try{if(badRace)return false;if(!race3D)race3D=new RacerRenderer(canvas);return race3D.frame(state)}
   catch(e){badRace=true;console.warn("3D unavailable; switch to Canvas fallback",e);return false}
  },
  garage(canvas,state){
   try{if(badGarage)return false;if(!garage3D)garage3D=new RacerRenderer(canvas);return garage3D.frame(state,true)}
   catch(e){badGarage=true;console.warn("Garage 3D unavailable; switch to Canvas fallback",e);return false}
  }
 };
})();