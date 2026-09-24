// Original canvas pixel art. No remote assets, engine, or sprite dependencies.
export function createWorld(canvas, interact, onMove, saved = {}) {
  const ctx = canvas.getContext('2d');
  const W = 960, H = 560;
  ctx.imageSmoothingEnabled = false;
  const player = {x: Number(saved.x) || 475, y: Number(saved.y) || 431};
  const keys = new Set();
  let path = [], pending = null, last = 0, clock = 0, paused = false, near = null, step = 0, dirty = false;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const objects = [
    {id:'Philosophy', kind:'shelf', x:69,y:170,w:112,h:30,label:'Philosophy & ideas'},
    {id:'Science', kind:'shelf', x:196,y:170,w:110,h:30,label:'Science & discovery'},
    {id:'History', kind:'shelf', x:321,y:170,w:111,h:30,label:'History & memory'},
    {id:'Literature', kind:'shelf', x:529,y:170,w:111,h:30,label:'Literature & poetry'},
    {id:'Politics', kind:'shelf', x:657,y:170,w:110,h:30,label:'Politics & society'},
    {id:'Religion', kind:'shelf', x:780,y:170,w:110,h:30,label:'Religion & belief'},
    {id:'computer',kind:'desk',x:672,y:312,w:120,h:57,label:'The computer'},
    {id:'post',kind:'post',x:565,y:240,w:36,h:20,label:'Letters & time machine'},
    {id:'reader',kind:'table',x:192,y:309,w:106,h:53,label:'The reading table'},
    {id:'coffee',kind:'coffee',x:813,y:299,w:64,h:46,label:'Make a little coffee'},
    {id:'fire',kind:'fire',x:65,y:302,w:80,h:48,label:'Warm your hands'},
    {id:'sofa',kind:'sofa',x:365,y:266,w:101,h:38,label:'Take a quiet moment'},
    {id:'editor',kind:'person',x:535,y:350,w:18,h:12,label:'Margot · editor',shirt:'#aa6e67',hair:'#6b392f',skin:'#e8b38c'},
    {id:'researcher',kind:'person',x:326,y:245,w:18,h:12,label:'Ada · researcher',shirt:'#87a7a0',hair:'#332c2a',skin:'#ba815c'},
    {id:'professor',kind:'person',x:237,y:418,w:18,h:12,label:'Elias · professor',shirt:'#97826b',hair:'#d0c8b2',skin:'#dba785'},
    {id:'publisher',kind:'person',x:762,y:438,w:18,h:12,label:'Jules · publisher',shirt:'#8b88a0',hair:'#392f33',skin:'#d8a080'},
    {id:'friend',kind:'person',x:460,y:288,w:18,h:12,label:'Noor · friend',shirt:'#b99457',hair:'#3b2b2a',skin:'#bd8059'},
    {id:'cat',kind:'cat',x:575,y:436,w:24,h:12,label:'Miso · head of naps'},
    {id:'plant1',kind:'plant',x:56,y:427,w:28,h:28,label:'A small discovery'},
    {id:'plant2',kind:'plant',x:867,y:425,w:28,h:28,label:'A small discovery'},
    {id:'globe',kind:'globe',x:480,y:183,w:24,h:24,label:'A small discovery'},
    {id:'plant3',kind:'plant',x:48,y:215,w:26,h:25,label:'A very happy fern'},
    {id:'plant4',kind:'plant',x:889,y:224,w:25,h:25,label:'A very happy fern'},
  ];
  const r = (x,y,w,h,c) => {ctx.fillStyle=c;ctx.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));};
  const poly = (points,c) => {ctx.fillStyle=c;ctx.beginPath();points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();ctx.fill();};
  const line = (x,y,x2,y2,c,width=1) => {ctx.strokeStyle=c;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x2,y2);ctx.stroke();};
  const noise = (x,y) => {const n=Math.sin(x*127.1+y*311.7)*43758.5453;return n-Math.floor(n);};
  const label = (s,x,y,color='#d7bb88',size=8) => {ctx.font=`${size}px monospace`;ctx.textAlign='center';ctx.fillStyle=color;ctx.fillText(s,x,y);};
  function shadow(x,y,w,h){r(x-3,y+3,w+9,h,'#2b211c45');}
  function lamp(x,y){
    r(x-2,y-21,4,24,'#6e573d');r(x-10,y+2,20,4,'#5f4731');
    r(x-8,y-38,16,5,'#e6bb69');r(x-13,y-33,26,11,'#d5a956');r(x-15,y-22,30,3,'#f4d58c');
    r(x-8,y-30,3,8,'#eacc7e');r(x+7,y-30,3,8,'#ab7c42');
  }
  function plant(x,y,w){
    shadow(x,y,w,8);r(x+4,y-2,w-8,15,'#956447');r(x+2,y-5,w-4,5,'#c18c59');r(x+7,y+1,4,9,'#b88254');
    r(x+w/2-2,y-33,4,29,'#688064');
    for(let i=0;i<7;i++){const side=i%2?1:-1;const yy=y-10-i*5;poly([[x+w/2,yy+8],[x+w/2+side*(15-i/2),yy-4],[x+w/2+side*12,yy-9],[x+w/2,yy]],i%2?'#597258':'#8c9f70');}
  }
  function shelf(o){const {x,y,w}=o;
    shadow(x,y,w,18);r(x-3,y-99,w+6,116,'#533d31');r(x,y-97,w,106,'#332b28');
    const colors=['#758d80','#aa665c','#d1ad70','#667991','#927894','#b58756','#c4bd9a','#647c70'];
    for(let row=0;row<3;row++){
      const yy=y-70+row*31;r(x+5,yy+2,w-10,4,'#aa754b');r(x+5,yy+6,w-10,4,'#473025');
      let xx=x+8;
      while(xx<x+w-12){const seed=noise(xx,row);const bw=4+Math.floor(seed*6);const bh=15+Math.floor(noise(xx,5+row)*12);const c=colors[Math.floor(seed*colors.length)];
        r(xx,yy-bh,bw,bh,c);r(xx+1,yy-bh+3,bw-2,1,'#e7d39b88');r(xx+1,yy-4,bw-2,1,'#e7d39b77');r(xx+bw-1,yy-bh,1,bh,'#0003');xx+=bw+2;
      }
    }
    r(x-3,y-103,w+6,7,'#bc8956');r(x-5,y-96,w+10,3,'#d09a62');r(x,y-94,5,108,'#94623e');r(x+w-5,y-94,5,108,'#8c5939');r(x-2,y+10,w+4,8,'#aa784a');
    r(x+w/2-34,y-119,68,12,'#4b3d30');r(x+w/2-33,y-118,66,1,'#b69b68');label(o.id.toUpperCase(),x+w/2,y-109,'#dec694',7);
  }
  function person(x,y,shirt='#7b9a8d',hair='#58402d',skin='#ddb089',walking=false){
    const sway=walking?Math.round(Math.sin(clock*12)*2):0;
    r(x-10,y+2,23,5,'#30262955');
    r(x-6,y-6,5,10+sway,'#433c3b');r(x+2,y-6,5,10-sway,'#433c3b');r(x-7,y+3+sway,6,3,'#302c30');r(x+2,y+3-sway,7,3,'#302c30');
    r(x-8,y-24,17,18,shirt);r(x-11,y-21,4,13+sway,shirt);r(x+9,y-21,4,13-sway,shirt);r(x-11,y-9+sway,4,5,skin);r(x+9,y-9-sway,4,5,skin);
    r(x-2,y-26,6,5,skin);r(x-7,y-39,16,15,skin);r(x-10,y-39,4,10,hair);r(x+8,y-39,4,10,hair);r(x-7,y-43,17,7,hair);r(x-9,y-39,12,4,hair);
    r(x-4,y-33,2,2,'#332b2a');r(x+5,y-33,2,2,'#332b2a');r(x+1,y-28,3,1,'#a66c55');r(x-5,y-20,2,11,'#ffffff18');r(x+6,y-19,2,11,'#0002');
  }
  function drawObject(o){const {x,y,w,h}=o;
    if(o.kind==='post'){shadow(x,y,w,h);r(x,y,w,h,'#876043');r(x+4,y-8,w-8,19,'#ead7ac');line(x+4,y-8,x+w/2,y+3,'#987653');line(x+w-4,y-8,x+w/2,y+3,'#987653');r(x+w/2-3,y,6,6,'#a34f42');label('POST',x+w/2,y+32,'#dec694',7);return;}
    if(o.kind==='shelf')return shelf(o);
    if(o.kind==='person'){person(x+w/2,y+h,o.shirt,o.hair,o.skin);if(o.id==='professor'){r(x+4,y-21,7,4,'#d9caaa');r(x+13,y-21,7,4,'#d9caaa');r(x+11,y-20,2,1,'#55453c');}return;}
    if(o.kind==='plant')return plant(x,y,w);
    if(o.kind==='cat'){
      shadow(x,y,w,6);const bob=reduced?0:Math.floor(Math.sin(clock*2)*1.2);r(x,y-6+bob,22,12,'#d0a271');r(x+16,y-14+bob,13,13,'#dcb480');r(x+16,y-17+bob,4,5,'#dcb480');r(x+25,y-17+bob,4,5,'#dcb480');r(x+19,y-8+bob,2,2,'#463b32');r(x+25,y-8+bob,2,2,'#463b32');r(x+22,y-5+bob,2,2,'#a87366');r(x-7,y-3+bob,10,4,'#bd8f61');r(x-9,y-8+bob,4,8,'#bd8f61');r(x+4,y-6+bob,3,7,'#af8054');r(x+10,y-6+bob,3,7,'#af8054');label('z',x+32,y-25-Math.sin(clock)*3,'#d6c8ad',9);return;
    }
    if(o.kind==='desk'){
      shadow(x,y,w,h);r(x+7,y+22,8,34,'#4e382b');r(x+w-15,y+22,8,34,'#4e382b');r(x,y-4,w,33,'#a37750');r(x,y+23,w,9,'#64462f');r(x+3,y,w-6,4,'#c59462');r(x+5,y+32,31,16,'#805838');r(x+17,y+36,7,2,'#d4b376');
      r(x+41,y-36,43,30,'#c2b79b');r(x+44,y-33,37,22,'#343f3b');r(x+47,y-30,31,17,'#7bada0');r(x+51,y-27,14,2,'#c3e0bc');r(x+51,y-22,23,1,'#c3e0bc');r(x+51,y-18,17,1,'#c3e0bc');r(x+59,y-6,7,8,'#ada387');r(x+51,y+1,24,4,'#c6baa0');r(x+41,y+10,43,10,'#c5b89b');for(let k=0;k<9;k++)r(x+44+k*4,y+12,2,5,'#8c856f');
      lamp(x+15,y-4);r(x+96,y+6,10,11,'#d4c5a3');r(x+105,y+8,4,6,'#d4c5a3');r(x+98,y+6,6,2,'#61442e');
      r(x+49,y+49,28,17,'#4d695b');r(x+46,y+41,34,15,'#6e8b72');r(x+46,y+54,4,12,'#42382d');r(x+76,y+54,4,12,'#42382d');
      label('THE IDEA MACHINE',x+w/2,y+81,'#c7a97d',7);return;
    }
    if(o.kind==='table'){
      shadow(x,y,w,h);r(x+8,y+21,7,29,'#573d2c');r(x+w-15,y+21,7,29,'#573d2c');r(x,y-6,w,35,'#ad8159');r(x,y+22,w,9,'#765036');r(x+3,y-3,w-6,3,'#c99a6c');
      r(x+15,y+4,31,19,'#ece0b8');r(x+29,y+5,1,17,'#a28b67');for(let k=0;k<4;k++){r(x+18,y+8+k*3,8,1,'#a69978');r(x+32,y+8+k*3,10,1,'#a69978');}
      r(x+59,y+8,24,4,'#778b7c');r(x+61,y+3,23,4,'#c3916a');r(x+58,y-2,25,4,'#836679');lamp(x+89,y-4);
      r(x-21,y+6,17,25,'#7b5a47');r(x-26,y,7,34,'#a07955');r(x+w+4,y+6,17,25,'#7b5a47');r(x+w+21,y,7,34,'#a07955');return;
    }
    if(o.kind==='sofa'){
      shadow(x,y,w,h);r(x,y-15,w,34,'#56665d');r(x+5,y-24,w-10,28,'#728172');r(x+6,y-21,w-12,4,'#8a947e');r(x+6,y+5,w-12,22,'#81907a');r(x+5,y+28,w-10,6,'#434c43');r(x-5,y-6,13,34,'#91a087');r(x+w-8,y-6,13,34,'#7b8d76');r(x+31,y+5,1,19,'#566c5b');r(x+63,y+5,1,19,'#566c5b');r(x+16,y-3,16,16,'#c5a577');r(x+17,y-2,14,2,'#d7bc8d');r(x+69,y-2,16,16,'#aa7161');r(x+8,y+33,6,5,'#4a3528');r(x+w-14,y+33,6,5,'#4a3528');return;
    }
    if(o.kind==='fire'){
      shadow(x,y,w,h);r(x,y-57,w,87,'#8a7966');for(let row=0;row<7;row++)for(let col=0;col<4;col++){r(x+col*21+(row%2?8:0),y-54+row*11,18,8,row%2?'#9e8970':'#a69074');}
      r(x+16,y-28,w-32,59,'#3e3029');r(x+22,y+11,w-44,13,'#745039');
      for(let i=0;i<5;i++){const hh=13+Math.sin(clock*5+i*2)*8;poly([[x+22+i*7,y+23],[x+25+i*7,y-hh],[x+34+i*7,y+23]],i%2?'#ec9d4c':'#d4763a');r(x+26+i*6,y+17,5,6,'#f6c570');}
      r(x-7,y-59,w+14,8,'#c2a781');r(x-3,y-51,w+6,4,'#68503b');r(x-6,y+30,w+12,12,'#b39a7a');r(x+8,y-69,8,10,'#d5c49f');r(x+w-18,y-72,9,13,'#b68568');return;
    }
    if(o.kind==='coffee'){
      shadow(x,y,w,h);r(x,y,w,28,'#a47c55');r(x+3,y+28,w-6,17,'#64472e');r(x+5,y+32,22,9,'#8d633e');r(x+34,y+32,22,9,'#8d633e');r(x+17,y+35,4,2,'#c4a571');r(x+43,y+35,4,2,'#c4a571');
      r(x+18,y-21,21,22,'#ae794b');r(x+21,y-26,15,5,'#cba06a');r(x+26,y-30,5,4,'#6f4c34');r(x+39,y-18,8,4,'#cba06a');r(x+44,y-17,4,13,'#ae794b');r(x+39,y-5,8,4,'#ae794b');poly([[x+18,y-18],[x+8,y-23],[x+11,y-12],[x+18,y-6]],'#cba06a');r(x+49,y-6,9,9,'#e4d2af');
      for(let i=0;i<3;i++)r(x+29+Math.sin(clock*2+i)*3,y-35-i*5,2,3,'#d7c8ac88');label('BUT FIRST, COFFEE',x+w/2,y+61,'#c7a97d',7);return;
    }
    if(o.kind==='globe'){
      shadow(x,y,w,10);r(x+10,y-1,4,19,'#95784f');r(x+3,y+15,19,4,'#9b7e51');r(x+1,y-25,24,23,'#698e85');r(x-2,y-20,30,14,'#698e85');r(x+6,y-23,8,8,'#a9b08a');r(x+13,y-12,9,8,'#b7b38b');r(x+3,y-10,8,4,'#98a882');line(x-3,y-27,x+28,y,'#d4b270',2);return;
    }
  }
  function backdrop(){
    r(0,0,W,H,'#292632');r(17,23,926,514,'#191e2a');
    // Rainy skyline behind the upper wall, with little occupied windows.
    const sky=ctx.createLinearGradient(0,0,0,135);sky.addColorStop(0,'#34394c');sky.addColorStop(1,'#9d7b76');ctx.fillStyle=sky;ctx.fillRect(23,23,914,147);
    r(600,41,20,18,'#d7c9a2');r(604,38,14,23,'#d7c9a2');r(610,37,12,18,'#505061');
    for(let i=0;i<29;i++){const x=23+i*33;const hh=25+noise(i,1)*65;const y=132-hh;r(x,y,30,hh,'#444454');r(x+4,y-5,23,5,'#494755');for(let a=0;a<4;a++)for(let b=0;b<2;b++)if(noise(i+a,b)>.45)r(x+7+b*12,y+9+a*14,4,6,noise(a,i)>.5?'#d9ad76':'#837b77');}
    // Cutaway walls and inlaid floor.
    r(27,155,906,350,'#634733');r(27,145,906,12,'#b08359');r(27,155,12,351,'#48352c');r(921,155,12,351,'#49362d');
    for(let row=0;row<22;row++){
      const y=159+row*16;
      for(let col=0;col<12;col++){let x=39+col*84-(row%2)*42;const width=Math.min(82,921-x);if(width<=0)continue;const c=['#9c704d','#a77952','#a47550','#ad7d55','#a07350'][Math.floor(noise(col,row)*5)];r(Math.max(39,x),y,width-(x<39?39-x:0),15,c);line(Math.max(40,x+5),y+6,Math.min(918,x+width-7),y+6,'#684a321c');if(noise(col,row)>.75)r(Math.max(41,x+18),y+10,17,1,'#684a3233');}
    }
    r(39,155,882,13,'#30262555');r(39,167,882,2,'#b38d6033');r(26,497,908,12,'#4a372c');r(22,508,916,10,'#aa8157');r(22,518,916,6,'#4f3b30');r(34,524,893,4,'#141a2488');
    // Tall window behind the central globe, bookshelves backed by timber paneling.
    for(let i=0;i<7;i++){const x=44+i*128;r(x,43,111,111,'#594238');r(x+4,46,103,107,'#a47b55');r(x+7,50,97,99,'#775942');}
    r(437,37,86,112,'#503e37');r(443,40,74,108,'#c0986c');r(449,45,62,98,'#5b6672');
    for(let i=0;i<3;i++){r(454+i*17,76-i*8,14,62+i*8,'#404956');for(let j=0;j<3;j++)r(458+i*17,86+j*16-i*6,4,7,'#c7a777');}
    r(477,44,5,101,'#b79364');r(449,89,62,5,'#b79364');r(439,143,82,7,'#d0a875');
    // Rugs with woven borders, diamonds, and fringe.
    r(330,325,287,141,'#6c513d55');r(333,321,280,138,'#50665f');r(339,327,268,126,'#c0a371');r(344,332,258,116,'#738779');r(350,338,246,104,'#4f6c62');
    for(let x=340;x<609;x+=9){r(x,318,3,5,'#c4ab7d');r(x,459,3,5,'#c4ab7d');}
    for(let x=355;x<595;x+=20){poly([[x,340],[x+5,345],[x,350],[x-5,345]],'#c1a978');poly([[x,430],[x+5,435],[x,440],[x-5,435]],'#c1a978');}
    poly([[475,351],[533,390],[475,430],[417,390]],'#a99670');poly([[475,360],[520,390],[475,421],[430,390]],'#56766a');poly([[475,370],[501,390],[475,410],[449,390]],'#c0a97b');poly([[475,379],[491,390],[475,402],[460,390]],'#6c8878');
    for(const x of [370,575])for(const y of [371,409]){poly([[x,y-8],[x+9,y],[x,y+8],[x-9,y]],'#b3a37d');r(x-2,y-2,4,4,'#536c5f');}
    r(170,279,153,104,'#93724e44');r(174,278,145,98,'#b39970');r(180,284,133,86,'#79564b');r(184,288,125,78,'#a47a64');
    // Side table, a handwritten note, standing lamps, and trailing ivy.
    r(375,319,69,17,'#4c3a2e44');r(379,310,60,17,'#a17951');r(384,327,5,11,'#62472e');r(429,327,5,11,'#62472e');r(389,309,19,10,'#dfcba3');r(393,312,11,1,'#9a855f');r(419,309,7,8,'#e5cba0');
    lamp(156,246);lamp(631,288);r(154,246,4,20,'#6f5439');r(146,265,21,4,'#6d5337');r(629,288,4,21,'#6f5439');r(621,308,21,4,'#6d5337');
    for(let i=0;i<16;i++){const x=53+i*57;r(x,34,28,4,'#596c50');r(x+7,36,11,6,'#809065');r(x+22,32,9,5,'#718660');if(i%3===0){r(x+9,41,3,15,'#62754f');r(x+6,49,9,4,'#809265');}}
    // Welcome mat and slippers at the entrance.
    r(407,479,144,27,'#7b5941');r(412,483,134,17,'#b49368');label('STAY A LITTLE WHILE',479,494,'#634c39',7);
  }
  function blocked(x,y){return x<49||x>910||y<205||y>487||objects.some(o=>o.kind!=='person'&&o.kind!=='cat'&&x>o.x-9&&x<o.x+o.w+9&&y>o.y-5&&y<o.y+o.h+8);}
  if(blocked(player.x,player.y)){player.x=475;player.y=431;}
  function route(tx,ty,target=null){
    const cell=10, cols=96, start=[Math.round(player.x/cell),Math.round(player.y/cell)];
    const goal=[Math.round(tx/cell),Math.round(ty/cell)];
    const queue=[start], previous=new Map([[start.join(','),null]]);let end=null;
    for(let i=0;i<queue.length;i++){
      const [x,y]=queue[i];const px=x*cell,py=y*cell;
      const reached=target?Math.hypot(px-(target.x+target.w/2),py-(target.y+target.h))<48:Math.abs(x-goal[0])+Math.abs(y-goal[1])<=1;
      if(reached){end=[x,y];break;}
      for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){const nx=x+dx,ny=y+dy;const key=`${nx},${ny}`;if(nx<0||nx>=cols||previous.has(key)||blocked(nx*cell,ny*cell))continue;previous.set(key,[x,y]);queue.push([nx,ny]);}
    }
    path=[];if(!end)return;let p=end;while(p){path.push({x:p[0]*cell,y:p[1]*cell});p=previous.get(p.join(','));}path.reverse();pending=target;
  }
  function act(o){if(o)interact(o.kind==='shelf'?'catalog':o.id,o.kind==='shelf'?o.id:null);}
  canvas.addEventListener('pointerdown',e=>{
    canvas.focus();const bounds=canvas.getBoundingClientRect();const x=(e.clientX-bounds.left)*W/bounds.width,y=(e.clientY-bounds.top)*H/bounds.height;
    const hit=[...objects].reverse().find(o=>x>=o.x-8&&x<=o.x+o.w+8&&y>=o.y-(o.kind==='shelf'?105:40)&&y<=o.y+o.h+8);
    if(hit)route(hit.x+hit.w/2,hit.y+hit.h+20,hit);else route(x,y);
  });
  window.addEventListener('keydown',e=>{if(paused||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)||e.ctrlKey||e.metaKey||e.altKey)return;const key=e.key.toLowerCase();if(['w','a','s','d','arrowup','arrowleft','arrowdown','arrowright','e'].includes(key)){e.preventDefault();if(key==='e'&&!e.repeat)act(near);else keys.add(key);}});
  window.addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));
  window.addEventListener('blur',()=>keys.clear());
  function frame(now){
    const dt=Math.min((now-last)/1000,.05)||0;last=now;if(!reduced)clock+=dt;
    let dx=0,dy=0;
    if(!paused){dx=(keys.has('d')||keys.has('arrowright')?1:0)-(keys.has('a')||keys.has('arrowleft')?1:0);dy=(keys.has('s')||keys.has('arrowdown')?1:0)-(keys.has('w')||keys.has('arrowup')?1:0);
      if(dx||dy){path=[];pending=null;}
      else if(path.length){const next=path[0];dx=next.x-player.x;dy=next.y-player.y;if(Math.hypot(dx,dy)<3){path.shift();dx=dy=0;}}
      const mag=Math.hypot(dx,dy);if(mag){const speed=104*dt;const nx=player.x+dx/mag*speed,ny=player.y+dy/mag*speed;if(!blocked(nx,player.y))player.x=nx;if(!blocked(player.x,ny))player.y=ny;dirty=true;}
      if(!path.length&&pending){const o=pending;pending=null;act(o);}
    }
    backdrop();
    const layers=[...objects,{kind:'player',y:player.y-6,h:6}].sort((a,b)=>(a.y+a.h)-(b.y+b.h));
    for(const o of layers){if(o.kind==='player'){person(player.x,player.y,'#7f9f92','#594235','#e4b28a',Boolean(dx||dy));poly([[player.x,player.y-55],[player.x-4,player.y-60],[player.x+4,player.y-60]],'#eed092');}else drawObject(o);}
    // Amber pools from the lamps and fireplace; retain crisp sprites underneath.
    for(const [x,y,size,alpha] of [[104,327,105,.16],[697,311,95,.09],[256,319,75,.08],[475,260,130,.05]]){const glow=ctx.createRadialGradient(x,y,2,x,y,size);glow.addColorStop(0,`rgba(255,190,93,${alpha})`);glow.addColorStop(1,'rgba(255,190,93,0)');ctx.fillStyle=glow;ctx.fillRect(x-size,y-size,size*2,size*2);}
    if(!reduced){for(let i=0;i<70;i++){const x=25+noise(i,0)*910;const y=24+(noise(i,1)*120+clock*36)%120;line(x,y,x-2,y+5,'#d1cbca22');}for(let i=0;i<17;i++){const x=70+noise(i,4)*810+Math.sin(clock*.3+i)*8,y=200+noise(i,6)*250+Math.sin(clock*.4+i)*7;r(x,y,1,1,'#f7d99c55');}}
    near=objects.map(o=>({o,d:Math.hypot(player.x-(o.x+o.w/2),player.y-(o.y+o.h))})).filter(v=>v.d<66).sort((a,b)=>a.d-b.d)[0]?.o||null;
    const hint=document.getElementById('interaction');hint.hidden=!near||paused;if(near)hint.textContent=`E · ${near.label}`;
    step+=dt;if(step>2&&dirty&&!paused){onMove({x:Math.round(player.x),y:Math.round(player.y)});step=0;dirty=false;}
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  return {pause(value){paused=value;keys.clear();path=[];pending=null;},player};
}
