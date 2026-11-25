# Engine notes (for the next AI)

Baseline engine = `render.py` from https://github.com/barryralphh/cn-endsem-coach (Pillow frames 1280x720, edge-tts `en-IN-PrabhatNeural` rate -6%, espeak fallback, ffmpeg concat, libx264 crf30 stillimage, fps 10). Mascot bird with mouth open/close frames, left panel (theory/diagram) and right paper panel (calculation, step highlighted, spoken step by step).

## Lesson file format (`lessons/Lnn_name.py`)
```python
L = dict(title='...', points=[10 one-line golden points], scenes=[
  S(say='Hinglish narration', cap='speech bubble caption',
    left=[['h','heading'],['t','text'],['b',['bullet','bullet']],['row',['A','B','C']],['col',['step1','step2']],
          ['tbl',[['H1','H2'],['a','b']]],['bits','1010',['1','0','1','0']],['plot',pts,opt]],
    right=['## Title','? question','working line','! final answer','~ note']),
])
```
`S` is injected by render.py. Scenes with `right` are narrated twice: left part with `say`, then each right group step by step (`words()` converts =, +, x, / to spoken Hinglish). Recap scene of the 10 points is auto appended.

## To add (planned engine upgrades)
- `['graph', nodes, edges, height]`: generic shape diagram (boxes, diamonds, ovals, arrows with labels) for flowcharts, control-flow graphs, ER, DFD, state diagrams, use case, architecture. nodes = {id: (x, y, 'label', shape)} with x,y in 0..1; edges = [(a, b, 'label')].
- `['mind', center, [spokes]]` for the unit map scene.
- Brand text: 'Gussa Guru SE Dojo'.
- Parts: `python render.py build 04 --part 2 --parts 4` renders a contiguous quarter of the scenes to `out/04_p2.mp4`; merge job: `ffmpeg -f concat -safe 0 -i list.txt -c copy out/04.mp4`. 20 workers = 5 units x 4 parts.

## Actions
Workflow `build-videos` (workflow_dispatch) with matrix unit in [01..05] x part in [1..4], `fail-fast: false`, installs ffmpeg + fonts-dejavu-core + espeak-ng + pillow + edge-tts. Publish job downloads artifacts, merges parts, commits `videos/` as bot.
