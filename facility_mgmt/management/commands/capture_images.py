"""
批量采集设施图片
用法:
    python manage.py capture_images --count 100 --interval 2 --category public_seat
"""
import os
import time
import cv2
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = '批量采集设施图片'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=50, help='采集数量')
        parser.add_argument('--interval', type=float, default=1.0, help='采集间隔(秒)')
        parser.add_argument('--category', type=str, required=True,
                          choices=['public_seat', 'lighting', 'electricity_meter',
                                  'water_meter', 'street_light', 'speed_bump'],
                          help='设施类别')
        parser.add_argument('--camera', type=int, default=1, help='摄像头索引')
        parser.add_argument('--location', type=str, default='default', help='采集地点标识')

    def handle(self, *args, **options):
        count = options['count']
        interval = options['interval']
        category = options['category']
        camera_idx = options['camera']
        location = options['location']

        # 创建保存目录
        base_dir = Path(settings.MEDIA_ROOT) / 'facility_images' / 'raw' / category / location
        base_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(f'摄像头索引: {camera_idx}')
        self.stdout.write(f'保存目录: {base_dir}')
        self.stdout.write(f'采集数量: {count}')
        self.stdout.write(f'采集间隔: {interval}秒')
        self.stdout.write('')

        # 打开摄像头
        cap = cv2.VideoCapture(camera_idx)
        if not cap.isOpened():
            self.stderr.write(self.style.ERROR(f'无法打开摄像头 {camera_idx}'))
            return

        self.stdout.write(self.style.WARNING('开始采集，按 Ctrl+C 停止...'))
        self.stdout.write('')

        captured = 0
        try:
            for i in range(count):
                ret, frame = cap.read()
                if not ret:
                    self.stderr.write(self.style.ERROR(f'第 {i+1} 帧读取失败'))
                    continue

                # 生成文件名: category_location_timestamp.jpg
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                filename = f'{category}_{location}_{timestamp}.jpg'
                filepath = base_dir / filename

                cv2.imwrite(str(filepath), frame)
                captured += 1

                if captured % 10 == 0 or captured == count:
                    self.stdout.write(f'进度: {captured}/{count} - {filename}')

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('用户中断'))

        finally:
            cap.release()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'采集完成! 共采集 {captured} 张图片'))
        self.stdout.write(f'保存位置: {base_dir}')
