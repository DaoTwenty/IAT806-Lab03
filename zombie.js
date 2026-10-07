// Class for zombie

class Zombie {

    // takes the image files and the speed. Images are drawn at their own size, never resized
    constructor(files, body_files, speed, x, y, ice_block, max_steps_obliterated) {
        this.files = files;
        this.body_files = body_files;
        this.og_speed = speed;
        this.speed = speed;
        this.x = x;
        this.y = y;
        this.ice_block = ice_block;
        this.max_steps_obliterated = max_steps_obliterated;
        this.images = [];
        this.body_images = [];
        this.intact = true;
        this.frozen = false;
        this.index = 0;
        this.active = true;
    }

    async setup() {
        for (let i = 0; i < this.files.length; i++) {
            this.images[i] = await loadImage(this.files[i]);
        }
        for (let j = 0; j < this.body_files.length; j++) {
            this.body_images[j] = await loadImage(this.body_files[j]);
        }
        this.width = this.images[0].width;
        this.height = this.images[0].height;
    }

    speed_up(factor) {
        this.speed = this.og_speed * Math.max(1, factor);
    }

    slow_up(factor) {
        this.speed = this.og_speed * Math.min(Math.max(0, factor), 1) ;
    }

    // obliterate the zombie
    obliterate() {
        this.intact = false;
        this.step_when_obliterated = frameCount;
        this.body_pos = [];
        for (let i = 0; i < this.body_images.length; i++) {
            this.body_pos[i] = {
                x: this.x + random(-this.width/4, this.width/4),
                y: this.y + random(-this.height/4, this.height/4),
                speed_x: random(-2, 2),
                speed_y: random(-2, 2),
                rotation: random(-PI/8, PI/8),
                rotation_speed: random(-PI/32, PI/32)
            }
        }
    }

    // freeze zombie
    freeze() {
        this.frozen = true;
    }

    unfreeze() {
        this.frozen = false;
    }

    // draw zombie
    draw() {
        if (this.intact == true) {
            if (this.frozen == false ) {
                this.index = Math.floor((frameCount / this.speed) % this.files.length);
            }
            push();
            imageMode(CENTER);
            image(this.images[this.index], this.x, this.y);
            if (this.frozen == true) {
                image(this.ice_block, this.x, this.y);
            }
            pop();
        } else {
            if (frameCount - this.step_when_obliterated < this.max_steps_obliterated) {
                for (let i = 0; i < this.body_images.length; i++) {
                    // simulate gravity by increasing the speed_y
                    this.body_pos[i].speed_y += 0.15;
                    // friction
                    this.body_pos[i].speed_x *= 0.95;
                    this.body_pos[i].speed_y *= 0.95;
                    this.body_pos[i].rotation_speed *= 0.99;
                    // update position
                    this.body_pos[i].x += this.body_pos[i].speed_x;
                    this.body_pos[i].y += this.body_pos[i].speed_y;
                    // bounce off the walls and ceiling, keeping the part inside the canvas
                    if (this.body_pos[i].x < 0 || this.body_pos[i].x > width) {
                        this.body_pos[i].x = constrain(this.body_pos[i].x, 0, width);
                        this.body_pos[i].speed_x *= -1;
                    }
                    if (this.body_pos[i].y < 0 || this.body_pos[i].y > height) {
                        this.body_pos[i].y = constrain(this.body_pos[i].y, 0, height);
                        this.body_pos[i].speed_y *= -1;
                    }
                    // spin
                    this.body_pos[i].rotation += this.body_pos[i].rotation_speed;

                    push();
                    imageMode(CENTER);
                    translate(this.body_pos[i].x, this.body_pos[i].y);
                    rotate(this.body_pos[i].rotation);
                    image(this.body_images[i], 0, 0);
                    pop();
                }
            } else {
                this.active = false;
            }
        }
    }

    is_clicked() {
        // check if in ellipse of the zombie (half the width and height are the radii)
        if ((mouseX - this.x)**2/(this.width/2)**2 + (mouseY - this.y)**2/(this.height/2)**2 <= 1) {
            return true;
        } else {
            return false;
        }
    }
}
