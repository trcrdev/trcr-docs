# How-to walkthroughs

Short spoken walkthroughs of TRCR, each a minute or two long. The text of
each one is next to its recording, so you can read instead of listen, and so
the recording can be made again when the product changes.

| # | Walkthrough | Script | Audio |
|---|---|---|---|
| 1 | What TRCR is, in two minutes | [01-what-trcr-is.md](01-what-trcr-is.md) | [audio/01-what-trcr-is.mp3](audio/01-what-trcr-is.mp3) |
| 2 | Install TRCR in one command | [02-install-one-command.md](02-install-one-command.md) | [audio/02-install-one-command.mp3](audio/02-install-one-command.mp3) |
| 3 | Add an agent | [03-add-an-agent.md](03-add-an-agent.md) | [audio/03-add-an-agent.mp3](audio/03-add-an-agent.mp3) |
| 4 | Run TRCR in Docker or Podman | [04-containers.md](04-containers.md) | [audio/04-containers.mp3](audio/04-containers.mp3) |

The recordings are made with ElevenLabs from the scripts, using
`narrate.py` (it needs an `ELEVENLABS_API_KEY` in the environment). Headings
and blank lines become pauses; fenced code blocks are shown on screen in the
video and are not read aloud.

```
python3 howto/narrate.py howto/02-install-one-command.md howto/audio/02-install-one-command.mp3
```
