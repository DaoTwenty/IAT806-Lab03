# Lab 03 — Make the Dancers Yours

In class we loaded eight dance poses into an array with a loop, then animated a dancer using arrays. We also have a code that demonstrate how to use click to step through them.

![The dancers from class](dance_preview.gif)

In this lab you add **sounds**, a way to **stop and start** the animation, and **something fun** of your own. Then you put it on your website.

## Start from the in-class sketch

The starter is in the [`starter/`](starter/) folder of this repo. If you haven't finished your class code, this could help. but feel free and you SHOULD use your own. Don't use my frames. Use yours. These are here so it works. Bring your own sounds:

```
starter/
├── sketch.js         the in-class sketch, ready for your website
├── dance_frames/     dance0.png ... dance7.png
└── sounds/           sound0.mp3 ... sound3.mp3
```

1. In your website repo, copy your `lab-01/` folder and rename the copy `lab-03`.
2. On this repo's GitHub page, click the green **Code** button, then **Download ZIP**. Unzip it.
3. Copy everything inside `starter/` into your `lab-03/` folder. Let it replace `sketch.js`.
4. Open `lab-03/index.html` with Live Server. You should see the dancers moving before you change anything.
5. Replace the frames with these frames. Should work. Make sure the names match.
6. Replace sounds with your own.

## How sound works in p5

### 1. Add the p5.sound library

Sound isn't built into p5.js. It comes from an add-on library called **p5.sound**. In `lab-03/index.html`, add the p5.sound line right **after** the p5.js line and **before** `sketch.js`:

```html
<!-- p5.js, version 2.3.3. Every sketch page needs this line. -->
<script src="https://cdn.jsdelivr.net/npm/p5@2.3.3/lib/p5.min.js"></script>

<!-- p5.sound, the sound add-on. Must come after p5.js and before sketch.js. -->
<script src="https://cdn.jsdelivr.net/npm/p5.sound@0.4.1/dist/p5.sound.min.js"></script>

<!-- Your code. Keep this line last. -->
<script src="sketch.js"></script>
```

### 2. `loadSound()` works like `loadImage()`

Loading a sound is the same as loading an image, with a different function name:

```js
img = await loadImage("dance_frames/dance0.png"); // an image
snd = await loadSound("sounds/sound0.mp3"); // a sound
```

Just like with images:

- It goes in `async setup()`, with `await` in front.
- The path is relative to `index.html`.
- It only works with Live Server.

You draw an image with `image()`. You play a sound with `.play()`:

```js
snd.play();
```

### 3. Many sounds: use an array and a loop

This is exactly what we did with the frames. The sounds are named `sound0.mp3` to `sound3.mp3`, so a loop can build the names:

```js
let sounds = [];

// in setup(), after the frames loop:
for (let i = 0; i < 4; i++) {
  sounds.push(await loadSound("sounds/sound" + i + ".mp3"));
}
```

Now `sounds[0]` is the first sound, `sounds[1]` the second, and so on.

Want to use your own sounds? Put them in the `sounds/` folder and name them `sound0.mp3`, `sound1.mp3`, `sound2.mp3`, ... Change the `4` in the loop to however many you have. You can record them on your phone, or find clips on [freesound.org](https://freesound.org) or [Pixabay](https://pixabay.com/sound-effects/). Keep them short.

## What to add

Do **all three**.

### 1. Play the next sound on every click

Each click plays a sound from your array: the first click plays `sounds[0]`, the next `sounds[1]`, and so on. After the last one, go back to `sounds[0]`.

This works just like `index` does for the frames: a variable that counts up, wrapped with `%`.

```js
let soundIndex = 0;

function mousePressed() {
  userStartAudio(); // browsers block sound until the user clicks; this switches it on
  sounds[soundIndex].play();
  soundIndex = (soundIndex + 1) % sounds.length;
}
```

Keep the `index` line that's already in `mousePressed()`, so the click dancer still changes too.

### 2. Stop and start the animation

Pick a key, like `space`, that freezes the dancers. Pressing it again starts them again. p5 has three things that help:

- `noLoop()` stops `draw()`, so nothing moves.
- `loop()` starts `draw()` again.
- `isLooping()` is `true` while `draw()` is running.

Put them in `keyPressed()` with an `if`/`else`, like the pause in our Week 2 ball sketch.

This stops the whole animation. How can you stop only one of them? This is bonus points :).

### 3. Something fun

Make the animation yours. Some ideas:

- **Click to add a dancer:** `xs.push(mouseX)` and `speeds.push(8)` in `mousePressed()`. The loop in `draw()` draws the new one for you.
- **Change the speeds** with a key.
- **Disco background:** a background color that changes on every click.
- **Color the dancers** with `tint(r, g, b)` before `image()`, and `noTint()` after.
- **Draw your own dancer:** replace the images in `dance_frames/` with your own, named `dance0.png` to `dance7.png`.

Weird is good. Have fun with it.

Put a **comment** above each thing you add that says what it does, in your own words.

## How to hand it in

1. Edit `lab-03/index.html`: change the title and the `<h1>` to Lab 03, and write a sentence or two about how to play with it: what to click and which key to press.
2. Add a link to it on `projects/iat-806/index.html`.
3. Commit and sync, then check that it works, **with sound**, at:

```
https://your-username.github.io/projects/iat-806/lab-03/
```

In **Canvas**, submit:

1. The link to your live sketch.
2. The link to your `lab-03` folder in your GitHub repo.

Need a reminder on adding a folder to your site? See [section 4 of the personal-website README](https://github.com/IAT-806/personal-website#4-add-a-submission).

## If something doesn't work

Open the browser console (right-click the page → **Inspect** → **Console**) and read the red text.

- **`loadSound is not defined`**: the p5.sound line is missing from `index.html`, or it's below `sketch.js`.
- **Blank canvas and `404 (File not found)`**: a sound or image path is wrong. Check the folder name, the file name, and the extension.
- **Works with Live Server but not on GitHub Pages**: check capital letters. Your computer may not care about `Sound0.mp3` vs `sound0.mp3`, but GitHub Pages does.
