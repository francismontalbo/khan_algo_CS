# Original code excerpts

The three C++ update-loop excerpts come from TensorFlow and OpenXLA. The tagged TensorFlow file carries **Copyright 2016 The TensorFlow Authors. All Rights Reserved.** and the Apache License, Version 2.0. The accompanying Apache license is retained here. Original comments around the excerpts were omitted and indentation was normalized; the loop operations are unchanged. The excerpts alone are not complete programs.

- TensorFlow v2.10.0: https://github.com/tensorflow/tensorflow/blob/v2.10.0/tensorflow/compiler/xla/service/hlo_memory_scheduler.cc
- OpenXLA parent 6f691ec5e9f4e8c900a1cde65ed27df02d04f4c5: https://github.com/openxla/xla/blob/6f691ec5e9f4e8c900a1cde65ed27df02d04f4c5/xla/hlo/transforms/simplifiers/hlo_memory_scheduler.cc
- OpenXLA change 6ecede672c8177bce1580bb3b60d9f6766e8994e: https://github.com/openxla/xla/blob/6ecede672c8177bce1580bb3b60d9f6766e8994e/xla/hlo/transforms/simplifiers/hlo_memory_scheduler.cc

The Python examples were independently written for the earlier review. They implement a simplified sequential workflow model and are not the original code of the cited papers or a complete reproduction of the compiler.
