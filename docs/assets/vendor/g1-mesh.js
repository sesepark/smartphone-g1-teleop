/* Official Unitree visual geometry; all motion comes from existing G1 body FK. */
(() => {
  const states = new WeakMap();
  // A canvas with data-theme="dark" is transparent over its CSS backdrop and adds
  // presentation lighting; other canvases keep the plain light rendering.
  function setup(canvas) {
    const dark=canvas.dataset.theme==='dark';
    const gl = canvas.getContext('webgl', {antialias:true, alpha:dark, preserveDrawingBuffer:true});
    if (!gl) { const tr=window.I18N?.tr??(text=>text); canvas.setAttribute('aria-label',tr('WebGL is unavailable. Reopen this page in a browser with hardware acceleration enabled.')); return null; }
    function shader(type, source) {
      const s=gl.createShader(type); gl.shaderSource(s,source); gl.compileShader(s);
      if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(s)); return s;
    }
    const program=gl.createProgram();
    gl.attachShader(program,shader(gl.VERTEX_SHADER,`
      attribute vec3 point; attribute vec3 normal;
      uniform vec4 quat; uniform vec3 position; uniform vec2 root;
      uniform vec4 camera; uniform vec2 size; uniform float scale;
      varying float light; varying vec3 shade; varying vec2 local; varying vec2 ground;
      vec3 rot(vec3 p){return p+2.0*cross(quat.yzw,cross(quat.yzw,p)+quat.x*p);}
      // Screen right, screen up and depth toward the viewer for a robot-frame vector.
      vec3 view(vec3 w){
        vec3 p=vec3(w.y,w.z,w.x);
        float a=p.x*camera.x+p.z*camera.y;
        float b=-p.x*camera.y+p.z*camera.x;
        return vec3(a,p.y*camera.z-b*camera.w,p.y*camera.w+b*camera.z);
      }
      void main(){
        vec3 w=rot(point)+position;
        local=point.xy; ground=w.xy-root;
        vec3 v=view(vec3(ground,w.z));
        gl_Position=vec4(2.0*v.x*scale/size.x, -0.82+2.0*v.y*scale/size.y, -v.z/10.0,1.0);
        vec3 n=normalize(rot(normal));
        light=0.45+0.55*max(0.0,dot(n,normalize(vec3(0.6,-0.8,1.0))));
        vec3 nv=view(n), key=normalize(vec3(-0.45,0.65,0.62));
        shade=vec3(max(0.0,dot(nv,key)),
                   pow(max(0.0,dot(nv,normalize(key+vec3(0.0,0.0,1.0)))),28.0),
                   pow(1.0-clamp(nv.z,0.0,1.0),2.5));
      }`));
    gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`
      precision mediump float; uniform vec3 color; uniform vec3 glow; uniform float dark; uniform float mode;
      varying float light; varying vec3 shade; varying vec2 local; varying vec2 ground;
      void main(){
        if(mode>1.5){ // contact shadow
          float a=0.6*(1.0-smoothstep(0.15,1.0,length(local)/0.42));
          gl_FragColor=vec4(0.0,0.0,0.0,a);
        }else if(mode>0.5){ // floor grid
          float a=mix(1.0,1.0-smoothstep(0.5,1.5,length(ground)),dark);
          gl_FragColor=vec4(color*a,a);
        }else if(dark>0.5){
          vec3 c=color*(0.34+0.78*shade.x)+vec3(0.32)*shade.y
                +vec3(0.30,0.48,1.0)*shade.z*0.55+glow*(0.22+0.9*shade.z+0.35*shade.x);
          gl_FragColor=vec4(c,1.0);
        }else gl_FragColor=vec4(color*light,1.0);
      }`));
    gl.linkProgram(program); if(!gl.getProgramParameter(program,gl.LINK_STATUS)) throw Error(gl.getProgramInfoLog(program));
    const u={}; for(const n of ['quat','position','root','camera','size','scale','color','glow','dark','mode'])u[n]=gl.getUniformLocation(program,n);
    const point=gl.getAttribLocation(program,'point'), normal=gl.getAttribLocation(program,'normal');
    function upload(values){const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(values),gl.STATIC_DRAW);return buffer;}
    const geoms=window.G1_MESH_DATA.geoms.map(g=>{
      const side=g.body.startsWith('left_')?'left':g.body.startsWith('right_')?'right':null;
      const limb=side&&side+'_'+(/shoulder|elbow|wrist/.test(g.body)?'arm':'leg');
      const tint=g.rgba.slice(0,3);tint[0]*=.75;tint[1]*=.86;tint[2]=Math.min(1,tint[2]*1.1+.07);
      return {body:g.body,limb,rgb:g.rgba.slice(0,3),tint,buffer:upload(g.vertices),count:g.vertices.length/6};
    });
    const grid=[];for(let i=-6;i<=6;i++)for(const p of [[-1.5,i*.25,0],[1.5,i*.25,0],[i*.25,-1.5,0],[i*.25,1.5,0]])grid.push(...p,0,0,1);
    const disk=[];for(const p of [[-1,-1],[1,-1],[1,1],[-1,-1],[1,1],[-1,1]])disk.push(p[0]*.42,p[1]*.42,0,0,0,1);
    const state={gl,program,u,point,normal,geoms,dark,gridBuffer:upload(grid),gridCount:grid.length/6,diskBuffer:upload(disk),meta:null,bodies:[]};
    states.set(canvas,state);return state;
  }
  window.drawG1Mesh=function(canvas,frame,meta,yaw,pitch,zoom,rootlock){
    const s=states.get(canvas)||setup(canvas);if(!s)return;
    const {gl,u,dark}=s,rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return;
    const dpr=Math.min(devicePixelRatio,2),cw=Math.round(rect.width*dpr),ch=Math.round(rect.height*dpr);
    if(canvas.width!==cw||canvas.height!==ch){canvas.width=cw;canvas.height=ch;}
    gl.viewport(0,0,cw,ch);
    if(dark)gl.clearColor(0,0,0,0);else gl.clearColor(.98,.985,.995,1);
    gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.useProgram(s.program);
    gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);
    gl.uniform2f(u.size,rect.width,rect.height);gl.uniform1f(u.scale,Math.min(zoom,rect.width*.55));
    gl.uniform4f(u.camera,Math.cos(yaw),Math.sin(yaw),Math.cos(pitch),Math.sin(pitch));
    gl.uniform1f(u.dark,dark?1:0);gl.uniform3f(u.glow,0,0,0);
    function buffer(b){gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.enableVertexAttribArray(s.point);gl.vertexAttribPointer(s.point,3,gl.FLOAT,false,24,0);gl.enableVertexAttribArray(s.normal);gl.vertexAttribPointer(s.normal,3,gl.FLOAT,false,24,12);}
    gl.uniform4f(u.quat,1,0,0,0);gl.uniform3f(u.position,0,0,0);gl.uniform2f(u.root,0,0);
    gl.uniform1f(u.mode,1);if(dark)gl.uniform3f(u.color,.28,.4,.78);else gl.uniform3f(u.color,.84,.87,.92);
    buffer(s.gridBuffer);gl.drawArrays(gl.LINES,0,s.gridCount);
    if(!frame?.robot||!meta){gl.uniform1f(u.mode,0);return;}
    const r=frame.robot,root=r.root_pos||[0,0,0];gl.uniform2f(u.root,rootlock?root[0]:0,rootlock?root[1]:0);
    if(dark){
      // Soft disc on the floor under the pelvis; it is a visual cue, not a contact estimate.
      gl.depthMask(false);gl.uniform1f(u.mode,2);gl.uniform3f(u.position,root[0],root[1],.002);
      buffer(s.diskBuffer);gl.drawArrays(gl.TRIANGLES,0,6);gl.depthMask(true);
    }
    gl.uniform1f(u.mode,0);
    if(s.meta!==meta){s.meta=meta;s.bodies=s.geoms.map(g=>meta.body_names.indexOf(g.body));}
    s.geoms.forEach((g,k)=>{
      const j=s.bodies[k];if(j<0)return;
      gl.uniform4fv(u.quat,r.body_quat_w[j]);gl.uniform3fv(u.position,r.body_pos_w[j]);
      const active=g.limb&&meta.enabled_limbs?.[g.limb];
      gl.uniform3fv(u.color,active?g.tint:g.rgb);
      if(dark){if(active)gl.uniform3f(u.glow,.16,.36,1);else gl.uniform3f(u.glow,0,0,0);}
      buffer(g.buffer);gl.drawArrays(gl.TRIANGLES,0,g.count);
    });
    canvas.dataset.geometry='unitree-official-mesh';
  };
})();
