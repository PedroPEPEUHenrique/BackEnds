import eventlet
eventlet.monkey_patch() # CRÍTICO PARA FUNCIONAR

from flask import Flask, request
from flask_socketio import SocketIO, emit
import random
import math
import socket

# --- CONFIGURAÇÃO DE REDE ---
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

# --- CONFIGURAÇÃO DO SERVIDOR ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lan_party_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- ESTADO DO JOGO ---
players = {}
enemies = {}
obstacles = []

# Gera Mapa
for _ in range(40):
    obstacles.append({
        'x': random.randint(-45, 45), 'z': random.randint(-45, 45),
        'w': random.randint(3, 8), 'h': random.randint(3, 7), 'd': random.randint(3, 8)
    })

# Gera Inimigos Iniciais
for i in range(5):
    eid = f"bot_{i}"
    enemies[eid] = {'id': eid, 'x': random.randint(-40, 40), 'z': random.randint(-40, 40), 'hp': 100}

# --- THREAD DE IA DOS INIMIGOS ---
def enemy_loop():
    while True:
        eventlet.sleep(0.05) # 20 ticks por segundo
        if not players: continue

        for eid, bot in enemies.items():
            # Achar jogador mais próximo
            closest_p = None
            min_dist = 9999
            
            for pid, p in players.items():
                dist = math.sqrt((bot['x'] - p['x'])**2 + (bot['z'] - p['z'])**2)
                if dist < min_dist:
                    min_dist = dist
                    closest_p = p
            
            # Perseguir e Atacar
            if closest_p:
                if min_dist > 1.5: # Se longe, anda
                    dx = closest_p['x'] - bot['x']
                    dz = closest_p['z'] - bot['z']
                    length = math.sqrt(dx**2 + dz**2)
                    if length > 0:
                        bot['x'] += (dx/length) * 0.15 # Velocidade do bot
                        bot['z'] += (dz/length) * 0.15
                elif min_dist < 1.5: # Se perto, morde
                    closest_p['hp'] -= 1 # Dano contínuo
                    socketio.emit('player_hit', {'id': closest_p['id'], 'hp': closest_p['hp']})
                    if closest_p['hp'] <= 0:
                        # Respawn player
                        closest_p['hp'] = 100
                        closest_p['x'] = random.randint(-40, 40)
                        closest_p['z'] = random.randint(-40, 40)
                        socketio.emit('player_respawn', closest_p)

        # Envia posição dos bots para todos
        socketio.emit('enemy_update', enemies)

eventlet.spawn(enemy_loop)

# --- FRONTEND ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>LAN Shooter Python</title>
    <style>
        body { margin: 0; overflow: hidden; font-family: 'Courier New', monospace; user-select: none; background: #000; }
        #ui { position: absolute; width: 100%; height: 100%; pointer-events: none; }
        #hud-top { position: absolute; top: 20px; left: 20px; color: #0f0; text-shadow: 1px 1px 3px #000; }
        .stat-box { background: rgba(0, 20, 0, 0.8); padding: 10px 20px; border: 1px solid #0f0; display: inline-block; margin-right: 10px; }
        .stat-value { font-size: 24px; font-weight: bold; }
        #crosshair { position: absolute; top: 50%; left: 50%; width: 6px; height: 6px; background: #0f0; border-radius: 50%; transform: translate(-50%, -50%); box-shadow: 0 0 5px #0f0; }
        #overlay { 
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(0,0,0,0.9); display: flex; align-items: center; justify-content: center;
            flex-direction: column; color: #0f0; pointer-events: auto; z-index: 10;
        }
        button { padding: 15px 40px; font-size: 20px; cursor: pointer; background: #004400; border: 2px solid #0f0; color: #0f0; font-family: inherit; transition: 0.2s; }
        button:hover { background: #006600; }
    </style>
</head>
<body>
    <div id="overlay">
        <h1>PYTHON LAN WAR</h1>
        <p>Inimigos Vermelhos: Mate ou Morra</p>
        <button onclick="startGame()">CONECTAR</button>
    </div>
    <div id="ui">
        <div id="hud-top">
            <div class="stat-box">HP: <span id="hp-val">100</span>%</div>
            <div class="stat-box">Bots Vivos: <span id="bot-val">5</span></div>
        </div>
        <div id="crosshair"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        // --- TEXTURAS ---
        function createTex(color) {
            const c = document.createElement('canvas'); c.width=64; c.height=64;
            const ctx = c.getContext('2d'); ctx.fillStyle = color; ctx.fillRect(0,0,64,64);
            // Noise
            for(let i=0;i<200;i++){ ctx.fillStyle=`rgba(0,0,0,${Math.random()*0.3})`; ctx.fillRect(Math.random()*64,Math.random()*64,2,2); }
            const t = new THREE.CanvasTexture(c); t.magFilter = THREE.NearestFilter; return t;
        }

        const socket = io();
        let scene, camera, renderer, myMesh;
        const peers = {}, enemies = {}, obstacles = [];
        const keys = {w:false, a:false, s:false, d:false};
        let isLocked = false;

        function init() {
            scene = new THREE.Scene(); scene.background = new THREE.Color(0x111111); scene.fog = new THREE.Fog(0x111111, 10, 60);
            camera = new THREE.PerspectiveCamera(70, window.innerWidth/window.innerHeight, 0.1, 1000);
            renderer = new THREE.WebGLRenderer({antialias:true});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            document.body.appendChild(renderer.domElement);

            // Luzes
            const al = new THREE.AmbientLight(0xffffff, 0.4); scene.add(al);
            const dl = new THREE.DirectionalLight(0xffffff, 0.8); dl.position.set(20,50,20); dl.castShadow=true; scene.add(dl);
            
            // Chão
            const floor = new THREE.Mesh(new THREE.PlaneGeometry(200,200), new THREE.MeshStandardMaterial({map:createTex('#222')}));
            floor.rotation.x = -Math.PI/2; floor.receiveShadow = true; scene.add(floor);

            window.addEventListener('resize', ()=>{camera.aspect=window.innerWidth/window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth,window.innerHeight)});
            document.addEventListener('keydown', e=>{if(keys[e.key.toLowerCase()]!==undefined) keys[e.key.toLowerCase()]=true});
            document.addEventListener('keyup', e=>{if(keys[e.key.toLowerCase()]!==undefined) keys[e.key.toLowerCase()]=false});
            document.addEventListener('mousemove', e=>{if(isLocked && myMesh){ myMesh.rotation.y-=e.movementX*0.002; camera.rotation.x-=e.movementY*0.002;}});
            document.addEventListener('mousedown', ()=>{if(isLocked) shoot()});
            document.addEventListener('pointerlockchange', ()=>{isLocked=document.pointerLockElement===document.body});
            
            animate();
        }

        function startGame(){ document.getElementById('overlay').style.display='none'; document.body.requestPointerLock(); }

        function createBox(x,z,w,h,d, color, isMob=false){
            const m = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), new THREE.MeshStandardMaterial({map:createTex(color)}));
            m.position.set(x, h/2, z); m.castShadow=true; m.receiveShadow=true;
            scene.add(m); return m;
        }

        // --- SOCKETS ---
        socket.on('init', d => {
            d.obstacles.forEach(o => {
                const b = createBox(o.x, o.z, o.w, o.h, o.d, '#554433');
                b.geometry.computeBoundingBox();
                obstacles.push(new THREE.Box3().setFromObject(b));
            });
        });

        socket.on('player_joined', p => { 
            if(!peers[p.id]) peers[p.id] = createBox(p.x, p.z, 1, 2.5, 1, p.color); 
        });
        
        socket.on('connect', () => { 
            const myColor = '#'+Math.floor(Math.random()*16777215).toString(16);
            myMesh = createBox(0,0,1,2.5,1, myColor);
            myMesh.add(camera); camera.position.set(0, 0.8, 0); // FPS
            socket.emit('join_req', {color: myColor}); // Pede para entrar
        });

        socket.on('player_left', id => { if(peers[id]){ scene.remove(peers[id]); delete peers[id]; }});
        
        socket.on('player_moved', d => {
            if(peers[d.id]) { peers[d.id].position.set(d.x, 1.25, d.z); peers[d.id].rotation.y = d.ry; }
        });

        socket.on('enemy_update', list => {
            document.getElementById('bot-val').innerText = Object.keys(list).length;
            // Atualiza ou cria bots
            for(let id in list){
                const b = list[id];
                if(!enemies[id]) enemies[id] = createBox(b.x, b.z, 1.2, 1.2, 1.2, '#ff0000', true);
                else {
                    enemies[id].position.x += (b.x - enemies[id].position.x)*0.3;
                    enemies[id].position.z += (b.z - enemies[id].position.z)*0.3;
                }
            }
            // Remove mortos
            for(let id in enemies){ if(!list[id]){ scene.remove(enemies[id]); delete enemies[id]; }}
        });

        socket.on('player_hit', d => {
            if(d.id === socket.id) {
                document.getElementById('hp-val').innerText = d.hp;
                document.body.style.background = 'red'; setTimeout(()=>document.body.style.background='#000', 100);
            }
        });
        
        socket.on('player_respawn', d => {
            if(d.id === socket.id){ myMesh.position.set(d.x, 1.25, d.z); document.getElementById('hp-val').innerText=100; }
        });

        // --- LÓGICA LOCAL ---
        const raycaster = new THREE.Raycaster();
        function shoot(){
            // Efeito Visual
            const laser = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 50), new THREE.MeshBasicMaterial({color:0x00ff00}));
            laser.position.set(0, -0.2, -25); myMesh.add(laser); setTimeout(()=>myMesh.remove(laser), 50);

            raycaster.setFromCamera(new THREE.Vector2(0,0), camera);
            
            // Check Hit Players
            const pMeshes = Object.values(peers);
            let intersects = raycaster.intersectObjects(pMeshes);
            if(intersects.length > 0){
                const tid = Object.keys(peers).find(k=>peers[k]===intersects[0].object);
                if(tid) socket.emit('shoot', {type: 'player', id: tid});
                return;
            }
            
            // Check Hit Enemies
            const eMeshes = Object.values(enemies);
            intersects = raycaster.intersectObjects(eMeshes);
            if(intersects.length > 0){
                const eid = Object.keys(enemies).find(k=>enemies[k]===intersects[0].object);
                if(eid) socket.emit('shoot', {type: 'enemy', id: eid});
            }
        }

        function checkCol(x, z){
            const box = new THREE.Box3(); 
            box.setFromCenterAndSize(new THREE.Vector3(x, 1.25, z), new THREE.Vector3(0.8, 2, 0.8));
            for(let o of obstacles) if(box.intersectsBox(o)) return true;
            return false;
        }

        function animate() {
            requestAnimationFrame(animate);
            if(isLocked && myMesh){
                const s = 0.2;
                const d = new THREE.Vector3();
                if(keys.w) d.z-=1; if(keys.s) d.z+=1; if(keys.a) d.x-=1; if(keys.d) d.x+=1;
                d.applyEuler(new THREE.Euler(0,myMesh.rotation.y,0)).normalize().multiplyScalar(s);
                
                if(!checkCol(myMesh.position.x+d.x, myMesh.position.z)) myMesh.position.x+=d.x;
                if(!checkCol(myMesh.position.x, myMesh.position.z+d.z)) myMesh.position.z+=d.z;

                socket.emit('move', {x:myMesh.position.x, z:myMesh.position.z, ry:myMesh.position.y});
            }
            renderer.render(scene, camera);
        }
        init();
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return HTML_CONTENT

@socketio.on('join_req')
def join(data):
    pid = request.sid
    players[pid] = {'id':pid, 'x': random.randint(-40,40), 'z': random.randint(-40,40), 'ry':0, 'color':data['color'], 'hp':100}
    emit('init', {'obstacles':obstacles})
    emit('player_joined', players[pid], broadcast=True, include_self=False)
    # Envia players existentes para o novo
    for oid, p in players.items():
        if oid != pid: emit('player_joined', p)

@socketio.on('move')
def move(d):
    if request.sid in players:
        players[request.sid].update(d)
        emit('player_moved', {'id':request.sid, 'x':d['x'], 'z':d['z'], 'ry':d['ry']}, broadcast=True, include_self=False)

@socketio.on('shoot')
def shoot(d):
    shooter = request.sid
    # Tiro em Player
    if d['type'] == 'player':
        tid = d['id']
        if tid in players:
            players[tid]['hp'] -= 10
            emit('player_hit', {'id':tid, 'hp':players[tid]['hp']}, broadcast=True)
            if players[tid]['hp'] <= 0:
                players[tid]['hp']=100; players[tid]['x']=random.randint(-40,40); players[tid]['z']=random.randint(-40,40)
                emit('player_respawn', players[tid], broadcast=True)
    
    # Tiro em Bot
    elif d['type'] == 'enemy':
        eid = d['id']
        if eid in enemies:
            enemies[eid]['hp'] -= 25 # 4 tiros mata
            if enemies[eid]['hp'] <= 0:
                # Mata e respawna em outro lugar
                enemies[eid]['hp'] = 100
                enemies[eid]['x'] = random.randint(-40, 40)
                enemies[eid]['z'] = random.randint(-40, 40)
    
@socketio.on('disconnect')
def disc():
    if request.sid in players:
        del players[request.sid]
        emit('player_left', request.sid, broadcast=True)

if __name__ == '__main__':
    print("="*40)
    print(f"JOGO ONLINE! CONVIDE AMIGOS:")
    print(f"LINK LOCAL: http://{LOCAL_IP}:5001")
    print("="*40)
    # host='0.0.0.0' libera o acesso para a rede
    socketio.run(app, host='0.0.0.0', port=5001)