// SPDX-License-Identifier: LGPL-3.0-or-later
#pragma once
#include <iostream>
#include <string>
#include <vector>

#include "device.h"
#include "tensorflow/core/framework/op.h"
#include "tensorflow/core/framework/op_kernel.h"
#include "tensorflow/core/framework/shape_inference.h"

using namespace tensorflow;
using CPUDevice = Eigen::ThreadPoolDevice;
using GPUDevice = Eigen::GpuDevice;

// functions used in custom ops
struct DeviceFunctor {
  void operator()(std::string& device, const CPUDevice& d) { device = "CPU"; }
#if GOOGLE_CUDA || TENSORFLOW_USE_ROCM
  void operator()(std::string& device, const GPUDevice& d) { device = "GPU"; }
#endif  // GOOGLE_CUDA || TENSORFLOW_USE_ROCM
};

namespace deepmd {
void safe_compute(OpKernelContext* context,
                  std::function<void(OpKernelContext*)> ff);
};
