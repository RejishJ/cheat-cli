# Demo Assets

This directory is reserved for demo GIFs, screenshots, and visual documentation.

## Adding a Demo GIF

To record a demo GIF of Cheat CLI:

1. Install a terminal recorder:
   - Linux: `asciinema` + `agg` (for GIF conversion)
   - macOS: Use [asciinema](https://asciinema.org/) or [LICEcap](https://www.cockos.com/licecap/)

2. Record a session demonstrating:
   - Launching `cheat`
   - Searching for a command (`cheat git`)
   - Showing all entries (`cheat all`)
   - Adding a new command (`cheat add`)
   - Clean terminal output

3. Save the recording as `demo.gif` in this directory.

4. Uncomment the demo line in `README.md`:
   ```markdown
   ![Demo](docs/assets/demo.gif)
   ```

## Adding Screenshots

- Save terminal screenshots as `screenshot.png` in this directory.
- Reference them in the README where appropriate.
