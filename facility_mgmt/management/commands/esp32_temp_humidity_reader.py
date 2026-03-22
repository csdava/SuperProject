import json
import re
import time
from typing import Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "读取ESP32(DHT22)串口温湿度，并更新系统参数 + 控制台打印"

    def add_arguments(self, parser):
        parser.add_argument(
            "--port",
            type=str,
            default="",
            help="串口端口（例如 COM5）。不填会列出可用端口并退出。",
        )
        parser.add_argument("--baudrate", type=int, default=115200, help="串口波特率")
        parser.add_argument("--timeout", type=float, default=1.0, help="串口读超时（秒）")
        parser.add_argument(
            "--once",
            action="store_true",
            help="只读取一次数据后退出（便于测试）",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="调试模式：解析失败时打印原始串口行",
        )
        parser.add_argument(
            "--max_wait_seconds",
            type=float,
            default=0,
            help="调试/测试用：最多等待多少秒仍未获得有效数据则退出（0=不限制）",
        )

    def _read_and_parse_line(self, raw_line: str) -> Tuple[Optional[float], Optional[float]]:
        """
        期望 ESP32 固件发送：{"t":25.3,"h":60.2}
        兼容一些简易格式（例如：TEMP=25.3 HUM=60.2）
        """
        line = raw_line.strip()
        if not line:
            return None, None

        # JSON 模式：在一行里可能夹杂ESP32启动/乱码噪声
        # 所以不要用“第一左括号到最后右括号”的方式截取，
        # 而是枚举所有形如 {...} 的候选片段逐个尝试。
        if "{" in line and "}" in line:
            for m in re.finditer(r"\{[^{}]*\}", line):
                json_candidate = m.group(0)
                try:
                    obj = json.loads(json_candidate)
                    t = obj.get("t")
                    h = obj.get("h")
                    if t is None or h is None:
                        continue
                    return float(t), float(h)
                except Exception:
                    continue

        # 兜底2：直接从带引号的JSON字段提取数值
        # 例如：{"t":25.3,"h":60.2}（哪怕json.loads失败，也能抓到数字）
        t_q = re.search(r'(?i)["\']\s*t\s*["\']\s*[:=]\s*(-?\d+(?:\.\d+)?)', line)
        h_q = re.search(r'(?i)["\']\s*h\s*["\']\s*[:=]\s*(-?\d+(?:\.\d+)?)', line)
        if t_q and h_q:
            return float(t_q.group(1)), float(h_q.group(1))

        # 兜底：TEMP/HUM 简易文本模式
        # 允许：TEMP=25.3 HUM=60.2 / t:25.3 h:60.2
        temp_m = re.search(r"(?i)\b(?:t|temp|temperature)\b\s*[:=]\s*(-?\d+(?:\.\d+)?)", line)
        hum_m = re.search(r"(?i)\b(?:h|hum|humidity)\b\s*[:=]\s*(-?\d+(?:\.\d+)?)", line)
        if not temp_m or not hum_m:
            return None, None
        return float(temp_m.group(1)), float(hum_m.group(1))

    def _upsert_system_config(self, key: str, value: float) -> None:
        from accounts.models import SystemConfig

        str_value = str(value)
        with transaction.atomic():
            obj, created = SystemConfig.objects.get_or_create(
                key=key, defaults={"value": str_value}
            )
            if not created:
                if (obj.value or "") != str_value:
                    obj.value = str_value
                    obj.save(update_fields=["value", "updated_at"])

    def handle(self, *args, **options):
        # 延迟导入，避免未安装依赖时影响启动其他管理命令
        try:
            import serial  # type: ignore
            from serial.tools import list_ports  # type: ignore
        except Exception as e:
            raise CommandError(
                "缺少依赖 `pyserial`，请在你的Python环境中安装：pip install pyserial"
            ) from e

        port = (options.get("port") or "").strip()
        baudrate = int(options.get("baudrate") or 115200)
        timeout = float(options.get("timeout") or 1.0)
        once = bool(options.get("once"))
        debug = bool(options.get("debug"))
        max_wait_seconds = float(options.get("max_wait_seconds") or 0)

        self.stdout.write(f"[INFO] debug_flag={debug}, once={once}, max_wait_seconds={max_wait_seconds}")

        if not port:
            ports = list_ports.comports()
            if not ports:
                self.stderr.write(self.style.ERROR("未发现可用串口，请手动指定 --port（例如 COM5）。"))
                return
            self.stdout.write("可用串口列表：")
            for p in ports:
                self.stdout.write(f"- {p.device} ({p.description})")
            self.stderr.write("请使用 --port 指定要读取的串口（例如：--port COM5）。")
            return

        self.stdout.write(f"开始读取串口：{port} @ {baudrate}bps")
        self.stdout.write("协议：每行发送JSON，例如：{\"t\":25.3,\"h\":60.2}")

        ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        try:
            start_ts = time.time()
            debug_printed = False
            while True:
                if max_wait_seconds > 0 and (time.time() - start_ts) > max_wait_seconds:
                    self.stdout.write(self.style.WARNING(f"等待{max_wait_seconds}s仍未获得有效JSON，退出。"))
                    return

                raw = ser.readline()
                if not raw:
                    continue

                try:
                    line = raw.decode("utf-8", errors="ignore")
                except Exception:
                    continue

                t, h = self._read_and_parse_line(line)
                if t is None or h is None:
                    # 串口可能有调试输出/空行，忽略
                    if debug:
                        if not debug_printed:
                            self.stdout.write(
                                f"[DEBUG] first_line={line!r} parsed_t=None parsed_h=None"
                            )
                            debug_printed = True
                    continue
                if debug and not debug_printed:
                    self.stdout.write(f"[DEBUG] first_line={line!r} parsed_t={t} parsed_h={h}")
                    debug_printed = True

                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                self.stdout.write(f"[{ts}] 温度={t:.1f}°C 湿度={h:.1f}%RH")

                # 更新户主端工作台使用的系统参数
                # accounts/views.py 中会读取这两个key
                self._upsert_system_config("current_temperature_c", round(t, 1))
                self._upsert_system_config("current_humidity_rh", round(h, 1))

                if once:
                    self.stdout.write(self.style.SUCCESS("读取一次完成，已退出。"))
                    return
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("已停止（Ctrl+C）。"))
        finally:
            try:
                ser.close()
            except Exception:
                pass

