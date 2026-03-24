"""
自动标注命令
使用预训练 YOLO 模型自动标注图片，管理员审核后加入训练集
"""
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

# 添加 yolo26 到路径
YOLO26_PATH = Path(__file__).resolve().parent.parent.parent.parent / 'yolo26'
sys.path.insert(0, str(YOLO26_PATH))

from ultralytics import YOLO


class Command(BaseCommand):
    help = "使用预训练 YOLO 模型自动标注设施图片"

    def add_arguments(self, parser):
        parser.add_argument(
            '--image-ids',
            type=str,
            help='要标注的图片ID，逗号分隔 (如: 1,2,3)',
        )
        parser.add_argument(
            '--all-pending',
            action='store_true',
            help='标注所有待标注的图片',
        )
        parser.add_argument(
            '--model',
            type=str,
            default='yolo26n',
            help='用于标注的模型 (默认: yolo26n)',
        )
        parser.add_argument(
            '--conf-threshold',
            type=float,
            default=0.25,
            help='置信度阈值 (默认: 0.25)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅预览，不保存标注结果',
        )

    def handle(self, *args, **options):
        image_ids = options.get('image_ids')
        all_pending = options.get('all_pending')
        model_name = options.get('model', 'yolo26n')
        conf_threshold = options.get('conf_threshold', 0.25)
        dry_run = options.get('dry_run', False)

        if not image_ids and not all_pending:
            raise CommandError("请提供 --image-ids 或使用 --all-pending")

        self.stdout.write(f"使用模型: {model_name}")
        self.stdout.write(f"置信度阈值: {conf_threshold}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run 模式：不会保存标注结果"))

        # 加载模型
        self.stdout.write(f"加载模型: {model_name}.pt")
        try:
            model = YOLO(f'{model_name}.pt')
        except Exception as e:
            raise CommandError(f"加载模型失败: {e}")

        # 获取要标注的图片
        from facility_mgmt.models import FacilityImage, TrainingImage

        if all_pending:
            pending_images = FacilityImage.objects.filter(
                training_images__isnull=True
            ).distinct() | FacilityImage.objects.filter(
                training_images__annotation_status='pending'
            ).distinct()
            images = list(pending_images)
        else:
            id_list = [int(x.strip()) for x in image_ids.split(',')]
            images = list(FacilityImage.objects.filter(id__in=id_list))

        if not images:
            self.stdout.write(self.style.WARNING("没有找到要标注的图片"))
            return

        self.stdout.write(f"找到 {len(images)} 张待标注图片")

        # 类别名称映射
        class_names = [
            'public_seat', 'lighting', 'electricity_meter',
            'water_meter', 'street_light', 'speed_bump'
        ]

        # 标注统计
        annotated_count = 0
        skipped_count = 0
        error_count = 0

        for facility_image in images:
            try:
                image_path = facility_image.image.path

                # 运行检测
                results = model.predict(
                    source=image_path,
                    conf=conf_threshold,
                    verbose=False,
                    save=False,
                )

                if not results or len(results) == 0:
                    self.stdout.write(f"[{facility_image.id}] 未检测到目标，跳过")
                    skipped_count += 1
                    continue

                result = results[0]
                if result.boxes is None or len(result.boxes) == 0:
                    self.stdout.write(f"[{facility_image.id}] 未检测到目标，跳过")
                    skipped_count += 1
                    continue

                # 转换为 YOLO 格式标注
                h, w = result.orig_shape
                annotations = []

                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    xywhn = box.xywhn[0].cpu().numpy()  # 归一化的中心点+宽高

                    annotation = {
                        'class_id': cls_id,
                        'class_name': class_names[cls_id] if cls_id < len(class_names) else f'class_{cls_id}',
                        'bbox': xywhn.tolist(),  # [x_center, y_center, width, height] 归一化
                        'confidence': float(box.conf[0]),
                    }
                    annotations.append(annotation)

                if dry_run:
                    self.stdout.write(
                        f"[{facility_image.id}] 预览: 检测到 {len(annotations)} 个目标"
                    )
                    for ann in annotations:
                        self.stdout.write(
                            f"  - {ann['class_name']}: conf={ann['confidence']:.2f}"
                        )
                else:
                    # 保存标注结果
                    TrainingImage.objects.create(
                        original_image=facility_image,
                        annotations={'annotations': annotations, 'format': 'yolo'},
                        annotation_status='annotated',
                    )
                    self.stdout.write(
                        f"[{facility_image.id}] 已自动标注: {len(annotations)} 个目标"
                    )

                annotated_count += 1

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"[{facility_image.id}] 标注失败: {e}")
                )
                error_count += 1

        # 输出统计
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"自动标注完成!")
        self.stdout.write(f"  成功: {annotated_count}")
        self.stdout.write(f"  跳过: {skipped_count}")
        self.stdout.write(f"  失败: {error_count}")

        if not dry_run:
            self.stdout.write("")
            self.stdout.write(
                "请在 Django Admin 中审核标注结果，状态变为 'verified' 后可加入训练集"
            )
