class Grenade {
    constructor(grenade_image, explosions, x, y, rotation, explosion_time) {
        this.grenade_image = grenade_image;
        this.explosion_files = explosions;
        this.x = x;
        this.y = y;
        this.rotation = rotation;
        this.exploded = false;
        this.explosion_time = explosion_time;
        this.in_hand = false;
        this.active = true;
    }

    async setup() {
        this.grenade = await loadImage(this.grenade_image);
        this.explosions = [];
        for (let i = 0; i < this.explosion_files.length; i++) {
            this.explosions.push(await loadImage(this.explosion_files[i]));
        }
    }

    explode() {
        this.exploded = true;
        this.explosion_step = frameCount;
    }

    is_clicked() {
        if (this.exploded == false && abs(mouseX - this.x) <= this.grenade.width / 2 && abs(mouseY - this.y) <= this.grenade.height / 2) {
            return true;
        }
        return false;
    }

    // draw grenade
    draw() {
        if (this.exploded == false) {
            push();
            imageMode(CENTER);
            translate(this.x, this.y);
            rotate(this.rotation);
            image(this.grenade, 0, 0);
            pop();
        } else {
            if (frameCount - this.explosion_step < this.explosion_time) {
                push();
                imageMode(CENTER);
                let frameIndex = Math.floor(this.explosions.length * (frameCount - this.explosion_step) / this.explosion_time);
                translate(this.x, this.y);
                image(this.explosions[frameIndex], 0, 0);
                pop();
            } else {
                this.active = false;
            }
        }
    }

}