# Shared timing harness — AoES Labs 2–4

This is the student-facing adaptation of the course's worked
`src/es201/l0-dwt-demo/` harness. It retains GPIO, timer and ADC investigations,
uses the EP-0172 Gremlin UART workflow and gives each observation a precise name.
The older source and its captures remain separate; they are not acceptance data
for this revision. No nested repository or simulator is required to build this tool.

## Build and capture

From this directory, using the course SDK and `picolab` installation:

```sh
export PICOLAB_BUILD_TYPE=Release
picolab build aoes_timing
picolab flash build/aoes_timing.elf
picolab monitor
```

Use the monitor's established logging facility, or retain its plain UART output
as `captures/timing.log` (create that directory first). Do not hardcode a moving
`/dev/ttyACM` number. The program repeats, so a monitor attached after reset can
still retain an entire run. Keep one complete `@@BEGIN` through `@@END` window,
with all raw sample lines. There is no input-byte handshake.

```sh
python3 decode.py captures/timing.log -o captures/timing.json
```

The decoder selects the last complete run; `--run 2` selects a particular complete
run. It rejects unsupported schemas, malformed/duplicate samples and incomplete
selected runs. Use a separate capture file after resetting the firmware, since
run numbers start again at 1. Partial records before the first retained begin
marker are ignored. Firmware summaries are convenience output; the host tool
recomputes statistics from the retained raw samples.

## Measurement contract

| Case | Bracket / observations | Interpretation |
|---|---|---|
| `empty_bracket` | Two cycle-counter reads | Observe instrumentation overhead; do not blindly subtract its maximum |
| `gpio_xor_mask` | One SDK XOR operation | CPU-visible call bracket, not a physical edge-to-edge measurement |
| `gpio_put` | One SDK level write with alternating levels | Includes argument preparation in the bracket |
| `sio_xor_write` | One direct typed SIO XOR-register write | Compare generated instructions with the SDK operation |
| `timer_callback_period` | Consecutive DWT reads at callback entry | Callback-period variation; not interrupt-request-to-handler latency |
| `adc_read` | One blocking SDK conversion call | Includes software/read overhead; not just the converter's internal cycles |

All readings use Core 0 and the fixed, reported `clk_sys` value. Unsigned
subtraction handles one counter wrap only if the actual interval is shorter
than a full wrap. The 32-bit counter wraps after `2^32 / clock_hz` seconds.
Interrupts, cache/memory delays and blocking can contribute inside a bracket.
Printing happens after each measurement window. GPIO cases toggle the existing
GP16 LED; ADC0 reads the GP26 joystick input. There is no new wiring.

The timer case has its own bounded recorder of callback-entry timestamps; it
does not poll a lossy one-event flag. The default SDK alarm pool runs on Core 0;
the harness checks the recorded core and aborts on a mismatch or timeout.
Counter unavailability is reported explicitly. This reference is for RP2350 Arm;
simulator timing and RISC-V cycle counting need their own validated contracts.

UART format `aoes-timing-v1` contains clock/core/configuration metadata, indexed
raw samples and end/abort markers. JSON preserves the raw cycles and reports
population standard deviation and means converted with the recorded clock.
No output value constitutes a deadline guarantee or a universal expected number.

Record the source commit/local changes, SDK/compiler versions, build type and
ELF hash beside each capture. This tool is included in the pinned Lab 2 source candidate. That source
availability is separate from a new hardware acceptance run.
