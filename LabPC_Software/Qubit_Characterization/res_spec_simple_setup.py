descriptor_shfqa= """\
instruments:
  SHFQA:
  - address: DEV12249
    uid: device_shfqa_1
connections:
  device_shfqa:
    - iq_signal: q0/measure_line
      ports: QACHANNELS/0/OUTPUT
    - acquire_signal: q0/acquire_line
      ports: QACHANNELS/0/INPUT
"""