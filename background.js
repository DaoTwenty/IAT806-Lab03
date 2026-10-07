
// Class for changing background
class AnimatedBackground {

    // takes the image files and the speed. Images are drawn at their own size, never resized
    constructor(files, winter, speed) {
        this.files = files;
        this.winter_file = winter;
        this.speed = speed;
        this.frozen = false;
    }

    async setup() {
        this.images = [];
        for (let i = 0; i < this.files.length; i++) {
            this.images[i] = await loadImage(this.files[i]);
        }
        this.winter = await loadImage(this.winter_file);
    }

    freeze() {
        this.frozen = true;
    }

    unfreeze() {
        this.frozen = false;
    }

    // Display current image as background
    background() {
        if (this.frozen) {
            background(this.winter);
        } else {
            let index = Math.floor((frameCount / this.speed) % this.files.length);
            background(this.images[index]);
        }
    }

}