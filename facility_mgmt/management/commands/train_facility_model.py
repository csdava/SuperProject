"""
训练 YOLO 设施检测模型
"""
import sys
from pathlib import Path
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# 添加 yolo26 到路径
YOLO26_PATH = Path(__file__).resolve().parent.parent.parent.parent / 'yolo26'
sys.path.insert(0, str(YOLO26_PATH))

from ultralytics import YOLO


class Command(BaseCommand):
    help = "训练 YOLO 设施检测模型"

    def add_arguments(self, parser):
        parser.add_argument(
            '--epochs',
            type=int,
            default=100,
            help='训练轮数 (默认: 100)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=16,
            help='批次大小 (默认: 16)',
        )
        parser.add_argument(
            '--image-size',
            type=int,
            default=640,
            help='图像尺寸 (默认: 640)',
        )
        parser.add_argument(
            '--model',
            type=str,
            default='yolo26n',
            help='基础模型 (默认: yolo26n)',
        )
        parser.add_argument(
            '--dataset-version',
            type=str,
            required=True,
            help='数据集版本标识',
        )
        parser.add_argument(
            '--job-id',
            type=int,
            help='TrainingJob PK，用于更新训练任务状态',
        )
        parser.add_argument(
            '--data-yaml',
            type=str,
            help='数据集 YAML 文件路径 (默认: 自动生成)',
        )
        parser.add_argument(
            '--project',
            type=str,
            default='facility_detection',
            help='训练项目名称 (默认: facility_detection)',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='训练实验名称 (默认: {dataset_version}_{timestamp})',
        )

    def handle(self, *args, **options):
        epochs = options['epochs']
        batch_size = options['batch_size']
        image_size = options['image_size']
        model_name = options['model']
        dataset_version = options['dataset_version']
        job_id = options['job_id']
        data_yaml = options['data_yaml']
        project = options['project']
        name = options['name'] or f"{dataset_version}_{datetime.now().strftime('%Y%m%d_%H%M')}"

        self.stdout.write(f"开始训练设施检测模型...")
        self.stdout.write(f"  数据集版本: {dataset_version}")
        self.stdout.write(f"  基础模型: {model_name}")
        self.stdout.write(f"  训练轮数: {epochs}")
        self.stdout.write(f"  批次大小: {batch_size}")
        self.stdout.write(f"  图像尺寸: {image_size}")

        # 导入模型
        from facility_mgmt.models import TrainingJob
        job = None

        if job_id:
            try:
                job = TrainingJob.objects.get(id=job_id)
                job.status = 'training'
                job.started_at = datetime.now()
                job.save()
                self.stdout.write(f"已更新训练任务 #{job_id} 状态")
            except TrainingJob.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"TrainingJob #{job_id} 不存在，将不更新状态"))

        try:
            # 加载基础模型
            self.stdout.write(f"加载基础模型: {model_name}")
            model = YOLO(f'{model_name}.pt')

            # 如果没有提供数据集 YAML，创建默认配置
            if not data_yaml:
                data_yaml = self._create_dataset_yaml(dataset_version)

            # 开始训练
            self.stdout.write(self.style.SUCCESS(f"开始训练，输出目录: {project}/{name}"))

            results = model.train(
                data=data_yaml,
                epochs=epochs,
                batch=batch_size,
                imgsz=image_size,
                project=project,
                name=name,
                verbose=True,
                exist_ok=True,
            )

            # 获取训练结果
            if hasattr(results, 'results_dict'):
                metrics = results.results_dict
                map50 = metrics.get('metrics/mAP50(B)', None)
                map50_95 = metrics.get('metrics/mAP50-95(B)', None)
            else:
                map50 = None
                map50_95 = None

            # 保存模型路径
            best_model_path = f"{project}/{name}/weights/best.pt"
            last_model_path = f"{project}/{name}/weights/last.pt"

            self.stdout.write(self.style.SUCCESS(f"训练完成!"))
            self.stdout.write(f"  最佳模型: {best_model_path}")
            self.stdout.write(f"  mAP50: {map50}")
            self.stdout.write(f"  mAP50-95: {map50_95}")

            # 更新训练任务状态
            if job:
                job.status = 'completed'
                job.completed_at = datetime.now()
                job.map50 = map50
                job.map50_95 = map50_95
                job.model_path = best_model_path
                job.save()
                self.stdout.write(self.style.SUCCESS(f"已更新训练任务 #{job.id} 状态"))

        except Exception as e:
            error_msg = str(e)
            self.stderr.write(self.style.ERROR(f"训练失败: {error_msg}"))

            if job:
                job.status = 'failed'
                job.completed_at = datetime.now()
                job.error_message = error_msg
                job.save()

            raise CommandError(f"训练失败: {error_msg}")

    def _create_dataset_yaml(self, dataset_version: str) -> str:
        """创建数据集配置文件"""
        import os
        import tempfile

        # 数据集路径
        dataset_root = Path(settings.MEDIA_ROOT) / 'facility_images' / 'dataset'

        yaml_content = f"""
# 设施检测数据集配置
path: {dataset_root}
train: images/train
val: images/val

# 类别数量
nc: 6

# 类别名称
names:
  0: public_seat
  1: lighting
  2: electricity_meter
  3: water_meter
  4: street_light
  5: speed_bump
"""

        # 保存到临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            dir=settings.MEDIA_ROOT
        )
        temp_file.write(yaml_content.strip())
        temp_file.close()

        self.stdout.write(f"已创建数据集配置: {temp_file.name}")
        return temp_file.name
