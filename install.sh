# Linux/macOS 一键安装脚本
set -e

echo "🔧 安装 Rust 工具链（czsc 编译需要）..."
if ! command -v rustc &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

echo "📦 安装 Python 依赖..."
pip install --break-system-packages git+https://github.com/waditu/czsc.git
pip install --break-system-packages ccxt pandas plotly
pip install --break-system-packages baostock pydantic-settings rich python-dotenv

echo "✅ 验证安装..."
python3 -c "import czsc; print(f'czsc {czsc.__version__}')"
python3 -c "from czsc.connectors.ccxt_connector import get_raw_bars; print('get_raw_bars ✅')"
python3 -c "from czsc import CZSC, Freq; print(f'Freq.F240={Freq.F240}')"

echo ""
echo "🚀 安装完成！试试:"
echo "  python scripts/czsc_analyze.py BTCUSDT 4h --signals"
