"""接件子包：设备接收单、设备档案、接件单、设备明细、领料明细、配件、照片。"""
from .device import (
    DeviceAccessory,
    DevicePhoto,
    DeviceReceiveOrder,
)
from .order import (
    DeviceArchive,
    ReceiveOrder,
    ReceiveOrderDevice,
    ReceiveOrderPart,
)

__all__ = [
    'DeviceAccessory',
    'DeviceArchive',
    'DevicePhoto',
    'DeviceReceiveOrder',
    'ReceiveOrder',
    'ReceiveOrderDevice',
    'ReceiveOrderPart',
]