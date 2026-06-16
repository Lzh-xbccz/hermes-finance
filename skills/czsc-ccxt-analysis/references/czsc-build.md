# czsc 从源码构建实录

## 环境要求
- Ubuntu 24.04+ / Python 3.14 / Rust 1.96+
- ccxt 4.5.59+

## 步骤

```bash
# 1. 安装 Rust 工具链（首次）
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# 2. 安装 maturin（PyO3 构建工具）
pip install maturin --break-system-packages

# 3. 卸载旧版
pip uninstall czsc -y --break-system-packages

# 4. 克隆 + 构建
git clone --depth 1 https://github.com/waditu/czsc.git /tmp/czsc
cd /tmp/czsc
maturin build --release  # 首次 15-25 分钟（编译 polars + 9 个 crate）

# 5. 安装 wheel
pip install target/wheels/czsc-*.whl --break-system-packages --force-reinstall

# 6. 验证
python3 -c "from czsc.utils.plotting.lightweight import plot_czsc; print('OK')"
czsc --help
```

## 依赖编译链
maturin build → cargo rustc (czsc-python crate) →
├── polars-core (v0.52, 最大依赖, 48% CPU / 3.3GB RAM)
├── polars-io
├── czsc-signals (246 个信号函数)
├── czsc-core / czsc-trader / czsc-ta / czsc-utils
└── czsc-python (PyO3 binding 总入口)

## 编译时间
- 首次（无缓存）: 15-25 分钟
- 增量构建: 2-5 分钟

## 关键变更（HEAD vs pip 0.10.12）
- + lightweight charts (替代 echarts_plot)
- + CLI 工具链
- − echarts_plot / echarts_* (Phase J 删除)
- − czsc/signals/ Python 层 (信号移至 _native)
- − svc / plotting/backtest / plotting/common
- 信号 256 → 246（精简）
