# Relative timing

Edit `main.c`, then build and run from this directory:

```sh
export PICOLAB_BUILD_TYPE=Release
picolab build
picolab flash build/aoes_lab02_relative.elf
picolab monitor
```

The main loop contains the timing experiment directly. Keep the UART record while
changing the timing statements. PC analysis tools are in `../tools/`
in the standalone source repository. The course manual gives the edit and the
observations to compare.
