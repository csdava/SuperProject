# 设施图像数据集标注指南

## 设施类别

| 类别ID | 类别名称 | 说明 | 示例 |
|--------|----------|------|------|
| 0 | public_seat | 公共座椅 | 公园长椅、社区休息椅 |
| 1 | lighting | 照明灯 | 室内吸顶灯、壁灯 |
| 2 | electricity_meter | 电表 | 家庭电表、配电箱电表 |
| 3 | water_meter | 水表 | 家庭水表、水管水表 |
| 4 | street_light | 路灯 | 室外路灯、庭院灯 |
| 5 | speed_bump | 减速带 | 橡胶减速带、铸铁减速带 |

## 标注工具

### 推荐工具: LabelImg

```bash
pip install labelImg
labelImg
```

### 或使用 Roboflow (在线工具)

访问 https://roboflow.com 注册免费账号

## YOLO 标注格式

YOLO 格式: `class_id x_center y_center width height`

- 所有数值都是相对于图像尺寸的归一化值 (0.0 - 1.0)
- `class_id`: 类别索引 (0-5)
- `x_center`, `y_center`: 边界框中心点坐标
- `width`, `height`: 边界框宽高

### 示例

假设图像尺寸为 640x480，标注一个位于 (100, 120) 尺寸为 (80x60) 的公共座椅:

```
class_id = 0
x_center = (100 + 80/2) / 640 = 0.4375
y_center = (120 + 60/2) / 480 = 0.625
width = 80 / 640 = 0.125
height = 60 / 480 = 0.125
```

标注文件内容: `0 0.4375 0.625 0.125 0.125`

## 标注流程

### 1. 安装并启动 LabelImg

```bash
pip install labelImg
labelImg
```

### 2. 配置 LabelImg

1. 点击左侧 "Open Dir" 选择图片目录: `facility_dataset/raw/<category>/pending`
2. 点击 "Change Save Dir" 选择标注保存目录: `facility_dataset/raw/<category>/annotated`
3. 点击左侧 "PascalVOC" 切换为 "YOLO" 格式
4. 点击 "View" -> "Auto Save Mode" 开启自动保存

### 3. 标注步骤

1. 点击 "Create RectBox" 或按 `W` 键开始画框
2. 在目标周围拖动画框
3. 在弹窗中选择类别或输入类别名
4. 按 `D` 键下一张，按 `A` 键上一张
5. 重复直到标注完所有图片

### 4. 质量检查

- 确保边界框紧贴目标边缘
- 每个目标只画一个框
- 避免标注错误类别
- 检查标注文件是否正确生成

## 数据集划分

标注完成后，将数据按以下比例划分:

- **训练集 (train)**: 70%
- **验证集 (val)**: 20%
- **测试集 (test)**: 10%

### 使用自动划分脚本

```bash
python manage.py split_dataset --category public_seat
```

## 数据增强 (可选)

训练时可启用以下增强:

- 随机翻转 (horizontal flip)
- 随机旋转 (±10°)
- 随机缩放 (±10%)
- 亮度调整 (±20%)
- 模糊处理 (可选)

## 标注要求

### 最低数量建议

每个类别至少 100 张图片才能获得较好的检测效果。

### 图片要求

- 分辨率: 建议 640x480 或更高
- 格式: JPG 或 PNG
- 内容: 清晰、可辨识的目标
- 多角度: 目标的不同拍摄角度
- 多场景: 不同的环境背景

### 注意事项

- 避免标注模糊或被遮挡的目标
- 对于重叠目标，分别标注
- 对于部分可见的目标，标注可见部分
- 确保训练集包含不同光照条件下的图片
