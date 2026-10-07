// IAT 806 · Lab 03: Zombie Dance Party.

const NUM_ZOMBIES = 5;
const GROUND_POS_Y = 300; 
const BACKGROUND_SPEED = 240; 
const ZOMBIE_SPEED = 6;
const BODY_PARTS_STEPS = 250; 
const EXPLOSION_STEPS = 32;

let bg;
let zombies = [];
let grenades = [];
let ice_block;

let zombie_sounds;
let grenade_sounds;
let freezing_sounds;

let frozen = false;

let held_grenade = null;

async function setup() {
  const canvas = createCanvas(700, 420);
  canvas.parent("sketch-holder");


  let bg_files = [];
  for (let i = 0; i < 5; i++) {
    bg_files.push("backgrounds/bg" + i + ".png");
  }
  bg = new AnimatedBackground(bg_files, "backgrounds/winter.png", BACKGROUND_SPEED);
  await bg.setup();

  zombie_sounds = new IterativeSound(sound_files("zombie", 10));
  grenade_sounds = new IterativeSound(sound_files("grenade", 6));
  freezing_sounds = new IterativeSound(sound_files("freezing", 3));
  await zombie_sounds.setup();
  await grenade_sounds.setup();
  await freezing_sounds.setup();

  ice_block = await loadImage("ice/ice_block.png");
}

async function create_zombie(n, x) {

  let dance_files = [];
  for (let j = 0; j < 8; j++) {
    dance_files.push(`zombies/zombie${n}/zombie${n}_dance${j}.png`);
  }
  let body_files = [];
  for (let part of ["head", "torso", "armL", "armR", "legL", "legR", "extra"]) {
    body_files.push(`zombies/zombie${n}/zombie${n}_${part}.png`);
  }

  let zombie = new Zombie(dance_files, body_files, ZOMBIE_SPEED, x, GROUND_POS_Y, ice_block, BODY_PARTS_STEPS);
  await zombie.setup();
  zombies.push(zombie);

}

function sound_files(name, count) {
  let files = [];
  for (let i = 0; i < count; i++) {
    files.push("sounds/" + name + "/" + name + i + ".mp3");
  }
  return files;
}

function draw() {
  bg.background();

  for (let i = 0; i < zombies.length; i++) {
    zombies[i].draw();
  }
  for (let i = 0; i < grenades.length; i++) {
    grenades[i].draw();
  }

  // forget zombies and grenades that are finished
  for (let i = 0; i < zombies.length; i++) {
    if (zombies[i].active == false) {
      zombies.splice(i, 1);
    }
  }
  for (let i = 0; i < grenades.length; i++) {
    if (grenades[i].active == false) {
      grenades.splice(i, 1);
    }
  }
}

function keyPressed() {
  if (key === " ") {
    frozen = !frozen;
    if (frozen) {
      bg.freeze();
      for (let zombie of zombies) {
        zombie.freeze();
      }
      freezing_sounds.play();
    } else {
      bg.unfreeze();
      for (let zombie of zombies) {
        zombie.unfreeze();
      }
    }
  }

  if ((key === "z") && frozen == false && zombies.length < NUM_ZOMBIES) {
    create_zombie(floor(random(1, 6)), random(70, width - 70));
  }

  if ((key === "g" || key === "G") && frozen == false) {
    spawn_grenade();
  }
}

// creates a grenade at a random position
async function spawn_grenade() {
  let grenade = new Grenade("grenade/grenade.png",explosion_files(8), random(50, width - 50), random(50, height - 100), 0, EXPLOSION_STEPS);
  await grenade.setup();
  grenades.push(grenade);
}

function explosion_files(count) {
  let files = [];
  for (let i = 0; i < count; i++) {
    files.push("grenade/explosion" + i + ".png");
  }
  return files;
}

function mousePressed() {
  if (frozen) {
    return;
  }

  for (let i = grenades.length - 1; i >= 0; i--) {
    if (grenades[i].is_clicked()) {
      held_grenade = grenades[i];
      held_grenade.in_hand = true;
      return;
    }
  }

  for (let i = zombies.length - 1; i >= 0; i--) {
    if (zombies[i].intact && zombies[i].is_clicked()) {
      zombie_sounds.play();
      return;
    }
  }
}

function mouseDragged() {
  if (held_grenade) {
    held_grenade.x = mouseX;
    held_grenade.y = mouseY;
  }
}

function mouseReleased() {
  if (!held_grenade) {
    return;
  }
  let grenade = held_grenade;
  held_grenade = null;
  grenade.in_hand = false;

  for (let zombie of zombies) {
    if (zombie.intact && zombie.is_clicked()) {
      zombie.obliterate();
    }
  }

  grenade.explode();
  grenade_sounds.play();
}
